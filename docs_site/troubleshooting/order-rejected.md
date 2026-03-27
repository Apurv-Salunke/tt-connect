# Order Rejected

## Common symptoms

- Order status becomes `REJECTED`
- `BrokerError`, `InvalidOrderError`, or `InsufficientFundsError`

## Fast checks

1. Check available funds before placing order.
2. Verify product type and order type are supported for your broker and segment.
3. Verify required fields for order type (price for LIMIT, trigger_price for SL).
4. Read latest order book entry for the broker's rejection message.

## Debug pattern

```python
orders = broker.get_orders()
for o in orders[:10]:
    print(o.id, o.status, o.order_type, o.product, o.qty)
```

## Safe recovery

- Do not blindly retry the same payload
- Fix the root cause first (funds, parameters, capability)
- Re-submit only after checks pass

## Related

- [Orders](../orders.md)
- [Error Handling](../error-handling.md)
- [Broker Differences](../broker-differences.md)
