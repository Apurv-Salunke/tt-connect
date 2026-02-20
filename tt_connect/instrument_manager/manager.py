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
        parsed = await fetch_fn()
        await truncate_all(self._conn)
        await self._insert(parsed)
        await self._set_last_updated()
        logger.info("Instrument refresh complete")

    async def _insert(self, parsed) -> None:
        # Chunk 1: indices — must go in before futures/options reference them
        await self._insert_indices(parsed.indices)

        # Chunk 2: equities
        await self._insert_equities(parsed.equities)

        # Chunk 3: futures   — coming soon
        # Chunk 4: options   — coming soon

        await self._conn.commit()

    async def _insert_indices(self, indices) -> None:
        if not indices:
            return

        logger.info(f"Inserting {len(indices)} indices")

        for idx in indices:
            # 1. Base instrument record
            cursor = await self._conn.execute(
                """
                INSERT INTO instruments (exchange, symbol, segment, name, lot_size, tick_size)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (idx.exchange, idx.symbol, idx.segment, idx.name, idx.lot_size, idx.tick_size),
            )
            instrument_id = cursor.lastrowid

            # 2. Equities sub-table (indices have no ISIN)
            await self._conn.execute(
                "INSERT INTO equities (instrument_id, isin) VALUES (?, NULL)",
                (instrument_id,),
            )

            # 3. Broker token
            await self._conn.execute(
                """
                INSERT INTO broker_tokens (instrument_id, broker_id, token, broker_symbol)
                VALUES (?, ?, ?, ?)
                """,
                (instrument_id, self._broker_id, idx.broker_token, idx.broker_symbol),
            )

    async def _insert_equities(self, equities) -> None:
        if not equities:
            return

        logger.info(f"Inserting {len(equities)} equities")

        for eq in equities:
            # 1. Base instrument record
            cursor = await self._conn.execute(
                """
                INSERT INTO instruments (exchange, symbol, segment, name, lot_size, tick_size)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (eq.exchange, eq.symbol, eq.segment, eq.name, eq.lot_size, eq.tick_size),
            )
            instrument_id = cursor.lastrowid

            # 2. Equities sub-table (Zerodha CSV has no ISIN)
            await self._conn.execute(
                "INSERT INTO equities (instrument_id, isin) VALUES (?, NULL)",
                (instrument_id,),
            )

            # 3. Broker token
            await self._conn.execute(
                """
                INSERT INTO broker_tokens (instrument_id, broker_id, token, broker_symbol)
                VALUES (?, ?, ?, ?)
                """,
                (instrument_id, self._broker_id, eq.broker_token, eq.broker_symbol),
            )

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

    @property
    def connection(self) -> aiosqlite.Connection:
        assert self._conn, "InstrumentManager not initialized"
        return self._conn
