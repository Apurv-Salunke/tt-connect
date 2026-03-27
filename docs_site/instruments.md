# Instruments

## Supported types

- **Equity** — cash market stock
- **Future** — derivative keyed by expiry
- **Option** — derivative keyed by expiry + strike + CE/PE
- **Index** — for market data and underlying reference (not tradeable for orders)

## Create instrument objects

```python
from datetime import date
from tt_connect.instruments import Equity, Future, Option, Index
from tt_connect.enums import Exchange, OptionType

reliance = Equity(exchange=Exchange.NSE, symbol="RELIANCE")
nifty_index = Index(exchange=Exchange.NSE, symbol="NIFTY")

nifty_fut = Future(
    exchange=Exchange.NSE,
    symbol="NIFTY",
    expiry=date(2026, 3, 26),
)

nifty_ce = Option(
    exchange=Exchange.NSE,
    symbol="NIFTY",
    expiry=date(2026, 3, 26),
    strike=22000.0,
    option_type=OptionType.CE,
)
```

## Search instruments

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        results = broker.search_instruments("RELIANCE", exchange="NSE")
        for i in results:
            print(i.exchange, i.symbol)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect

    async with AsyncTTConnect(broker_id, config) as broker:
        results = await broker.search_instruments("RELIANCE", exchange="NSE")
        for i in results:
            print(i.exchange, i.symbol)
    ```

## Discover futures, options, and expiries

=== "Sync"

    ```python
    from tt_connect import TTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange

    config = {"api_key": "...", "access_token": "..."}
    underlying = Equity(exchange=Exchange.NSE, symbol="SBIN")

    with TTConnect(broker_id, config) as broker:
        expiries = broker.get_expiries(underlying)
        print("Expiries:", expiries)

        futures = broker.get_futures(underlying)
        print("Futures count:", len(futures))

        if expiries:
            chain = broker.get_options(underlying, expiry=expiries[0])
            print("Options for first expiry:", len(chain))
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange

    config = {"api_key": "...", "access_token": "..."}
    underlying = Equity(exchange=Exchange.NSE, symbol="SBIN")

    async with AsyncTTConnect(broker_id, config) as broker:
        expiries = await broker.get_expiries(underlying)
        futures = await broker.get_futures(underlying)
        if expiries:
            chain = await broker.get_options(underlying, expiry=expiries[0])
    ```

## Tips

- Always use the correct exchange + symbol combination
- Use helper APIs to discover futures/options/expiries rather than guessing
- Index instruments cannot be used for order placement
- The package maps canonical instruments to broker-specific tokens automatically
