# Recipe: First Order

The shortest safe path to place your first order.

## 1) Create client and check funds

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        funds = broker.get_funds()
        print("Available:", funds.available)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        funds = await broker.get_funds()
        print("Available:", funds.available)
    ```

## 2) Place a small order

```python
from tt_connect.instruments import Equity
from tt_connect.enums import Exchange, Side, ProductType, OrderType

order_id = broker.place_order(
    instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
    side=Side.BUY,
    qty=1,
    order_type=OrderType.MARKET,
    product=ProductType.CNC,
)
print("Order ID:", order_id)
```

## 3) Confirm status

```python
orders = broker.get_orders()
match = next((o for o in orders if o.id == order_id), None)
print(match.status if match else "not found")
```

## Notes

- Use very small quantity for your first run
- If rejected, print full order details and verify product / order type

## What's next

- [Cancel all open orders](cancel-all-open-orders.md) — clean up during testing
- [Stream live ticks](stream-and-store-live-ticks.md) — get live market data
- [Error Handling](../error-handling.md) — handle failures in production
