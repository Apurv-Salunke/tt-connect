# Market Data

## Data types

| Type | Source | Use case |
|------|--------|----------|
| **Quotes** | REST snapshot | Current price check |
| **Ticks** | WebSocket stream | Live monitoring |
| **Candles** | Historical API | Backtesting, charting |

??? note "Broker-specific"
    REST quotes (`get_quotes`) may not be available on all brokers. Use WebSocket streaming for guaranteed live data across brokers. Historical candles (`get_historical`) work on all brokers.

## Get quotes

=== "Sync"

    ```python
    from tt_connect import TTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        instruments = [
            Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
            Equity(exchange=Exchange.NSE, symbol="SBIN"),
        ]
        quotes = broker.get_quotes(instruments)
        for q in quotes:
            print(q.instrument.symbol, q.ltp, q.volume)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        instruments = [
            Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
            Equity(exchange=Exchange.NSE, symbol="SBIN"),
        ]
        quotes = await broker.get_quotes(instruments)
        for q in quotes:
            print(q.instrument.symbol, q.ltp, q.volume)
    ```

## Get historical candles

=== "Sync"

    ```python
    from datetime import datetime, timedelta
    from tt_connect.enums import CandleInterval

    end = datetime.now()
    start = end - timedelta(days=5)

    candles = broker.get_historical(
        instrument=Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
        interval=CandleInterval.MINUTE_5,
        from_date=start,
        to_date=end,
    )

    for c in candles[:3]:
        print(c.timestamp, c.open, c.high, c.low, c.close, c.volume)
    ```

=== "Async"

    ```python
    from datetime import datetime, timedelta
    from tt_connect.enums import CandleInterval

    end = datetime.now()
    start = end - timedelta(days=5)

    candles = await broker.get_historical(
        instrument=Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
        interval=CandleInterval.MINUTE_5,
        from_date=start,
        to_date=end,
    )
    ```

## Tick fields

| Field | Always present | Notes |
|-------|---------------|-------|
| `ltp` | Yes | Last traded price |
| `volume` | Optional | May be `None` |
| `oi` | Optional | Open interest |
| `bid` / `ask` | Optional | Best bid/ask |
| `timestamp` | Optional | Broker-provided time |

Field availability varies by broker and segment. Write tick callbacks that handle `None` values.

## What's next

- [WebSocket](websocket.md) — stream live ticks with feed health callbacks
- [Recipe: Stream live ticks](recipes/stream-and-store-live-ticks.md) — save ticks to CSV
