# WebSocket Disconnect/Reconnect

## Expected behavior

- WebSocket reconnect is automatic with exponential backoff (cap: 60 seconds)
- All subscriptions are restored after every reconnect
- `on_stale` / `on_recovered` callbacks continue to fire correctly across reconnects

## Common symptoms

- Ticks stop suddenly
- Short data gaps during reconnect
- `on_stale` fires but `on_recovered` never fires

## Detecting a stale feed

The library detects feed silence automatically. Use `on_stale` and `on_recovered` callbacks:

```python
async def on_stale() -> None:
    print("No tick for 30s — feed is stale")
    # halt algo, alert, etc.

async def on_recovered() -> None:
    print("Feed recovered")

await broker.subscribe(watch, on_tick, on_stale=on_stale, on_recovered=on_recovered)
```

Or poll `broker.feed_state` directly:

```python
from tt_connect.enums import FeedState

while True:
    if broker.feed_state == FeedState.STALE:
        print("Feed stale — waiting")
    elif broker.feed_state == FeedState.CONNECTED:
        pass  # healthy
    await asyncio.sleep(5)
```

## Per-instrument staleness

```python
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
ts = broker.last_tick_at(reliance)
if ts:
    age = (datetime.now(IST) - ts).total_seconds()
    if age > 60:
        print(f"No RELIANCE tick for {age:.0f}s")
```

## When `on_stale` fires but `on_recovered` never fires

- **Market is closed** — no ticks are sent outside exchange hours; this is expected
- **Subscribed to wrong instrument** — verify the symbol resolves to an actively traded contract
- **Connection is permanently dropped** — check `broker.feed_state` for `RECONNECTING`; if stuck, the broker endpoint may be down

## Callback exceptions hide errors

If your `on_tick` raises, the stream continues but the exception is only logged. Always wrap business logic:

```python
async def on_tick(tick):
    try:
        process(tick)
    except Exception as e:
        logger.error("tick processing failed", exc_info=e)
```

## Related

- [Realtime (WebSocket)](../realtime-websocket.md)
- [Recipe: Recover from reconnect](../recipes/recover-from-reconnect.md)
- [Broker operation notes](../reference/operation-notes.md)
