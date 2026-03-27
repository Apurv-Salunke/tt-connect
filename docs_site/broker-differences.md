# Broker Differences

The tt-connect API is unified, but brokers differ in capabilities and behavior. This page is the single reference for all per-broker specifics.

## Capability matrix

| Capability | Zerodha | AngelOne |
|---|---|---|
| Auth modes | `manual` | `manual`, `auto` |
| Segments | `NSE`, `BSE`, `NFO`, `BFO`, `CDS` | `NSE`, `BSE`, `NFO`, `CDS`, `MCX` |
| Order types | `MARKET`, `LIMIT`, `SL`, `SL_M` | `MARKET`, `LIMIT`, `SL`, `SL_M` |
| Product types | `CNC`, `MIS`, `NRML` | `CNC`, `MIS`, `NRML` |

## Pre-order validation

These checks run automatically before any network call:

| Check | What is validated |
|---|---|
| Segment | Instrument exchange is supported by broker |
| Order type | Requested order type is allowed |
| Product type | Requested product type is allowed |
| Tradeability | Index instruments are blocked for order placement |

If validation fails, `UnsupportedFeatureError` is raised immediately.

## Operation differences

### Orders

| Operation | Zerodha | AngelOne | Recommendation |
|---|---|---|---|
| `get_order(id)` | Supported | Fetches order book, filters by ID | Use `get_orders()` + filter for portability |
| `get_orders()` | Full order book | Normalized list (empty on null) | Handle empty list safely |
| `cancel_all_orders()` | List + cancel flow | List + cancel flow | Capture both cancelled and failed IDs |
| `tag` kwarg | Sent as `tag` (max 20 chars) | Sent as `uniqueorderid` | Use short tags for compatibility |

### GTT

| Operation | Zerodha | AngelOne | Recommendation |
|---|---|---|---|
| `place_gtt` | 1 or 2 legs | 1 leg only | Keep to single-leg for portability |
| `modify_gtt` | Supported | Supported | Re-fetch rule after modify |
| `cancel_gtt` | Direct cancel | Uses rule details internally | Handle errors, retry only on transient |

### Authentication

| Area | Zerodha | AngelOne | Recommendation |
|---|---|---|---|
| Auth modes | `manual` only | `manual` + `auto` | Check broker support before using `auto` |
| Token lifecycle | External OAuth flow daily | Auto mode supports TOTP login | Use `cache_session` in auto mode |

### Config keys

| Key | Zerodha | AngelOne (manual) | AngelOne (auto) |
|---|---|---|---|
| `api_key` | Required | Required | Required |
| `access_token` | Required | Required | — |
| `auth_mode` | — | `"manual"` | `"auto"` |
| `client_id` | — | — | Required |
| `pin` | — | — | Required |
| `totp_secret` | — | — | Required |
| `on_stale` | Optional | Optional | Optional |
| `cache_session` | Optional | Optional | Optional |

### Market data

| Operation | Zerodha | AngelOne | Recommendation |
|---|---|---|---|
| `get_quotes()` (REST) | Supported | Not supported | Use WebSocket for live quotes across brokers |
| `get_historical()` | Supported | Supported | Same canonical API |
| WebSocket mode | Full mode | Snap-quote mode | Keep tick callbacks tolerant to missing fields |

### WebSocket

| Area | Zerodha | AngelOne | Recommendation |
|---|---|---|---|
| Subscribe mode | Full (OI, depth, timestamps) | Snap-quote (OI, best-5 bid/ask) | Callbacks should handle optional fields |
| Reconnect | Auto + resubscribe | Auto + resubscribe | Keep callbacks idempotent and fast |

## Writing portable code

```python
from tt_connect import TTConnect

def run_strategy(broker_id: str, config: dict) -> None:
    with TTConnect(broker_id, config) as broker:
        profile = broker.get_profile()
        print(broker_id, profile.client_id, profile.name)
```

Test the same strategy on each broker separately. Use `UnsupportedFeatureError` handling for operations that may not be available on all brokers.
