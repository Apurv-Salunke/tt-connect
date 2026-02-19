# tt-connect: Desired State

## The Goal

A developer using tt-connect never writes broker-specific code.
Broker is a configuration detail, not an architectural one.

---

## Decisions Locked In

### 1. Auth is a Config, Not Code
- Pass credentials, the library handles OAuth, TOTP, session refresh, and daily re-login
- Swapping broker does not change any auth-handling code

```python
broker = TTConnect("zerodha", config)
broker.login()
```

### 2. Typed Instrument Objects + Enums, Not Strings
- Instruments are strongly-typed objects — no magic strings
- Symbols follow NSE official naming conventions as the canonical standard
- tt-connect translates to broker-specific format internally
- Validation at construction time — bad inputs fail early, not at broker call time

```python
from tt_connect.instruments import Equity, Future, Option
from tt_connect.enums import Exchange, OptionType, ProductType, OrderType, Side

equity = Equity(exchange=Exchange.NSE, symbol="RELIANCE")
future = Future(exchange=Exchange.NFO, symbol="NIFTY", expiry="2025-01-30")
option = Option(exchange=Exchange.NFO, symbol="NIFTY", expiry="2025-01-30", strike=18000, option_type=OptionType.CE)
```

Enums cover all categorical inputs: `Exchange`, `OptionType`, `ProductType`, `OrderType`, `Side`

### 3. One Canonical Data Model
- Every broker response is normalized to a standard shape before it reaches the caller
- No broker-specific keys leak into application code

### 4. One Order Interface

```python
broker.place_order(instrument=equity, qty=10, side=Side.BUY, product=ProductType.CNC, order_type=OrderType.MARKET)
```

### 5. One Streaming Interface

```python
broker.subscribe([equity, option], on_tick=handler)
```

### 6. Both Sync and Async Clients
- Core logic written once, exposed via two client classes
- Sync client wraps async using `asyncio.run()`
- Streaming is inherently async — sync streaming blocks the thread, this is documented

```python
# sync
broker = TTConnect("zerodha", config)
broker.place_order(...)

# async
broker = AsyncTTConnect("zerodha", config)
await broker.place_order(...)
```

### 7. Unified Error Handling
- Consistent exception hierarchy — `TTConnectError` and subclasses
- Rate limiting and retryable vs non-retryable errors handled by the library

### 8. Broker is a One-Line Swap
- No strategy or engine code needs to know which broker is active

---

## What the Developer Never Has to Do

- Parse broker-specific response envelopes
- Handle session expiry manually
- Translate symbol formats
- Know which HTTP method or encoding a broker uses
- Write broker-specific error handling
