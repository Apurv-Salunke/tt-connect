# Getting Started

## What this package does

`tt-connect` gives one common Python API over multiple Indian broker APIs. Write one trading flow, switch brokers by changing config.

## Who it is for

- Algo trading developers
- Backend services that place orders
- Teams that want broker portability

## Key concepts

| Term | Meaning |
|------|---------|
| **Instrument** | What you trade — stock, future, option, or index |
| **Exchange** | Market venue/segment: `NSE`, `BSE`, `NFO`, `BFO`, `CDS`, `MCX` |
| **Order** | Request to buy/sell an instrument |
| **Trade** | Actual execution fill from an order |
| **Position** | Current net open quantity for an instrument |
| **Holding** | Delivery inventory carried in account |
| **Tick** | Realtime market update from WebSocket |
| **Quote** | REST snapshot of current market values |
| **Candle** | OHLC bar for a time interval |
| **GTT** | Trigger rule that places an order when a price condition is met |
| **Product Type** | How broker treats margin/holding: `CNC`, `MIS`, `NRML` |
| **Order Type** | Execution style: `MARKET`, `LIMIT`, `SL`, `SL_M` |
| **Access Token** | Session token required for authenticated broker API calls |
| **Auth Mode** | How login is done: `manual` (provide token) or `auto` (where supported) |

## Sync vs async — which to use

| Use case | Client | Why |
|---|---|---|
| Scripts, one-shot tasks, Jupyter notebooks | `TTConnect` (sync) | Simpler — no `async`/`await` needed |
| WebSocket streaming, long-running services | `AsyncTTConnect` (async) | Required for `subscribe()` and non-blocking I/O |
| FastAPI, Django async views | `AsyncTTConnect` (async) | Fits naturally into async frameworks |

Both clients expose the same trading and account APIs. Realtime subscription (`subscribe`/`unsubscribe`) is available on the async client only. Start with sync — switch to async when you need streaming or are in an async context.

## First working script

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {
        "api_key": "YOUR_API_KEY",
        "access_token": "YOUR_ACCESS_TOKEN",
    }

    with TTConnect(broker_id, config) as broker:
        profile = broker.get_profile()
        funds = broker.get_funds()

        print(profile.client_id, profile.name)
        print("Available funds:", funds.available)
    ```

=== "Async"

    ```python
    import asyncio
    from tt_connect import AsyncTTConnect

    async def main() -> None:
        config = {
            "api_key": "YOUR_API_KEY",
            "access_token": "YOUR_ACCESS_TOKEN",
        }

        async with AsyncTTConnect(broker_id, config) as broker:
            profile = await broker.get_profile()
            print(profile.client_id, profile.name)

    asyncio.run(main())
    ```

Replace `broker_id` with your broker identifier (e.g. `"zerodha"`, `"angelone"`).

## Learning paths

**Beginner** — place your first order:

1. [Authentication](authentication.md) — configure credentials
2. [Recipe: First order](recipes/first-order.md) — place a live order
3. [Troubleshooting](troubleshooting/auth-failures.md) — if blocked

**Production** — harden for live trading:

1. [Authentication](authentication.md) — auth modes and config
2. [Error Handling](error-handling.md) — safety and retry patterns
3. [Broker Differences](broker-differences.md) — per-broker behavior
4. Risk controls: [Cancel all orders](recipes/cancel-all-open-orders.md), [Close all positions](recipes/close-all-open-positions.md)
5. [WebSocket](websocket.md) — live monitoring

**Data-first** — market data and instruments:

1. [Instruments](instruments.md) — discover what you can trade
2. [Market Data](market-data.md) — quotes, candles, ticks
3. [Recipe: Stream live ticks](recipes/stream-and-store-live-ticks.md)
