# Client API

## Trading clients

### Constructors

| Client | Signature | Notes |
|---|---|---|
| Sync | `TTConnect(broker: str, config: dict[str, Any])` | Initializes and logs in during construction |
| Async | `AsyncTTConnect(broker: str, config: dict[str, Any])` | Call `await init()` before use (or use `async with`) |

### Lifecycle methods

| Client | Method | Params | Returns | Common errors |
|---|---|---|---|---|
| Sync | `close` | — | `None` | `TTConnectError` |
| Async | `init` | — | `None` | `AuthenticationError`, `ConfigurationError`, `TTConnectError` |
| Async | `close` | — | `None` | `TTConnectError` |
| Async | `subscribe` | `instruments`, `on_tick`, `on_stale=None`, `on_recovered=None` | `None` | `ClientNotConnectedError`, `InstrumentNotFoundError` |
| Async | `unsubscribe` | `instruments` | `None` | `ClientNotConnectedError` |
| Async | `feed_state` *(property)* | — | `FeedState` | — |
| Async | `last_tick_at` | `instrument: Instrument` | `datetime \| None` | — |

### Portfolio / account methods

| Method | Params | Returns | Common errors |
|---|---|---|---|
| `get_profile` | — | `Profile` | `AuthenticationError`, `BrokerError` |
| `get_funds` | — | `Fund` | `AuthenticationError`, `BrokerError` |
| `get_holdings` | — | `list[Holding]` | `AuthenticationError`, `BrokerError` |
| `get_positions` | — | `list[Position]` | `AuthenticationError`, `BrokerError` |
| `get_trades` | — | `list[Trade]` | `AuthenticationError`, `BrokerError` |
| `get_quotes` | `instruments: list[Instrument]` | `list[Tick]` | `InstrumentNotFoundError`, `UnsupportedFeatureError` |
| `get_historical` | `instrument`, `interval`, `from_date`, `to_date` | `list[Candle]` | `InstrumentNotFoundError`, `UnsupportedFeatureError` |

### Order methods

| Method | Params | Returns | Common errors |
|---|---|---|---|
| `place_order` | `instrument, side, qty, order_type, product, price=None, trigger_price=None, tag=None` | `str` (order id) | `UnsupportedFeatureError`, `InsufficientFundsError`, `BrokerError` |
| `modify_order` | `order_id, qty=None, price=None, trigger_price=None, order_type=None` | `None` | `OrderNotFoundError`, `InvalidOrderError`, `BrokerError` |
| `cancel_order` | `order_id: str` | `None` | `OrderNotFoundError`, `BrokerError` |
| `cancel_all_orders` | — | `tuple[list[str], list[str]]` | `BrokerError` |
| `get_order` | `order_id: str` | `Order` | `OrderNotFoundError`, `BrokerError` |
| `get_orders` | — | `list[Order]` | `BrokerError` |
| `close_all_positions` | — | `tuple[list[str], list[str]]` | `BrokerError` |

!!! note "About `tag`"
    `tag` is an optional client-side correlation ID for tracing orders. If omitted, a UUID is auto-generated. Useful for idempotency checks — pass the same tag and verify via `get_orders()` to detect duplicates before retrying.

### GTT methods

| Method | Params | Returns | Common errors |
|---|---|---|---|
| `place_gtt` | `instrument, last_price, legs: list[GttLeg]` | `str` (gtt id) | `UnsupportedFeatureError`, `BrokerError` |
| `modify_gtt` | `gtt_id, instrument, last_price, legs: list[GttLeg]` | `None` | `UnsupportedFeatureError`, `BrokerError` |
| `cancel_gtt` | `gtt_id: str` | `None` | `UnsupportedFeatureError`, `BrokerError` |
| `get_gtt` | `gtt_id: str` | `Gtt` | `UnsupportedFeatureError`, `BrokerError` |
| `get_gtts` | — | `list[Gtt]` | `UnsupportedFeatureError`, `BrokerError` |

### Instrument helper methods

