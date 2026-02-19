# tt-connect: Architecture

## Responsibilities

1. Parsing, storing and maintaining instruments into a common SQLite DB for easy access and resolution
2. REST APIs — Auth, Profile, Funds, Holdings, Positions, Trades, Orders
3. WebSocket — streaming market data and order updates

---

## Project Structure

```
tt_connect/
├── __init__.py
├── client.py              # TTConnect + AsyncTTConnect
├── enums.py               # Exchange, OrderType, ProductType, Side, OptionType
├── instruments.py         # Equity, Future, Option, Currency
├── models.py              # Order, Position, Holding, Tick, Profile, Fund
├── exceptions.py          # TTConnectError, UnsupportedFeatureError, etc.
├── capabilities.py        # Capabilities dataclass + internal checker
├── instrument_manager/
│   ├── manager.py         # fetch, store, refresh lifecycle
│   ├── db.py              # SQLite interface
│   └── resolver.py        # Instrument → broker token/symbol
├── adapters/
│   ├── base.py            # BrokerAdapter base + auto-registry
│   ├── zerodha/
│   │   ├── adapter.py
│   │   ├── auth.py
│   │   ├── transformer.py # request/response normalization
│   │   └── capabilities.py
│   └── upstox/
│       ├── adapter.py
│       ├── auth.py
│       ├── transformer.py
│       └── capabilities.py
└── ws/
    ├── client.py          # WebSocket lifecycle manager
    └── normalizer.py      # raw tick → Tick model
```

**To add a new broker: create a folder under `adapters/`, implement 4 files. Touch nothing else.**

---

## Technology Decisions

| Concern | Choice | Reason |
|---|---|---|
| Models / Validation | Pydantic v2 | Runtime type enforcement critical for trading; built in Rust, fast; ubiquitous dependency |
| SQLite access | `aiosqlite` | Thin async wrapper over stdlib `sqlite3`, minimal overhead, no ORM magic |
| HTTP client | `httpx` | Native async support, sync client available, clean API |
| Core design | Async-first | Trading engines are event-driven; sync client wraps async in one place |

---

## Components

### 1. Instrument Manager
- Fetches, parses and stores the instrument/symbol master into SQLite
- Handles refresh lifecycle (NSE updates instruments, lot sizes, expiry calendars)
- Core job: resolves a typed instrument object to the broker-specific token/symbol
- Resolution is cached via `lru_cache` — SQLite lookups happen once per session

### 2. Broker Adapters
- One adapter per broker, each subclassing `BrokerAdapter`
- Auto-registers itself via `__init_subclass__` — no registry file to maintain
- Each adapter has 4 files: `adapter.py`, `auth.py`, `transformer.py`, `capabilities.py`
- Nothing outside the adapter knows about broker internals

### 3. REST Client
- Unified interface for: Auth, Profile, Funds, Holdings, Positions, Orders, Trades
- Sits on top of the broker adapter
- Always returns normalized Pydantic models — no broker-specific keys leak out

### 4. WebSocket Client
- Manages the streaming connection lifecycle — connect, subscribe, unsubscribe, reconnect
- Normalizes raw tick data into standard `Tick` models before emitting to the caller

### 5. Models / Schemas
- Pydantic v2 models — validation, serialization, and type safety for free
- Frozen (immutable) by default
- `Order`, `Position`, `Holding`, `Tick`, `Profile`, `Fund`

### 6. Instruments + Enums
- Typed instrument classes: `Equity`, `Future`, `Option`, `Currency`
- Enums for all categorical inputs: `Exchange`, `OptionType`, `ProductType`, `OrderType`, `Side`
- Symbols follow NSE official naming conventions as the canonical standard
- Validation at object construction — bad inputs fail before any network call

---

## Key Patterns

### Auto-registration via `__init_subclass__`
No registry file to maintain. A broker registers itself just by existing.

