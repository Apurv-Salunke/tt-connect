"""
Live integration test — Futures & Options via the public AsyncTTConnect API.

Tests NIFTY, BANKNIFTY, and MIDCPNIFTY futures + options end-to-end:
  1. Init   — login + instrument download + DB insert (full pipeline)
  2. Counts — verify futures and options rows in DB
  3. Futures — resolve nearest-expiry future for each index
  4. Options — resolve nearest-expiry ATM CE + PE for each index

Usage:
    python get_token.py           # if access_token is stale
    python test_live_fno.py
"""

import asyncio
import os
import time
from datetime import date
from pathlib import Path


def _load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

_load_env()

import tt_connect.instrument_manager.db as db_module
db_module.DB_PATH = Path("/tmp/tt_live_fno/instruments.db")
Path("/tmp/tt_live_fno").mkdir(exist_ok=True)
if db_module.DB_PATH.exists():
    db_module.DB_PATH.unlink()

from tt_connect.client import AsyncTTConnect
from tt_connect.instruments import Future, Option
from tt_connect.enums import Exchange, OptionType


INDICES = [
    ("NSE", "NIFTY"),
    ("NSE", "BANKNIFTY"),
    ("NSE", "MIDCPNIFTY"),
]


async def run():
    config = {
        "api_key":      os.environ["ZERODHA_API_KEY"],
        "access_token": os.environ["ZERODHA_ACCESS_TOKEN"],
    }

    # -------------------------------------------------------------------
    # Init
    # -------------------------------------------------------------------
    print("Initialising broker (login + instrument download + DB insert) ...")
    t0 = time.perf_counter()

    broker = AsyncTTConnect("zerodha", config)
    await broker.init()

    print(f"Ready in {time.perf_counter() - t0:.1f}s")
    print()

    conn = broker._instrument_manager.connection

    async def scalar(q, *args):
        async with conn.execute(q, args) as cur:
            return (await cur.fetchone())[0]

    # -------------------------------------------------------------------
    # DB counts
    # -------------------------------------------------------------------
    print("DB counts:")
    total   = await scalar("SELECT COUNT(*) FROM instruments")
    futures = await scalar("SELECT COUNT(*) FROM futures")
    options = await scalar("SELECT COUNT(*) FROM options")
    tokens  = await scalar("SELECT COUNT(*) FROM broker_tokens")
    print(f"  instruments   : {total}")
    print(f"  futures       : {futures}")
    print(f"  options       : {options}")
    print(f"  broker_tokens : {tokens}")
    print()

    # -------------------------------------------------------------------
    # Futures — nearest expiry for each index
    # -------------------------------------------------------------------
    print("=" * 55)
    print("FUTURES")
    print("=" * 55)
    print(f"  {'exchange:symbol':<20} {'expiry':<14} token")
    print("  " + "-" * 45)

    for uex, usym in INDICES:
        expiry_str = await scalar("""
            SELECT MIN(f.expiry)
            FROM futures f
            JOIN instruments u ON u.id = f.underlying_id
            WHERE u.exchange = ? AND u.symbol = ?
        """, uex, usym)

        if not expiry_str:
            print(f"  {uex}:{usym:<17}  — no futures found")
            continue

        instrument = Future(
            exchange=Exchange.NSE if uex == "NSE" else Exchange.BSE,
            symbol=usym,
            expiry=date.fromisoformat(expiry_str),
        )
        token = await broker._resolve(instrument)
        label = f"{uex}:{usym}"
        print(f"  {label:<20} {expiry_str:<14} {token}")

    print()

    # -------------------------------------------------------------------
    # Options — nearest expiry, 3 strikes (ITM / ATM / OTM), CE + PE
    # -------------------------------------------------------------------
    print("=" * 55)
    print("OPTIONS")
    print("=" * 55)

    for uex, usym in INDICES:
        exchange = Exchange.NSE if uex == "NSE" else Exchange.BSE

        # Nearest expiry for this underlying
        expiry_str = await scalar("""
            SELECT MIN(o.expiry)
            FROM options o
            JOIN instruments u ON u.id = o.underlying_id
            WHERE u.exchange = ? AND u.symbol = ?
        """, uex, usym)

        if not expiry_str:
            print(f"  {uex}:{usym}  — no options found")
            continue

        # Pick 3 representative strikes (low / mid / high of available range)
        async with conn.execute("""
            SELECT DISTINCT o.strike
            FROM options o
            JOIN instruments u ON u.id = o.underlying_id
            WHERE u.exchange = ? AND u.symbol = ? AND o.expiry = ?
            ORDER BY o.strike
        """, (uex, usym, expiry_str)) as cur:
            all_strikes = [r[0] for r in await cur.fetchall()]

        n = len(all_strikes)
        sampled = [
            all_strikes[n // 4],       # lower quartile
            all_strikes[n // 2],       # mid (approx ATM)
            all_strikes[3 * n // 4],   # upper quartile
        ]

        print(f"  {uex}:{usym}  expiry={expiry_str}  ({n} strikes)")
        print(f"    {'strike':<10} {'type':<5} token")
        print("    " + "-" * 30)

        for strike in sampled:
            for ot, ot_enum in [("CE", OptionType.CE), ("PE", OptionType.PE)]:
                instrument = Option(
                    exchange=exchange,
                    symbol=usym,
                    expiry=date.fromisoformat(expiry_str),
                    strike=strike,
                    option_type=ot_enum,
                )
                token = await broker._resolve(instrument)
                print(f"    {strike:<10} {ot:<5} {token}")
        print()

    await broker.close()
    print("All checks passed.")


asyncio.run(run())
