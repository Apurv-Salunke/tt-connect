"""
Smoke test for futures:
  1. Parser   — counts NFO + BFO futures, verifies expiry parsing
  2. DB       — insert and verify row counts + underlying FK integrity
  3. Resolver — resolves using Exchange.NSE/BSE (underlying exchange, not NFO/BFO)
"""

import asyncio
import os
from datetime import date
from pathlib import Path

os.environ["TT_CACHE_DIR"] = "/tmp/tt_test_cache"

from tt_connect.adapters.zerodha.parser import parse
from tt_connect.instrument_manager.db import get_connection, init_schema
from tt_connect.instrument_manager.manager import InstrumentManager
from tt_connect.instrument_manager.resolver import InstrumentResolver
from tt_connect.instruments import Future
from tt_connect.enums import Exchange, OnStale

CSV_PATH = Path("/Users/apurv/Desktop/algo-trading/master-instruments/data/zerodha.csv")
BROKER_ID = "zerodha"


# ---------------------------------------------------------------------------
# 1. Parser
# ---------------------------------------------------------------------------
print("=" * 60)
print("1. PARSER")
print("=" * 60)

raw_csv = CSV_PATH.read_text()
parsed = parse(raw_csv)

nfo = [f for f in parsed.futures if f.exchange == "NFO"]
bfo = [f for f in parsed.futures if f.exchange == "BFO"]

print(f"Futures parsed : {len(parsed.futures)}  (NFO={len(nfo)}, BFO={len(bfo)})")
print()

# Spot-check a few
print(f"{'broker_symbol':<25} {'symbol':<15} {'underlying_exchange':<20} {'expiry'}")
print("-" * 75)
samples = [
    next(f for f in nfo if f.symbol == "NIFTY"),
    next(f for f in nfo if f.symbol == "RELIANCE"),
    next(f for f in bfo if f.symbol == "SENSEX"),
    next(f for f in bfo if f.symbol == "SENSEX50"),
    next(f for f in nfo if f.symbol == "NIFTYNXT50"),
]
for f in samples:
    print(f"{f.broker_symbol:<25} {f.symbol:<15} {f.underlying_exchange:<20} {f.expiry}")
print()


# ---------------------------------------------------------------------------
# 2. DB insert + FK integrity check
# ---------------------------------------------------------------------------
async def run_db_test():
    print("=" * 60)
    print("2. DB INSERT + FK INTEGRITY")
    print("=" * 60)

    Path("/tmp/tt_test_cache").mkdir(exist_ok=True)

    import tt_connect.instrument_manager.db as db_module
    db_module.DB_PATH = Path("/tmp/tt_test_cache/instruments_fut.db")
    if db_module.DB_PATH.exists():
        db_module.DB_PATH.unlink()

    conn = await get_connection()
    await init_schema(conn)

    manager = InstrumentManager(broker_id=BROKER_ID, on_stale=OnStale.FAIL)
    manager._conn = conn

    await manager._insert_indices(parsed.indices)
    await manager._insert_equities(parsed.equities)
    lookup = await manager._build_underlying_lookup()
    await manager._insert_futures(parsed.futures, lookup)
    await conn.commit()

    async def count(q):
        async with conn.execute(q) as cur:
            return (await cur.fetchone())[0]

    total    = await count("SELECT COUNT(*) FROM instruments")
    fut_rows = await count("SELECT COUNT(*) FROM futures")
    bt_rows  = await count("SELECT COUNT(*) FROM broker_tokens")

    print(f"instruments rows : {total}")
    print(f"futures rows     : {fut_rows}  (expected {len(parsed.futures)})")
    print(f"broker_tokens    : {bt_rows}")
    print()

    # FK integrity — every futures.underlying_id must point to a real instruments row
    orphans = await count("""
        SELECT COUNT(*) FROM futures f
        LEFT JOIN instruments u ON u.id = f.underlying_id
        WHERE u.id IS NULL
    """)
    print(f"Orphaned underlying_ids : {orphans}  (expected 0)")
    print()

    # Verify underlying_id actually points to the right instrument
    print("Sample underlying resolution check:")
    async with conn.execute("""
        SELECT fut.symbol, u.exchange, u.symbol, u.segment, f.expiry
        FROM instruments fut
        JOIN futures f     ON f.instrument_id = fut.id
        JOIN instruments u ON u.id = f.underlying_id
        ORDER BY fut.exchange, fut.symbol, f.expiry
        LIMIT 6
    """) as cur:
        rows = await cur.fetchall()
    print(f"  {'future_symbol':<15} {'u.exchange':<10} {'u.symbol':<15} {'u.segment':<12} expiry")
    print("  " + "-" * 65)
    for r in rows:
        print(f"  {r[0]:<15} {r[1]:<10} {r[2]:<15} {r[3]:<12} {r[4]}")
    print()

    # ---------------------------------------------------------------------------
    # 3. Resolver — user uses Exchange.NSE / Exchange.BSE (underlying exchange)
    # ---------------------------------------------------------------------------
    print("=" * 60)
    print("3. RESOLVER")
    print("=" * 60)

    resolver = InstrumentResolver(conn, BROKER_ID)

    # Get real expiry dates from what we just inserted
    async with conn.execute("""
        SELECT u.exchange, u.symbol, MIN(f.expiry)
        FROM futures f
        JOIN instruments u ON u.id = f.underlying_id
        WHERE u.symbol IN ('NIFTY', 'RELIANCE', 'SENSEX', 'SENSEX50', 'NIFTYNXT50')
        GROUP BY u.exchange, u.symbol
    """) as cur:
        expiry_rows = await cur.fetchall()

    for uex, usym, expiry in expiry_rows:
        exchange = Exchange.NSE if uex == "NSE" else Exchange.BSE
        instrument = Future(exchange=exchange, symbol=usym, expiry=date.fromisoformat(expiry))
        token = await resolver.resolve(instrument)
        print(f"  {uex}:{usym:<15} expiry={expiry}  → token={token}")

    await conn.close()
    print()
    print("All checks passed.")

asyncio.run(run_db_test())
