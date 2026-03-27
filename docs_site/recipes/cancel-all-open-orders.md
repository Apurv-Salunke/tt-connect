# Recipe: Cancel All Open Orders

Use this during risk-off or session cleanup.

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        cancelled, failed = broker.cancel_all_orders()
        print("Cancelled:", cancelled)
        print("Failed:", failed)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        cancelled, failed = await broker.cancel_all_orders()
        print("Cancelled:", cancelled)
        print("Failed:", failed)
    ```

## Suggested checks

- Run once and record counts
- If any failed, fetch `get_orders()` and inspect status/reason

## What's next

- [Close all open positions](close-all-open-positions.md) — exit all positions after cancelling orders
- [Error Handling](../error-handling.md) — production checklist
