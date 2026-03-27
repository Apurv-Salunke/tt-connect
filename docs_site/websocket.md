# WebSocket

Live market data streaming is available via `AsyncTTConnect`.

## Subscribe to ticks

```python
import asyncio
from tt_connect import AsyncTTConnect, Tick
from tt_connect.instruments import Equity
from tt_connect.enums import Exchange

async def on_tick(tick: Tick) -> None:
    print(tick.instrument.symbol, tick.ltp, tick.timestamp)

async def main() -> None:
    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        watch = [
            Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
            Equity(exchange=Exchange.NSE, symbol="SBIN"),
        ]
        await broker.subscribe(watch, on_tick)
        await asyncio.sleep(30)
        await broker.unsubscribe(watch)

asyncio.run(main())
```

## Feed health callbacks

`subscribe` accepts two optional callbacks for when the feed goes silent or recovers:

```python
async def on_stale() -> None:
    print("No tick for 30s — feed is stale")

async def on_recovered() -> None:
    print("Feed recovered — resuming")

await broker.subscribe(
    watch,
    on_tick,
    on_stale=on_stale,
    on_recovered=on_recovered,
)
```

`on_stale` fires once when the feed crosses the **30-second silence threshold**.
`on_recovered` fires on the first tick after a stale period. Both work identically across all brokers and survive reconnects.

## Feed state

Check `broker.feed_state` at any point to read the current stream health:

```python
from tt_connect.enums import FeedState

if broker.feed_state == FeedState.STALE:
    print("No data — market may be closed or connection degraded")

if broker.feed_state == FeedState.CONNECTED:
    print("Stream is healthy")
```

| State | Meaning |
|---|---|
| `CONNECTING` | Initial state before first connect |
| `CONNECTED` | Ticks are flowing normally |
| `STALE` | Connected but no tick for 30+ seconds |
| `RECONNECTING` | Connection lost — reconnect in progress |
| `CLOSED` | Client closed or `unsubscribe` called |

## Per-instrument last tick time

```python
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
ts = broker.last_tick_at(reliance)
if ts:
    age = (datetime.now(IST) - ts).total_seconds()
    if age > 60:
        print(f"RELIANCE tick is {age:.0f}s old")
```

Returns `None` if no tick has been received yet for that instrument.

## Reconnect behavior

- Reconnect is automatic with exponential backoff (cap: 60 seconds)
- All subscriptions are restored after every reconnect
- `on_stale` / `on_recovered` continue to fire across reconnects
- You do **not** need to re-subscribe after a disconnect

## Handling disconnects in your algo

Use `on_stale` and `on_recovered` to pause and resume:

```python
algo_active = True

async def on_tick(tick: Tick) -> None:
    if not algo_active:
        return
    process(tick)

async def on_stale() -> None:
    global algo_active
    algo_active = False
    print("Feed stale — algo paused")

async def on_recovered() -> None:
    global algo_active
    algo_active = True
    print("Feed recovered — algo resumed")
```

### When `on_stale` fires but `on_recovered` never fires

- **Market is closed** — no ticks outside exchange hours; this is expected
- **Wrong instrument** — verify the symbol resolves to an actively traded contract
- **Permanent disconnect** — check `broker.feed_state`; if stuck on `RECONNECTING`, the broker endpoint may be down

## Troubleshooting callback exceptions

If `on_tick` raises, the stream continues but the error is only logged. Always wrap business logic:

```python
async def on_tick(tick: Tick) -> None:
    try:
        process(tick)
    except Exception as e:
        logger.error("tick processing failed", exc_info=e)
```

## Tips

- Do not assume tick ordering is preserved across reconnect boundaries
- If your strategy holds state per tick (e.g. running VWAP), resync in `on_recovered`
- Keep callbacks fast and non-blocking — push heavy work to a queue
- `broker.last_tick_at(instrument)` gives exact IST wall-clock time of the last tick