| Method | Params | Returns | Common errors |
|---|---|---|---|
| `get_futures` | `instrument: Instrument` | `list[Future]` | `ClientNotConnectedError` |
| `get_options` | `instrument: Instrument`, `expiry: date \| None = None` | `list[Option]` | `ClientNotConnectedError` |
| `get_expiries` | `instrument: Instrument` | `list[date]` | `ClientNotConnectedError` |
| `search_instruments` | `query: str`, `exchange: str \| None = None` | `list[Equity]` | `ClientNotConnectedError` |

### Notes

- `TTConnect` runs async internals in a dedicated background event-loop thread.
- Use `AsyncTTConnect` for WebSocket-heavy flows.

---

## InstrumentStore

`InstrumentStore` and `AsyncInstrumentStore` provide **read-only** access to the local instrument cache without authenticating with a broker. Use them for instrument discovery, metadata, or option-chain browsing without placing trades.

!!! note "Seed the DB first"
    The store reads from a local SQLite DB populated by `TTConnect` / `AsyncTTConnect` during `init()`. If the DB has not been seeded, store initialization fails with a clear error.

### Constructors

| Class | Signature | Notes |
|---|---|---|
| Sync | `InstrumentStore(broker: str)` | Opens DB and starts background event loop |
| Async | `AsyncInstrumentStore(broker: str)` | Call `await init()` or use `async with` |

Both support context managers (`with` / `async with`).

### Quick example

=== "Sync"

    ```python
    from tt_connect import InstrumentStore
    from tt_connect.instruments import Index
    from tt_connect.enums import Exchange

    with InstrumentStore(broker_id) as store:
        results = store.search("NIFTY")

        nifty = Index(exchange=Exchange.NSE, symbol="NIFTY")
        expiries = store.get_expiries(nifty)
        info = store.get_instrument_info(nifty)
        print(f"Lot size: {info.lot_size}, Tick size: {info.tick_size}")

        chain = store.get_option_chain(nifty, expiries[0])
        for entry in chain.entries[:5]:
            print(f"  {entry.strike}  CE={entry.ce}  PE={entry.pe}")
    ```

=== "Async"

    ```python
    from tt_connect import AsyncInstrumentStore
    from tt_connect.instruments import Index
    from tt_connect.enums import Exchange

    async with AsyncInstrumentStore(broker_id) as store:
        nifty = Index(exchange=Exchange.NSE, symbol="NIFTY")
        expiries = await store.get_expiries(nifty)
        chain = await store.get_option_chain(nifty, expiries[0])
    ```

### Methods

| Method | Params | Returns | Description |
|---|---|---|---|
| `list_instruments` | `instrument_type=None, exchange=None, underlying=None, expiry=None, option_type=None, strike=None, strike_min=None, strike_max=None, has_derivatives=None, limit=100` | `list[Instrument]` | Filter instruments with any criteria |
| `get_expiries` | `instrument: Instrument` | `list[date]` | Distinct expiry dates for an underlying |
| `search` | `query: str, exchange: str \| None = None` | `list[Equity \| Index]` | Search underlyings by symbol substring |
| `get_instrument_info` | `instrument: Instrument` | `InstrumentInfo` | Metadata: lot size, tick size, segment, name |
| `get_option_chain` | `underlying: Instrument, expiry: date` | `OptionChain` | CE/PE pairs for all strikes |
| `execute` | `sql: str, params: tuple = ()` | `list[tuple]` | Raw SQL against the local DB |
| `close` | — | `None` | Close the DB connection |

### When to use InstrumentStore vs TTConnect

| | `TTConnect` | `InstrumentStore` |
|---|---|---|
| Authenticates | Yes | No |
| Refreshes instruments | Yes (on init) | No |
| Place orders | Yes | No |
| Instrument discovery | Yes | Yes (+ `list_instruments`, `search`, `get_option_chain`) |
| Raw SQL | No | Yes (`execute`) |
| Use case | Trading | Research, strategy tooling, option chain analysis |
