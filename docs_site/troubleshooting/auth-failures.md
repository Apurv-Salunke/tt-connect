# Auth Failures

## Common symptoms

- `AuthenticationError`
- Profile/funds call fails right after startup
- Token works in one session but fails in another

## Fast checks

1. Confirm broker ID is correct.
2. Confirm required config keys are present for your broker and auth mode.
3. Confirm token/session is still valid (tokens expire daily per SEBI rules).
4. Confirm auth mode is supported by your broker.

## Minimal test

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        print(broker.get_profile())
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        print(await broker.get_profile())
    ```

## What to do next

- Refresh or recreate your access token
- Verify system clock and TOTP secret for auto login
- Disable cached session (`cache_session: False`) and retry
- Check [Broker Differences](../broker-differences.md) for per-broker auth details

## Related

- [Authentication](../authentication.md)
- [Exceptions](../reference/exceptions.md)
