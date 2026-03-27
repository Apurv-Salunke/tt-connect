# Recipe: Close All Open Positions

This places offsetting market orders for all open positions.

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        placed, failed = broker.close_all_positions()
        print("Placed close orders:", placed)
        print("Failed symbols:", failed)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        placed, failed = await broker.close_all_positions()
        print("Placed close orders:", placed)
        print("Failed symbols:", failed)
    ```

## Important

- This is a high-impact action
- Verify open positions before and after
- Run in controlled environments first

## What's next

- [Cancel all open orders](cancel-all-open-orders.md) — cancel pending orders before closing positions
- [Error Handling](../error-handling.md) — handle partial failures gracefully
