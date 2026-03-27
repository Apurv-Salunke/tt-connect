# Orders

## Core actions

- Place order
- Modify order
- Cancel order
- List orders

## Place order (market)

=== "Sync"

    ```python
    from tt_connect import TTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange, Side, ProductType, OrderType

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        order_id = broker.place_order(
            instrument=Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
            side=Side.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            product=ProductType.CNC,
        )
        print("placed:", order_id)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange, Side, ProductType, OrderType

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        order_id = await broker.place_order(
            instrument=Equity(exchange=Exchange.NSE, symbol="RELIANCE"),
            side=Side.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            product=ProductType.CNC,
        )
        print("placed:", order_id)
    ```

## Place order (limit)

```python
order_id = broker.place_order(
    instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
    side=Side.BUY,
    qty=10,
    order_type=OrderType.LIMIT,
    product=ProductType.CNC,
    price=800.0,
)
```

## Modify and cancel

```python
broker.modify_order(order_id=order_id, price=801.0, qty=10)
broker.cancel_order(order_id)
```

## Read orders

```python
orders = broker.get_orders()
for o in orders:
    print(o.id, o.status, o.qty)
```

## Order lifecycle

`PENDING → OPEN → COMPLETE` or `CANCELLED` or `REJECTED`

## Good patterns

- Save the returned order ID
- Check order status after placement
- Handle rejection — do not retry blindly

## What's next

- [Portfolio](portfolio.md) — check trades, positions, and holdings
- [GTT Orders](gtt.md) — set up automated trigger-based orders
- [Error Handling](error-handling.md) — handle failures in production
