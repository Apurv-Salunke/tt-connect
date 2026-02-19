from __future__ import annotations
from datetime import date
import logging
import aiosqlite
from tt_connect.enums import OnStale
from tt_connect.instrument_manager.db import get_connection, init_schema, truncate_all

logger = logging.getLogger(__name__)


class InstrumentManager:
    def __init__(self, broker_id: str, on_stale: OnStale = OnStale.FAIL):
        self._broker_id = broker_id
        self._on_stale = on_stale
        self._conn: aiosqlite.Connection | None = None

    async def init(self, fetch_fn) -> None:
        self._conn = await get_connection()
        await init_schema(self._conn)
        await self.ensure_fresh(fetch_fn)

    async def ensure_fresh(self, fetch_fn) -> None:
        if await self._is_stale():
            try:
                await self.refresh(fetch_fn)
            except Exception as e:
                if self._on_stale == OnStale.FAIL:
                    raise
                logger.warning(f"Instrument refresh failed, using stale data: {e}")

    async def refresh(self, fetch_fn) -> None:
        logger.info(f"Refreshing instruments for {self._broker_id}")
        raw = await fetch_fn()
        await truncate_all(self._conn)
        await self._insert(raw)
        await self._set_last_updated()
        logger.info("Instrument refresh complete")

    async def _is_stale(self) -> bool:
        async with self._conn.execute(
            "SELECT value FROM _meta WHERE key = 'last_updated'"
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return True
        return row[0] != date.today().isoformat()

    async def _set_last_updated(self) -> None:
        await self._conn.execute(
            "INSERT OR REPLACE INTO _meta(key, value) VALUES ('last_updated', ?)",
            (date.today().isoformat(),),
        )
        await self._conn.commit()

    async def _insert(self, raw: list[dict]) -> None:
        # Implemented per broker via fetch_fn contract
        pass

    @property
    def connection(self) -> aiosqlite.Connection:
        assert self._conn, "InstrumentManager not initialized"
        return self._conn
