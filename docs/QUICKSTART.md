# Quick Start: Your First Order in 5 Minutes

This guide gets you from zero to placing live orders with `tt-connect`.

---

## Prerequisites

- Python 3.11+
- Poetry installed
- Broker credentials (Zerodha or AngelOne)

---

## Step 1: Install

```bash
pip install tt-connect
```

Or install from source for local development:

```bash
cd connect
poetry install
```

---

## Step 2: Set Up Credentials

### Option A: Using `.env` File (Recommended)

```bash
cp .env.example .env
```

Then edit `.env` with your credentials:

**For Zerodha:**
```env
ZERODHA_API_KEY=your_kite_api_key
ZERODHA_ACCESS_TOKEN=your_access_token
```

**For AngelOne (Auto mode with TOTP):**
```env
ANGELONE_API_KEY=your_smart_api_key
ANGELONE_CLIENT_ID=your_client_id
ANGELONE_PIN=1234
ANGELONE_TOTP_SECRET=JBSWY3DPEHPK3PXP
```

**For AngelOne (Manual mode with pre-obtained token):**
```env
ANGELONE_API_KEY=your_smart_api_key
ANGELONE_ACCESS_TOKEN=your_jwt_token
```

### Option B: Environment Variables

```bash
# Zerodha
export ZERODHA_API_KEY=your_kite_api_key
export ZERODHA_ACCESS_TOKEN=your_access_token

# AngelOne
export ANGELONE_API_KEY=your_smart_api_key
export ANGELONE_CLIENT_ID=your_client_id
export ANGELONE_PIN=1234
export ANGELONE_TOTP_SECRET=JBSWY3DPEHPK3PXP
```

### Where to Get Credentials

**Zerodha:**
1. Register app at https://kite.trade/ to get your `api_key` and `api_secret`
2. Each trading day, complete the OAuth login flow to get a fresh `access_token`:
   - Visit `https://kite.trade/connect/login?api_key=<your_api_key>&v=3`
   - Log in and authorize — you'll be redirected to your redirect URL with `?request_token=<token>`
   - Exchange the `request_token` for an `access_token` using the Kite Connect SDK or API
3. Tokens expire at the end of each trading day (SEBI requirement) — the login flow must be repeated daily

**AngelOne:**
1. Register at https://smartapi.angelbroking.com/ to get your `api_key`
2. Enable TOTP in the AngelOne mobile app (Profile → Settings → Enable TOTP) — when prompted, instead of scanning with your authenticator app, tap "Copy key" or "Show secret" to get the Base32 secret string (looks like `JBSWY3DPEHPK3PXP`) — use this as `totp_secret`
3. Tokens expire daily at midnight IST — auto mode re-authenticates on the next `init()` call; manual mode requires you to supply a fresh `access_token` each day

---

## Step 3: Initialize the Client

The recommended pattern is a context manager — resources are released automatically:

```python
from tt_connect import TTConnect

# Zerodha
with TTConnect("zerodha", {
    "api_key": "YOUR_API_KEY",
    "access_token": "YOUR_ACCESS_TOKEN",
}) as broker:
    profile = broker.get_profile()
    print(f"Logged in as: {profile.name}")
```

```python
from tt_connect import TTConnect

# AngelOne (Auto mode — handles TOTP and session refresh)
with TTConnect("angelone", {
    "auth_mode": "auto",
    "api_key": "YOUR_API_KEY",
    "client_id": "YOUR_CLIENT_ID",
    "pin": "1234",
    "totp_secret": "JBSWY3DPEHPK3PXP",
}) as broker:
    profile = broker.get_profile()
    print(f"Logged in as: {profile.name}")
```

Or manage the lifecycle manually:

```python
from tt_connect import TTConnect

broker = TTConnect("zerodha", {"api_key": "...", "access_token": "..."})
# init() is called automatically — broker is ready to use immediately

# ... use broker ...

broker.close()  # Always close when done
```

**State Management:** The client tracks connection state internally:
- Calling methods before the client is connected raises `ClientNotConnectedError`
- Calling methods after `close()` raises `ClientClosedError`

**Session Expiry:** All broker tokens expire at end-of-day (SEBI requirement). Each new trading day you must supply fresh credentials:
- **Zerodha:** repeat the OAuth flow to get a new `access_token`
- **AngelOne (auto mode):** tt-connect re-authenticates automatically on the next `init()` call
- **AngelOne (manual mode):** supply a fresh `access_token` each day

---

## Step 4: Get Profile and Funds

```python
from tt_connect import TTConnect

with TTConnect("zerodha", config) as broker:
    # Profile
    profile = broker.get_profile()
    print(f"Client ID: {profile.client_id}")
    print(f"Name: {profile.name}")
    print(f"Email: {profile.email}")

    # Funds
    funds = broker.get_funds()
    print(f"Available: ₹{funds.available:,.2f}")
    print(f"Used: ₹{funds.used:,.2f}")
    print(f"Total: ₹{funds.total:,.2f}")
```

---

## Step 5: Place Your First Order

```python
from tt_connect import TTConnect
from tt_connect.instruments import Equity
from tt_connect.enums import Exchange, Side, ProductType, OrderType

with TTConnect("zerodha", config) as broker:
    order_id = broker.place_order(
        instrument=Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
        side=Side.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        product=ProductType.CNC,
    )
    print(f"Order placed: {order_id}")
```

