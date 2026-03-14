"""Shared base for broker WebSocket streaming implementations."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Awaitable

from tt_connect.core.timezone import IST
from tt_connect.core.store.resolver import ResolvedInstrument
from tt_connect.core.models.instruments import Instrument
from tt_connect.core.models.enums import FeedState
from tt_connect.core.models import Tick

logger = logging.getLogger(__name__)

# Callback type: async function that receives a Tick
OnTick = Callable[[Tick], Awaitable[None]]

# Callback types for feed health events — no arguments
OnFeedStale     = Callable[[], Awaitable[None]]
OnFeedRecovered = Callable[[], Awaitable[None]]


class BrokerWebSocket(ABC):
    """
    Shared base for broker-specific WebSocket streaming implementations.

    Concrete subclasses provide broker-specific connection logic and binary
    parsing; this base supplies the shared lifecycle, feed-health machinery,
    and reconnect loop so every broker behaves identically at the API level.

    Class attributes (override in subclasses as needed):
        PING_INTERVAL       – seconds between keepalive / staleness checks
        STALE_THRESHOLD     – seconds without a tick before feed → STALE
        MAX_RECONNECT_DELAY – cap on exponential-backoff wait (seconds)
        _BROKER_NAME        – label used in structured log fields

    Abstract hooks (must implement in subclasses):
        _register_subscriptions, _tokens_for_instruments, _remove_tokens,
        _all_tracked_tokens, _connect_and_run, _send_subscribe, _send_unsubscribe

    Optional override:
        _maybe_ping(ws) — default no-op; override to send broker heartbeats
    """

    PING_INTERVAL:       int = 30
    STALE_THRESHOLD:     int = 30
    MAX_RECONNECT_DELAY: int = 60
    _BROKER_NAME:        str = ""

    def __init__(self) -> None:
        self._on_tick:      OnTick | None          = None
        self._on_stale:     OnFeedStale | None     = None
        self._on_recovered: OnFeedRecovered | None = None
        self._closed:       bool                   = False
        self._ws:           Any | None             = None
        self._task:         asyncio.Task[None] | None = None
        self._reconnect_delay: float               = 2.0

        self._feed_state:      FeedState                  = FeedState.CONNECTING
        self._reconnect_count: int                        = 0
        self._last_tick_at:    dict[Instrument, datetime] = {}

    # ------------------------------------------------------------------ public

    @property
    def is_connected(self) -> bool:
        """True when the socket is open (does not imply data is fresh)."""
        return self._ws is not None

    @property
    def feed_state(self) -> FeedState:
        """Current feed state: CONNECTING / CONNECTED / RECONNECTING / STALE / CLOSED."""
        return self._feed_state

    @property
    def reconnect_count(self) -> int:
        """Number of reconnect attempts since this instance was created."""
        return self._reconnect_count

    def last_tick_at(self, instrument: Instrument) -> datetime | None:
        """Return wall-clock IST time of the last tick received for an instrument."""
        return self._last_tick_at.get(instrument)

    async def subscribe(
        self,
        subscriptions: list[tuple[Instrument, ResolvedInstrument]],
        on_tick: OnTick,
        on_stale: OnFeedStale | None = None,
        on_recovered: OnFeedRecovered | None = None,
    ) -> None:
        """Track subscriptions and ensure the WebSocket loop is running."""
        self._on_tick      = on_tick
        self._on_stale     = on_stale
        self._on_recovered = on_recovered

        new_tokens = await self._register_subscriptions(subscriptions)

        if self._task is None or self._task.done():
            self._closed = False
            self._task = asyncio.create_task(self._run())
        elif self._ws is not None and new_tokens:
            await self._send_subscribe(self._ws, new_tokens)

    async def unsubscribe(self, instruments: list[Instrument]) -> None:
        """Unsubscribe instruments and remove them from all tracking state."""
        tokens = self._tokens_for_instruments(instruments)
        if not tokens:
            return
        if self._ws is not None:
            await self._send_unsubscribe(self._ws, tokens)
        self._remove_tokens(tokens)
        for inst in instruments:
            self._last_tick_at.pop(inst, None)

    async def close(self) -> None:
        """Stop the reconnect loop and cancel the active WebSocket task."""
        self._closed = True
        self._feed_state = FeedState.CLOSED
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    # ------------------------------------------------------------ shared loop

    async def _run(self) -> None:
        """Reconnect loop with exponential backoff."""
        while not self._closed:
            try:
                await self._connect_and_run()
                self._reconnect_delay = 2.0
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(
                    f"WS error: {exc}",
                    extra={"event": "ws.error", "broker": self._BROKER_NAME},
                )
            if self._closed:
                break
            self._reconnect_count += 1
            self._feed_state = FeedState.RECONNECTING
            logger.info(
                f"WS reconnecting in {self._reconnect_delay:.0f}s … "
                f"(attempt #{self._reconnect_count})",
                extra={
                    "event": "ws.reconnect", "broker": self._BROKER_NAME,
                    "delay_s": self._reconnect_delay,
                    "reconnect_count": self._reconnect_count,
                },
            )
            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, self.MAX_RECONNECT_DELAY)
        self._feed_state = FeedState.CLOSED

    async def _staleness_loop(self, ws: Any) -> None:
        """Background task: send optional keepalive and check feed staleness."""
        while True:
            await asyncio.sleep(self.PING_INTERVAL)
            try:
                await self._maybe_ping(ws)
            except Exception:
                break
            await self._check_staleness()

    async def _maybe_ping(self, ws: Any) -> None:
        """Send a broker-specific keepalive ping. Default: no-op (library handles it)."""
        pass

    async def _check_staleness(self) -> None:
        """Check if the feed has gone stale and fire the on_stale callback."""
        if self._feed_state not in (FeedState.CONNECTED, FeedState.STALE):
            return
        if not self._last_tick_at:
            return
        age = (datetime.now(IST) - max(self._last_tick_at.values())).total_seconds()
        if age > self.STALE_THRESHOLD and self._feed_state == FeedState.CONNECTED:
            self._feed_state = FeedState.STALE
            logger.warning(
                f"Feed stale — last tick {age:.0f}s ago",
                extra={"event": "ws.stale", "broker": self._BROKER_NAME, "age_s": age},
            )
            if self._on_stale:
                try:
                    await self._on_stale()
                except Exception:
                    logger.exception(
                        "on_stale callback failed",
                        extra={"event": "ws.stale_error", "broker": self._BROKER_NAME},
                    )

    # ------------------------------------------------------------ tick helpers

    def _record_tick(self, instrument: Instrument) -> bool:
        """
        Record that a tick was received for this instrument.

        Updates ``_last_tick_at`` and flips STALE → CONNECTED.
        Returns True if the feed was previously stale (caller should fire on_recovered).
        """
        was_stale = self._feed_state == FeedState.STALE
        self._last_tick_at[instrument] = datetime.now(IST)
        if was_stale:
            self._feed_state = FeedState.CONNECTED
            logger.info(
                "Feed recovered",
                extra={"event": "ws.recovered", "broker": self._BROKER_NAME},
            )
        return was_stale

    async def _maybe_fire_recovered(self, was_stale: bool) -> None:
        """Fire the on_recovered callback if transitioning out of STALE."""
        if was_stale and self._on_recovered:
            try:
                await self._on_recovered()
            except Exception:
                logger.exception(
                    "on_recovered callback failed",
                    extra={"event": "ws.recovered_error", "broker": self._BROKER_NAME},
                )

    # ------------------------------------------------------------ abstract hooks

    @abstractmethod
    async def _register_subscriptions(
        self, subscriptions: list[tuple[Instrument, ResolvedInstrument]]
    ) -> list[Any]:
        """Store broker-specific token data; return the list of new broker tokens."""
        ...

    @abstractmethod
    def _tokens_for_instruments(self, instruments: list[Instrument]) -> list[Any]:
        """Return broker tokens corresponding to the given instruments."""
        ...

    @abstractmethod
    def _remove_tokens(self, tokens: list[Any]) -> None:
        """Remove broker token entries from all local maps."""
        ...

    @abstractmethod
    def _all_tracked_tokens(self) -> list[Any]:
        """Return all currently tracked broker tokens."""
        ...

    @abstractmethod
    async def _connect_and_run(self) -> None:
        """Open the WebSocket, resubscribe all tokens, and run the message loop."""
        ...

    @abstractmethod
    async def _send_subscribe(self, ws: Any, tokens: list[Any]) -> None:
        """Send a subscribe request to the broker WebSocket."""
        ...

    @abstractmethod
    async def _send_unsubscribe(self, ws: Any, tokens: list[Any]) -> None:
        """Send an unsubscribe request to the broker WebSocket."""
        ...
