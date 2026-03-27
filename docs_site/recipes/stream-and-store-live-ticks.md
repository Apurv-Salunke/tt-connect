# Recipe: Stream and Store Live Ticks

This example streams ticks and writes simple CSV rows.

```python
import asyncio
from pathlib import Path
from tt_connect import AsyncTTConnect, Tick
from tt_connect.instruments import Equity
from tt_connect.enums import Exchange

OUT = Path("ticks.csv")

async def on_tick(tick: Tick) -> None:
    row = f"{tick.timestamp},{tick.instrument.exchange},{tick.instrument.symbol},{tick.ltp},{tick.volume},{tick.oi}\n"
    with OUT.open("a", encoding="utf-8") as f:
        f.write(row)

async def main() -> None:
    config = {"api_key": "...", "access_token": "..."}
    watch = [
        Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
        Equity(exchange=Exchange.NSE, symbol="SBIN"),
    ]

    async with AsyncTTConnect(broker_id, config) as broker:
        await broker.subscribe(watch, on_tick)
        await asyncio.sleep(30)
        await broker.unsubscribe(watch)

asyncio.run(main())
```

## Practical note

For high tick rates, use an in-memory queue + background writer instead of writing per tick.

## What's next

- [WebSocket](../websocket.md) — full feed health and reconnect guide