**Limit Order:**
```python
order_id = broker.place_order(
    instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
    side=Side.BUY,
    qty=10,
    order_type=OrderType.LIMIT,
    product=ProductType.CNC,
    price=800.00,
)
```

---

## Step 6: Modify or Cancel Orders

```python
# Modify order
broker.modify_order(
    order_id=order_id,
    price=801.00,
    qty=10,
)

# Cancel order
broker.cancel_order(order_id)

# Cancel all open orders
cancelled, failed = broker.cancel_all_orders()
print(f"Cancelled {len(cancelled)} orders")
```

---

## Step 7: View Portfolio

```python
# Holdings (long-term positions)
holdings = broker.get_holdings()
for h in holdings:
    print(f"{h.instrument.symbol}: qty={h.qty}, avg=₹{h.avg_price:.2f}, pnl=₹{h.pnl:.2f}")

# Open positions (intraday)
positions = broker.get_positions()
for p in positions:
    print(f"{p.instrument.symbol}: qty={p.qty}, pnl=₹{p.pnl:.2f}")

# Order book
# Note: o.instrument is always None from get_orders() — broker APIs do not
# return enough data to reconstruct an Instrument without an extra DB lookup.
orders = broker.get_orders()
for o in orders:
    sym = o.instrument.symbol if o.instrument else "—"
    print(f"{o.id}: {sym} {o.side} qty={o.qty} status={o.status}")

# Trade book (executed orders)
trades = broker.get_trades()
for t in trades:
    print(f"{t.order_id}: {t.instrument.symbol} qty={t.qty} avg=₹{t.avg_price:.2f}")
```

---

## Step 8: Use Instruments (Equity, Future, Option)

```python
from tt_connect.instruments import Equity, Future, Option, Index
from tt_connect.enums import Exchange, OptionType

# Index
nifty = Index(exchange=Exchange.NSE, symbol="NIFTY")

# Equity
reliance = Equity(exchange=Exchange.NSE, symbol="RELIANCE")

# Future (expiry is YYYY-MM-DD format)
nifty_fut = Future(
    exchange=Exchange.NSE,
    symbol="NIFTY",
    expiry="2025-03-27",
)

# Option
nifty_ce = Option(
    exchange=Exchange.NSE,
    symbol="NIFTY",
    expiry="2025-03-27",
    strike=25000.0,
    option_type=OptionType.CE,
)
```

**Note:** Instrument validation uses the live database — invalid symbols, expiries, or strikes fail at construction time, not at order placement.

---

## Step 9: Real-Time Streaming

```python
import asyncio
from tt_connect import AsyncTTConnect
from tt_connect.instruments import Equity
from tt_connect.enums import Exchange

async def on_tick(tick) -> None:
    print(f"TICK: {tick.instrument.symbol} ltp=₹{tick.ltp:.2f}")

async def main():
    async with AsyncTTConnect("angelone", config) as broker:
        instruments = [
            Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
            Equity(exchange=Exchange.NSE, symbol="INFY"),
        ]
        await broker.subscribe(instruments, on_tick)
        
        # Stream for 10 seconds
        await asyncio.sleep(10)
        
        await broker.unsubscribe(instruments)

asyncio.run(main())
```

---

## Complete Working Examples

Want to see everything in one file?

- **Zerodha:** `examples/zerodha.py` — 250 lines, covers every feature
- **AngelOne:** `examples/angelone.py` — 280 lines, shows both auth modes

Both files are fully commented and ready to run:

```bash
python examples/zerodha.py
python examples/angelone.py
```

See [EXAMPLES.md](./EXAMPLES.md) for details.

---

## Error Handling

```python
from tt_connect.exceptions import (
    ClientNotConnectedError,
    ClientClosedError,
    InsufficientFundsError,
    InvalidOrderError,
    RateLimitError,
    TTConnectError,
)

try:
    broker.place_order(req)
except InsufficientFundsError:
    print("Not enough margin")
except InvalidOrderError as e:
    print(f"Bad order params: {e}")
except RateLimitError:
    print("Too many requests — slow down")
except TTConnectError as e:
    print(f"Broker error: {e.broker_code}")
```

---

## Unsupported Features

Some brokers don't support certain segments. The library fails fast with a clear error:

```python
from tt_connect.instruments import Equity
from tt_connect.enums import Exchange

# MCX is not supported by Zerodha
gold = Equity(exchange=Exchange.MCX, symbol="GOLD")

with TTConnect("zerodha", config) as broker:
    broker.place_order(instrument=gold, side=Side.BUY, qty=1,
                       order_type=OrderType.MARKET, product=ProductType.CNC)
    # Raises: UnsupportedFeatureError: Zerodha does not support MCX segment
    # (Raised before any HTTP call is made)
```

---

## Async API

`tt-connect` is built async-first. `TTConnect` is a thin sync wrapper over `AsyncTTConnect`:

```python
from tt_connect import AsyncTTConnect

async def main():
    async with AsyncTTConnect("zerodha", config) as broker:
        profile = await broker.get_profile()
        funds = await broker.get_funds()
        order_id = await broker.place_order(instrument=..., side=Side.BUY, qty=1,
                                             order_type=OrderType.MARKET, product=ProductType.CNC)

asyncio.run(main())
```

---

## Next Steps

- **Complete Examples:** [EXAMPLES.md](./EXAMPLES.md) — full working code
- **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) — common errors and fixes
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md) — how it works internally
- **Contributor Guide:** [CONTRIBUTOR_GUIDE.md](./CONTRIBUTOR_GUIDE.md) — local setup and testing
