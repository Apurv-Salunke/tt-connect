# GTT (Trigger Orders)

A GTT (Good Till Triggered) is a rule that places an order when a price condition is met.

## Create a single-leg GTT

=== "Sync"

    ```python
    from tt_connect import TTConnect, GttLeg
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange, Side, ProductType

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        gtt_id = broker.place_gtt(
            instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
            last_price=800.0,
            legs=[
                GttLeg(
                    trigger_price=790.0,
                    price=789.5,
                    side=Side.BUY,
                    qty=1,
                    product=ProductType.CNC,
                )
            ],
        )
        print("GTT ID:", gtt_id)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect, GttLeg
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange, Side, ProductType

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        gtt_id = await broker.place_gtt(
            instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
            last_price=800.0,
            legs=[
                GttLeg(
                    trigger_price=790.0,
                    price=789.5,
                    side=Side.BUY,
                    qty=1,
                    product=ProductType.CNC,
                )
            ],
        )
        print("GTT ID:", gtt_id)
    ```

## Read, modify, and cancel

```python
# Read
gtt = broker.get_gtt("123456")
print(gtt.gtt_id, gtt.status, gtt.symbol)

# Modify
broker.modify_gtt(
    gtt_id="123456",
    instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
    last_price=805.0,
    legs=[
        GttLeg(trigger_price=792.0, price=791.5, side=Side.BUY, qty=1, product=ProductType.CNC)
    ],
)

# Cancel
broker.cancel_gtt("123456")
```

## Practical notes

- Always confirm trigger status after creation
- Keep to single-leg GTTs for maximum broker portability
- See [Broker Differences](broker-differences.md) for per-broker GTT behavior
