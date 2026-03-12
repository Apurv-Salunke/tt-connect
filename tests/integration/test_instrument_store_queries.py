"""Integration tests for new InstrumentManager discovery query methods."""

from __future__ import annotations

from datetime import date

import pytest

from tt_connect.core.exceptions import InstrumentNotFoundError
from tt_connect.core.models.enums import OnStale
from tt_connect.core.models.instruments import Equity, Index, Option
from tt_connect.core.store.manager import InstrumentManager


def _manager(db) -> InstrumentManager:
    m = InstrumentManager(broker_id="zerodha", on_stale=OnStale.FAIL)
    m._conn = db
    m.queries.bind(db)
    return m


# ---------------------------------------------------------------------------
# get_underlyings
# ---------------------------------------------------------------------------

async def test_get_underlyings_returns_only_those_with_derivatives(populated_db):
    mgr = _manager(populated_db)
    results = await mgr.queries.get_underlyings()
    symbols = [(str(r.exchange), r.symbol) for r in results]
    # Fixture has derivatives for NIFTY (NSE), SENSEX (BSE), RELIANCE (NSE), SBIN (NSE)
    assert ("NSE", "NIFTY") in symbols
    assert ("BSE", "SENSEX") in symbols
    assert ("NSE", "RELIANCE") in symbols
    assert ("NSE", "SBIN") in symbols
    # BSE RELIANCE has no derivatives — must not appear
    assert ("BSE", "RELIANCE") not in symbols


async def test_get_underlyings_index_typed_correctly(populated_db):
    mgr = _manager(populated_db)
    results = await mgr.queries.get_underlyings()
    by_symbol = {r.symbol: r for r in results}
    assert isinstance(by_symbol["NIFTY"], Index)
    assert isinstance(by_symbol["SENSEX"], Index)
    assert isinstance(by_symbol["RELIANCE"], Equity)
    assert isinstance(by_symbol["SBIN"], Equity)


async def test_get_underlyings_filtered_by_exchange(populated_db):
    mgr = _manager(populated_db)
    results = await mgr.queries.get_underlyings(exchange="NSE")
    assert all(str(r.exchange) == "NSE" for r in results)
    symbols = [r.symbol for r in results]
    assert "NIFTY" in symbols
    assert "RELIANCE" in symbols
    assert "SBIN" in symbols
    assert "SENSEX" not in symbols


# ---------------------------------------------------------------------------
# get_all_equities
# ---------------------------------------------------------------------------

async def test_get_all_equities_returns_everything(populated_db):
    mgr = _manager(populated_db)
    results = await mgr.queries.get_all_equities()
    symbols = [(str(r.exchange), r.symbol) for r in results]
    # All equities and indices in the fixture
    assert ("NSE", "NIFTY") in symbols
    assert ("BSE", "SENSEX") in symbols
    assert ("NSE", "RELIANCE") in symbols
    assert ("BSE", "RELIANCE") in symbols
    assert ("NSE", "SBIN") in symbols
    # Futures/options should not appear
    assert len(results) == 5


async def test_get_all_equities_exchange_filter(populated_db):
    mgr = _manager(populated_db)
    results = await mgr.queries.get_all_equities(exchange="BSE")
    assert all(str(r.exchange) == "BSE" for r in results)
    symbols = [r.symbol for r in results]
    assert "SENSEX" in symbols
    assert "RELIANCE" in symbols
    assert "NIFTY" not in symbols


# ---------------------------------------------------------------------------
# get_instrument_info
# ---------------------------------------------------------------------------

async def test_get_instrument_info_returns_correct_metadata(populated_db):
    mgr = _manager(populated_db)
    reliance = Equity(exchange="NSE", symbol="RELIANCE")
    info = await mgr.queries.get_instrument_info(reliance)
    assert info.name == "RELIANCE INDUSTRIES"
    assert info.lot_size == 1
    assert info.tick_size == pytest.approx(0.05)
    assert info.instrument == reliance


async def test_get_instrument_info_raises_for_unknown(populated_db):
    mgr = _manager(populated_db)
    unknown = Equity(exchange="NSE", symbol="DOESNOTEXIST")
    with pytest.raises(InstrumentNotFoundError):
        await mgr.queries.get_instrument_info(unknown)


# ---------------------------------------------------------------------------
# get_option_chain
# ---------------------------------------------------------------------------

async def test_get_option_chain_pairs_ce_pe(populated_db):
    mgr = _manager(populated_db)
    nifty = Equity(exchange="NSE", symbol="NIFTY")
    expiry = date(2026, 2, 26)
    chain = await mgr.queries.get_option_chain(nifty, expiry)

    assert len(chain.entries) == 1
    entry = chain.entries[0]
    assert entry.strike == 23000.0
    assert entry.ce is not None
    assert entry.pe is not None
    assert isinstance(entry.ce, Option)
    assert isinstance(entry.pe, Option)


async def test_get_option_chain_handles_missing_pe(populated_db):
    mgr = _manager(populated_db)
    reliance = Equity(exchange="NSE", symbol="RELIANCE")
    expiry = date(2026, 2, 26)
    chain = await mgr.queries.get_option_chain(reliance, expiry)

    assert len(chain.entries) == 1
    entry = chain.entries[0]
    assert entry.strike == 2500.0
    assert entry.ce is not None
    assert entry.pe is None


async def test_get_option_chain_handles_missing_ce(populated_db):
    mgr = _manager(populated_db)
    sbin = Equity(exchange="NSE", symbol="SBIN")
    expiry = date(2026, 2, 26)
    chain = await mgr.queries.get_option_chain(sbin, expiry)

    assert len(chain.entries) == 1
    entry = chain.entries[0]
    assert entry.strike == 600.0
    assert entry.ce is None
    assert entry.pe is not None


async def test_get_option_chain_sorted_by_strike(populated_db):
    mgr = _manager(populated_db)
    nifty = Equity(exchange="NSE", symbol="NIFTY")
    expiry = date(2026, 2, 26)
    chain = await mgr.queries.get_option_chain(nifty, expiry)
    strikes = [e.strike for e in chain.entries]
    assert strikes == sorted(strikes)


# ---------------------------------------------------------------------------
# execute (raw SQL escape hatch) — tested via manager directly
# ---------------------------------------------------------------------------

async def test_execute_raw_sql(populated_db):
    mgr = _manager(populated_db)
    # Verify we can run arbitrary SQL and get rows back
    async with mgr._conn_or_raise().execute(
        "SELECT COUNT(*) FROM instruments"
    ) as cur:
        row = await cur.fetchone()
    assert row is not None
    assert row[0] > 0
