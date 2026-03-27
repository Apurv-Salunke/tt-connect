# Instrument Not Found

## Common symptoms

- `InstrumentNotFoundError`
- Order or quote call fails for a specific symbol + expiry + strike

## Fast checks

1. Verify exchange is correct (`NSE`, `BSE`, etc.).
2. Verify symbol spelling exactly.
3. For derivatives, verify expiry / strike / CE-PE exactly.
4. Use search and helper APIs before placing an order.

## Debug pattern

=== "Sync"

    ```python
    from tt_connect import TTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        print(broker.search_instruments("SBIN", exchange="NSE"))
        underlying = Equity(exchange=Exchange.NSE, symbol="SBIN")
        print(broker.get_expiries(underlying))
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect
    from tt_connect.instruments import Equity
    from tt_connect.enums import Exchange

    config = {"api_key": "...", "access_token": "..."}

    async with AsyncTTConnect(broker_id, config) as broker:
        print(await broker.search_instruments("SBIN", exchange="NSE"))
        underlying = Equity(exchange=Exchange.NSE, symbol="SBIN")
        print(await broker.get_expiries(underlying))
    ```

## Common root causes

- Wrong exchange
- Stale or invalid derivative contract values
- Typo in symbol

## Related

- [Instruments](../instruments.md)
- [Client API](../reference/clients.md)