```python
# adapters/base.py
class BrokerAdapter:
    _registry: ClassVar[dict[str, type[BrokerAdapter]]] = {}

    def __init_subclass__(cls, broker_id: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if broker_id:
            BrokerAdapter._registry[broker_id] = cls

# adapters/zerodha/adapter.py
class ZerodhaAdapter(BrokerAdapter, broker_id="zerodha"):
    ...

# client.py — broker resolved from registry at runtime
class AsyncTTConnect:
    def __init__(self, broker: str, config: BrokerConfig):
        self._adapter = BrokerAdapter._registry[broker](config)
```

### Capability Checking
Capability matrix is internal to each adapter. Check happens before any network call. No capability API is exposed to the user.

```python
# capabilities.py
@dataclass(frozen=True)
class Capabilities:
    segments: frozenset[Exchange]
    order_types: frozenset[OrderType]
    product_types: frozenset[ProductType]

    def verify(self, instrument: Instrument, order_type: OrderType, product_type: ProductType):
        if instrument.exchange not in self.segments:
            raise UnsupportedFeatureError(f"{instrument.exchange} segment not supported")
        if order_type not in self.order_types:
            raise UnsupportedFeatureError(f"{order_type} not supported")

# adapters/zerodha/capabilities.py
ZERODHA_CAPABILITIES = Capabilities(
    segments=frozenset({Exchange.NSE, Exchange.BSE, Exchange.NFO, Exchange.CDS}),
    order_types=frozenset({OrderType.MARKET, OrderType.LIMIT, OrderType.SL, OrderType.SL_M}),
    product_types=frozenset({ProductType.CNC, ProductType.MIS, ProductType.NRML}),
)
```

### Transformer Pattern
All request building and response parsing is isolated inside the broker adapter. Nothing else touches raw broker data.

```python
# adapters/zerodha/transformer.py
class ZerodhaTransformer:
    @staticmethod
    def to_order_params(instrument: Instrument, qty: int, side: Side, ...) -> dict:
        return {
            "tradingsymbol": instrument.symbol,
            "exchange": instrument.exchange.value,
            "transaction_type": "BUY" if side == Side.BUY else "SELL",
            ...
        }

    @staticmethod
    def to_order(raw: dict) -> Order:
        return Order(
            id=raw["order_id"],
            status=raw["status"],
            ...
        )
```

### Pydantic v2 Models
Validation, serialization, and IDE support for free. Frozen by default.

```python
# models.py
class Order(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    instrument: Instrument
    side: Side
    qty: int
    status: OrderStatus
    filled_qty: int = 0
    average_price: float | None = None
```

### Sync Wrapper
Core logic is async. Sync client wraps it in one place — zero duplication.

```python
# client.py
class TTConnect:
    def __init__(self, broker: str, config: BrokerConfig):
        self._async = AsyncTTConnect(broker, config)

    def place_order(self, **kwargs) -> Order:
        return asyncio.run(self._async.place_order(**kwargs))

    def get_holdings(self) -> list[Holding]:
        return asyncio.run(self._async.get_holdings())
```

### Instrument Resolution with `lru_cache`
Symbol resolution is a SQLite lookup. Cached after first call.

```python
# instrument_manager/resolver.py
class InstrumentResolver:
    @lru_cache(maxsize=10_000)
    def resolve(self, instrument: Instrument, broker_id: str) -> str:
        # SQLite lookup → broker-specific token
        ...
```

---

## Broker Capability Handling

Each broker adapter has an internal capability matrix declaring what it supports — segments, order types, product types etc.

**The library does not expose capabilities to the user.** If an unsupported operation is attempted, the library raises immediately with a clear error before any network call is made.

```
UnsupportedFeatureError: Zerodha does not support MCX segment
UnsupportedFeatureError: Upstox does not support SL_M order type
```

No warnings. No fallbacks. No user-side capability checks.

---

## Adding a New Broker

Create a folder under `adapters/`. Implement 4 files. Touch nothing else.

```
adapters/newbroker/
├── adapter.py       # subclass BrokerAdapter with broker_id="newbroker"
├── auth.py          # login, token refresh, session management
├── transformer.py   # to_order_params(), to_order(), to_tick(), etc.
└── capabilities.py  # NEWBROKER_CAPABILITIES = Capabilities(...)
```
