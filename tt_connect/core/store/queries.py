"""Read-only discovery queries over the local SQLite instrument cache.

This module owns the *catalog-style* lookup surface for instruments that have
already been downloaded and stored locally. Unlike ``manager.py``, it does not
perform refreshes, staleness checks, or writes; and unlike ``resolver.py``, it
does not translate canonical instruments into broker execution tokens.

Typical use cases:

- browse underlyings that currently have derivatives
- inspect futures, options, and expiry calendars
- fetch lot size / tick size / segment metadata
- build an option chain grouped by strike

All queries run against the existing SQLite cache. If the DB has not yet been
seeded for the selected broker, callers receive a clear
``InstrumentStoreNotInitializedError`` directing them to initialize the main
client first.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import aiosqlite

from tt_connect.core.exceptions import InstrumentNotFoundError, InstrumentStoreNotInitializedError
from tt_connect.core.models.enums import Exchange, OptionType
from tt_connect.core.models.instruments import (
    Equity,
    Future,
    Index,
    Instrument,
    InstrumentInfo,
    Option,
    OptionChain,
    OptionChainEntry,
)


class InstrumentQueries:
    """Read-only query surface for the instrument cache.

    This class owns discovery-style lookups over the local SQLite database.
    It does not refresh data from brokers and does not participate in order
    execution token resolution.
    """

    def __init__(self, conn: aiosqlite.Connection | None) -> None:
        """Create a query helper bound to an optional SQLite connection."""
        self._conn = conn

    def bind(self, conn: aiosqlite.Connection | None) -> None:
        """Attach or detach the active SQLite connection."""
        self._conn = conn

    def _conn_or_raise(self) -> aiosqlite.Connection:
        """Return the active DB connection, or raise a store-specific error."""
        if self._conn is None:
            raise InstrumentStoreNotInitializedError(
                "Instrument DB not initialized. Initialize TTConnect or AsyncTTConnect first "
                "to seed or refresh instruments before using InstrumentStore."
            )
        return self._conn

    async def get_futures(self, underlying: Instrument) -> list[Future]:
        """Return all active futures for an underlying instrument, sorted by expiry."""
        query = """
            SELECT fut.exchange, u.symbol, f.expiry
            FROM instruments fut
            JOIN futures f     ON f.instrument_id = fut.id
            JOIN instruments u ON u.id = f.underlying_id
            WHERE u.exchange = ? AND u.symbol = ?
            ORDER BY f.expiry ASC
        """
        async with self._conn_or_raise().execute(
            query, (str(underlying.exchange), underlying.symbol)
        ) as cur:
            rows = await cur.fetchall()
        return [
            Future(
                exchange=Exchange(row[0]),
                symbol=row[1],
                expiry=date.fromisoformat(row[2]),
            )
            for row in rows
        ]

    async def get_options(
        self,
        underlying: Instrument,
        expiry: date | None = None,
    ) -> list[Option]:
        """Return options for an underlying, optionally filtered by expiry.

        Results are sorted by expiry -> strike -> option_type (CE before PE).
        """
        if expiry is not None:
            query = """
                SELECT opt.exchange, u.symbol, o.expiry, o.strike, o.option_type
                FROM instruments opt
                JOIN options o     ON o.instrument_id = opt.id
                JOIN instruments u ON u.id = o.underlying_id
                WHERE u.exchange = ? AND u.symbol = ? AND o.expiry = ?
                ORDER BY o.expiry ASC, o.strike ASC, o.option_type ASC
            """
            params: tuple[Any, ...] = (str(underlying.exchange), underlying.symbol, expiry.isoformat())
        else:
            query = """
                SELECT opt.exchange, u.symbol, o.expiry, o.strike, o.option_type
                FROM instruments opt
                JOIN options o     ON o.instrument_id = opt.id
                JOIN instruments u ON u.id = o.underlying_id
                WHERE u.exchange = ? AND u.symbol = ?
                ORDER BY o.expiry ASC, o.strike ASC, o.option_type ASC
            """
            params = (str(underlying.exchange), underlying.symbol)
        async with self._conn_or_raise().execute(query, params) as cur:
            rows = await cur.fetchall()
        return [
            Option(
                exchange=Exchange(row[0]),
                symbol=row[1],
                expiry=date.fromisoformat(row[2]),
                strike=float(row[3]),
                option_type=OptionType(row[4]),
            )
            for row in rows
        ]

    async def get_expiries(self, underlying: Instrument) -> list[date]:
        """Return all distinct expiry dates for an underlying across futures and options."""
        query = """
            SELECT DISTINCT expiry FROM (
                SELECT f.expiry FROM futures f
                JOIN instruments u ON u.id = f.underlying_id
                WHERE u.exchange = ? AND u.symbol = ?
                UNION
                SELECT o.expiry FROM options o
                JOIN instruments u ON u.id = o.underlying_id
                WHERE u.exchange = ? AND u.symbol = ?
            )
            ORDER BY expiry ASC
        """
        async with self._conn_or_raise().execute(
            query,
            (str(underlying.exchange), underlying.symbol,
             str(underlying.exchange), underlying.symbol),
        ) as cur:
            rows = await cur.fetchall()
        return [date.fromisoformat(row[0]) for row in rows]

    async def search_instruments(
        self,
        query: str,
        exchange: str | None = None,
    ) -> list[Equity]:
        """Search underlyings (equities + indices) by symbol substring.

        Matching is case-insensitive. Results are sorted by exchange then
        symbol and capped at 50 rows.
        """
        pattern = f"%{query.upper()}%"
        if exchange is not None:
            sql = """
                SELECT i.exchange, i.symbol
                FROM instruments i
                JOIN equities e ON e.instrument_id = i.id
                WHERE UPPER(i.symbol) LIKE ? AND i.exchange = ?
                ORDER BY i.exchange, i.symbol
                LIMIT 50
            """
            params: tuple[Any, ...] = (pattern, exchange)
        else:
            sql = """
                SELECT i.exchange, i.symbol
                FROM instruments i
                JOIN equities e ON e.instrument_id = i.id
                WHERE UPPER(i.symbol) LIKE ?
                ORDER BY i.exchange, i.symbol
                LIMIT 50
            """
            params = (pattern,)
        async with self._conn_or_raise().execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [Equity(exchange=Exchange(row[0]), symbol=row[1]) for row in rows]

    async def get_underlyings(self, exchange: str | None = None) -> list[Equity | Index]:
        """Return all indices and equities that have at least one future or option."""
        if exchange is not None:
            sql = """
                SELECT DISTINCT i.exchange, i.symbol, i.segment
                FROM instruments i JOIN equities e ON e.instrument_id = i.id
                WHERE i.id IN (SELECT underlying_id FROM futures
                               UNION SELECT underlying_id FROM options)
                AND i.exchange = ?
                ORDER BY i.exchange, i.symbol
            """
            params: tuple[Any, ...] = (exchange,)
        else:
            sql = """
                SELECT DISTINCT i.exchange, i.symbol, i.segment
                FROM instruments i JOIN equities e ON e.instrument_id = i.id
                WHERE i.id IN (SELECT underlying_id FROM futures
                               UNION SELECT underlying_id FROM options)
                ORDER BY i.exchange, i.symbol
            """
            params = ()
        async with self._conn_or_raise().execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [
            Index(exchange=Exchange(row[0]), symbol=row[1])
            if row[2] == "INDICES"
            else Equity(exchange=Exchange(row[0]), symbol=row[1])
            for row in rows
        ]

    async def get_all_equities(self, exchange: str | None = None) -> list[Equity | Index]:
        """Return every equity and index in the DB (no derivatives filter)."""
        if exchange is not None:
            sql = """
                SELECT i.exchange, i.symbol, i.segment
                FROM instruments i JOIN equities e ON e.instrument_id = i.id
                WHERE i.exchange = ?
                ORDER BY i.exchange, i.symbol
            """
            params: tuple[Any, ...] = (exchange,)
        else:
            sql = """
                SELECT i.exchange, i.symbol, i.segment
                FROM instruments i JOIN equities e ON e.instrument_id = i.id
                ORDER BY i.exchange, i.symbol
            """
            params = ()
        async with self._conn_or_raise().execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [
            Index(exchange=Exchange(row[0]), symbol=row[1])
            if row[2] == "INDICES"
            else Equity(exchange=Exchange(row[0]), symbol=row[1])
            for row in rows
        ]

    async def get_instrument_info(self, instrument: Instrument) -> InstrumentInfo:
        """Return lot size, tick size, name and segment for any instrument.

        Raises:
            InstrumentNotFoundError: if the instrument is not present in the DB.
        """
        sql = """
            SELECT i.name, i.lot_size, i.tick_size, i.segment
            FROM instruments i
            WHERE i.exchange = ? AND i.symbol = ?
            LIMIT 1
        """
        async with self._conn_or_raise().execute(
            sql, (str(instrument.exchange), instrument.symbol)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            raise InstrumentNotFoundError(
                f"Instrument not found: {instrument.exchange}:{instrument.symbol}"
            )
        return InstrumentInfo(
            instrument=instrument,
            name=row[0],
            lot_size=int(row[1]),
            tick_size=float(row[2]),
            segment=row[3],
        )

    async def get_option_chain(self, underlying: Instrument, expiry: date) -> OptionChain:
        """Return all CE/PE pairs at every strike for a given underlying + expiry."""
        sql = """
            SELECT o.strike, o.option_type, opt.exchange, u.symbol
            FROM options o
            JOIN instruments opt ON opt.id = o.instrument_id
            JOIN instruments u ON u.id = o.underlying_id
            WHERE u.exchange = ? AND u.symbol = ? AND o.expiry = ?
            ORDER BY o.strike ASC, o.option_type ASC
        """
        async with self._conn_or_raise().execute(
            sql, (str(underlying.exchange), underlying.symbol, expiry.isoformat())
        ) as cur:
            rows = await cur.fetchall()

        strikes: dict[float, dict[str, Option]] = {}
        for row in rows:
            strike, option_type, u_exchange, u_symbol = row
            strike = float(strike)
            opt = Option(
                exchange=Exchange(u_exchange),
                symbol=u_symbol,
                expiry=expiry,
                strike=strike,
                option_type=OptionType(option_type),
            )
            strikes.setdefault(strike, {})[option_type] = opt

        entries = [
            OptionChainEntry(strike=strike, ce=side_map.get("CE"), pe=side_map.get("PE"))
            for strike, side_map in sorted(strikes.items())
        ]
        return OptionChain(underlying=underlying, expiry=expiry, entries=entries)

    async def execute(self, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        """Execute raw SQL against the instrument DB and return all rows.

        This is an escape hatch for advanced local discovery queries not covered
        by the typed methods above.
        """
        async with self._conn_or_raise().execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [tuple(row) for row in rows]
