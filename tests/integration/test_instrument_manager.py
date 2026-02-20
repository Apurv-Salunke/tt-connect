import pytest
import aiosqlite
from tt_connect.instrument_manager.manager import InstrumentManager
from tt_connect.adapters.zerodha.parser import parse
from tt_connect.enums import OnStale
from tt_connect.instrument_manager.db import truncate_all

async def _count(db, table: str) -> int:
    async with db.execute(f"SELECT COUNT(*) FROM {table}") as cur:
        row = await cur.fetchone()
        return row[0]

async def test_insert_counts(populated_db):
    assert await _count(populated_db, "instruments") == 12
    assert await _count(populated_db, "equities") == 5  # 2 indices (also in equities) + 3 eqs
    assert await _count(populated_db, "futures") == 3
    assert await _count(populated_db, "options") == 4
    assert await _count(populated_db, "broker_tokens") == 12

async def test_futures_fk_integrity(populated_db):
    async with populated_db.execute("""
        SELECT COUNT(*) FROM futures f
        LEFT JOIN instruments u ON u.id = f.underlying_id
        WHERE u.id IS NULL
    """) as c:
        orphans = (await c.fetchone())[0]
    assert orphans == 0

async def test_options_fk_integrity(populated_db):
    async with populated_db.execute("""
        SELECT COUNT(*) FROM options o
        LEFT JOIN instruments u ON u.id = o.underlying_id
        WHERE u.id IS NULL
    """) as c:
        orphans = (await c.fetchone())[0]
    assert orphans == 0

async def test_idempotent_insert(db, zerodha_csv):
    """Inserting the same CSV twice (after truncate) yields same counts."""
    manager = InstrumentManager(broker_id="zerodha", on_stale=OnStale.FAIL)
    manager._conn = db
    parsed = parse(zerodha_csv)
    await manager._insert(parsed)
    first_count = await _count(db, "instruments")

    await truncate_all(db)
    await manager._insert(parsed)
    second_count = await _count(db, "instruments")

    assert first_count == second_count
    assert first_count == 12

from unittest.mock import AsyncMock
from datetime import date, timedelta
from freezegun import freeze_time

async def test_is_stale_behavior(db):
    manager = InstrumentManager(broker_id="zerodha")
    manager._conn = db
    
    # 1. No meta record -> stale
    assert await manager._is_stale() is True
    
    # 2. Today's meta record -> not stale
    await manager._set_last_updated()
    assert await manager._is_stale() is False
    
    # 3. Yesterday's meta record -> stale
    with freeze_time(date.today() + timedelta(days=1)):
        assert await manager._is_stale() is True

async def test_ensure_fresh_calls_refresh_only_when_stale(db):
    manager = InstrumentManager(broker_id="zerodha")
    manager._conn = db
    
    fetch_mock = AsyncMock(return_value=parse("")) # Empty parsed result
    
    # First call: stale (no meta) -> should call refresh
    await manager.ensure_fresh(fetch_mock)
    assert fetch_mock.await_count == 1
    
    # Second call: not stale (just updated) -> should NOT call refresh
    await manager.ensure_fresh(fetch_mock)
    assert fetch_mock.await_count == 1
