import pytest
from datetime import date
from tt_connect.instrument_manager.resolver import InstrumentResolver
from tt_connect.instruments import Index, Equity, Future, Option
from tt_connect.enums import Exchange
from tt_connect.exceptions import InstrumentNotFoundError

async def test_resolve_index(populated_db):
    resolver = InstrumentResolver(populated_db, "zerodha")
    # NIFTY 50 in CSV is mapped to NIFTY canonical symbol
    token = await resolver.resolve(Index(exchange=Exchange.NSE, symbol="NIFTY"))
    assert token == "256265"
    
    # SENSEX
    token = await resolver.resolve(Index(exchange=Exchange.BSE, symbol="SENSEX"))
    assert token == "256266"

async def test_resolve_equity(populated_db):
    resolver = InstrumentResolver(populated_db, "zerodha")
    token = await resolver.resolve(Equity(exchange=Exchange.NSE, symbol="RELIANCE"))
    assert token == "738561"
    
    token = await resolver.resolve(Equity(exchange=Exchange.BSE, symbol="RELIANCE"))
    assert token == "1280642"

async def test_resolve_future(populated_db):
    resolver = InstrumentResolver(populated_db, "zerodha")
    # Future resolution uses underlying exchange (NSE), not NFO
    token = await resolver.resolve(Future(
        exchange=Exchange.NSE, 
        symbol="NIFTY", 
        expiry=date(2026, 2, 26)
    ))
    assert token == "1000001"
    
    # BFO future
    token = await resolver.resolve(Future(
        exchange=Exchange.BSE,
        symbol="SENSEX",
        expiry=date(2026, 2, 26)
    ))
    assert token == "1000003"

async def test_resolve_option(populated_db):
    resolver = InstrumentResolver(populated_db, "zerodha")
    token = await resolver.resolve(Option(
        exchange=Exchange.NSE,
        symbol="NIFTY",
        expiry=date(2026, 2, 26),
        strike=23000.0,
        option_type="CE"
    ))
    assert token == "1000004"

async def test_resolve_unknown_raises(populated_db):
    resolver = InstrumentResolver(populated_db, "zerodha")
    with pytest.raises(InstrumentNotFoundError):
        await resolver.resolve(Equity(exchange=Exchange.NSE, symbol="NONEXISTENT"))

async def test_resolve_caching(populated_db):
    resolver = InstrumentResolver(populated_db, "zerodha")
    inst = Equity(exchange=Exchange.NSE, symbol="SBIN")
    
    token1 = await resolver.resolve(inst)
    assert token1 == "1280641"
    
    # Verify it's in cache
    assert inst in resolver._cache
    assert resolver._cache[inst] == "1280641"
    
    # Second call should use cache
    token2 = await resolver.resolve(inst)
    assert token2 == token1
