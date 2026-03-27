# Portfolio

## Overview

| API | Returns | Use case |
|-----|---------|----------|
| `get_positions()` | Open trading exposure | Intraday P&L, risk monitoring |
| `get_holdings()` | Delivery inventory | Long-term portfolio reporting |
| `get_funds()` | Account balances | Pre-order fund checks |
| `get_trades()` | Execution fills | Reconciliation, audit trail |

## Positions

Positions represent current net open quantity for an instrument.

- Positive qty = long
- Negative qty = short
- Zero qty = flat/closed

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {"api_key": "...", "access_token": "..."}

    with TTConnect(broker_id, config) as broker:
        for p in broker.get_positions():
            print(p.instrument.symbol, "qty=", p.qty, "pnl=", p.pnl)
    ```

=== "Async"

    ```python
    from tt_connect import AsyncTTConnect

    async with AsyncTTConnect(broker_id, config) as broker:
        for p in await broker.get_positions():
            print(p.instrument.symbol, "qty=", p.qty, "pnl=", p.pnl)
    ```

### Close all positions

=== "Sync"

    ```python
    with TTConnect(broker_id, config) as broker:
        placed, failed = broker.close_all_positions()
        print("Close orders:", placed)
        print("Failed:", failed)
    ```

=== "Async"

    ```python
    async with AsyncTTConnect(broker_id, config) as broker:
        placed, failed = await broker.close_all_positions()
    ```

!!! warning
    `close_all_positions()` sends market orders. Always verify product/segment limits and confirm positions are flat afterward.

## Holdings

Holdings are delivery inventory — stocks carried in your demat account.

=== "Sync"

    ```python
    with TTConnect(broker_id, config) as broker:
        for h in broker.get_holdings():
            print(h.instrument.symbol, "qty=", h.qty, "pnl=", h.pnl)
    ```

=== "Async"

    ```python
    async with AsyncTTConnect(broker_id, config) as broker:
        for h in await broker.get_holdings():
            print(h.instrument.symbol, "qty=", h.qty, "pnl=", h.pnl)
    ```

## Funds

=== "Sync"

    ```python
    with TTConnect(broker_id, config) as broker:
        f = broker.get_funds()
        print("Available:", f.available, "Used:", f.used, "Total:", f.total)
    ```

=== "Async"

    ```python
    async with AsyncTTConnect(broker_id, config) as broker:
        f = await broker.get_funds()
        print("Available:", f.available)
    ```

## Trades

A trade is an executed fill of an order. One order can generate multiple trades (partial fills).

=== "Sync"

    ```python
    with TTConnect(broker_id, config) as broker:
        for t in broker.get_trades():
            print(t.order_id, t.instrument.symbol, t.side, "qty=", t.qty, "avg=", t.avg_price)
    ```

=== "Async"

    ```python
    async with AsyncTTConnect(broker_id, config) as broker:
        for t in await broker.get_trades():
            print(t.order_id, t.instrument.symbol, t.side, "qty=", t.qty)
    ```

## Tips

- Values change during market hours — fetch fresh data before acting
- Use fund checks before placing orders
- Use trades for reconciliation — match `trade.order_id` back to orders
- Field names are normalized across brokers, but broker math may differ slightly
