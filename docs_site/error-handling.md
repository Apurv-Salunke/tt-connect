# Error Handling

## Exception types

```python
from tt_connect.exceptions import (
    TTConnectError,          # base library error
    AuthenticationError,     # invalid/expired auth
    ConfigurationError,      # missing/invalid config
    RateLimitError,          # broker rate limit exceeded
    UnsupportedFeatureError, # broker does not support this operation
    InsufficientFundsError,  # not enough funds/margin
    BrokerError,             # generic broker-side failure
    InvalidOrderError,       # order payload invalid
    OrderNotFoundError,      # order ID not found
    InstrumentNotFoundError, # instrument not in local master
)
```

## Handling pattern

Catch specific errors first, use `TTConnectError` as fallback:

```python
try:
    order_id = broker.place_order(
        instrument=instrument, side=side, qty=1,
        order_type=order_type, product=product,
    )
except InsufficientFundsError:
    # do not retry — change size/funds first
    raise
except UnsupportedFeatureError:
    # do not retry — broker does not support this
    raise
except RateLimitError:
    # retry with backoff
    raise
except AuthenticationError:
    # refresh token / re-login
    raise
except BrokerError:
    # broker rejected — inspect message
    raise
except TTConnectError:
    # generic library error fallback
    raise
```

## Retry guidance

**Retry with backoff:**

- Timeout / network transient failures
- `RateLimitError`

**Do not retry:**

- `InsufficientFundsError` — fix funds first
- `UnsupportedFeatureError` — broker doesn't support it
- `ConfigurationError` — fix config
- `InvalidOrderError` — fix order parameters

## Idempotency tags

Pass a `tag` kwarg to `place_order` for request correlation. Before retrying, check recent orders for a matching tag to avoid duplicates:

```python
order_id = broker.place_order(
    instrument=instrument,
    side=side,
    qty=qty,
    order_type=order_type,
    product=product,
    tag="strategyA-20260305-093000-01",
)
```

## Pre-order safety checks

=== "Sync"

    ```python
    from tt_connect import TTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange, Side, ProductType, OrderType

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        funds = broker.get_funds()
        if funds.available < 1000:
            raise RuntimeError("Not enough funds")

        order_id = broker.place_order(
            instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
            side=Side.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            product=ProductType.CNC,
        )
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange, Side, ProductType, OrderType

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        funds = await broker.get_funds()
        if funds.available < 1000:
            raise RuntimeError("Not enough funds")

        order_id = await broker.place_order(
            instrument=Equity(exchange=Exchange.NSE, symbol="SBIN"),
            side=Side.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            product=ProductType.CNC,
        )
    ```

## Production checklist

- Retry policy configured for transient errors
- Alerts for auth / placement failures
- Graceful shutdown closes the client
- Risk-off path tested (`cancel_all_orders`, `close_all_positions`)
- Credentials in environment variables or secret manager
- Sufficient logging for audit / replay
