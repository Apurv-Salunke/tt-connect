# Duplicate Order Protection

## Common symptoms

- Same intent appears multiple times in order book
- Retries after timeout create accidental duplicates

## Safety checklist

1. Always store `order_id` from each placement.
2. Pass a `tag` kwarg for request correlation.
3. Before retrying, check recent orders for matching intent.
4. Retry only on clearly transient errors.

## Basic pattern

```python
order_id = broker.place_order(
    instrument=instrument,
    side=side,
    qty=qty,
    order_type=order_type,
    product=product,
    tag="strategyA-20260305-093000-01",
)

# If place call is uncertain, inspect get_orders() before re-sending
```

## Operational controls

- Keep a short-term in-memory dedupe key
- Alert when same symbol + side + qty repeats quickly
- Use manual approval for replays in production

## Related

- [Error Handling](../error-handling.md)
- [Orders](../orders.md)
