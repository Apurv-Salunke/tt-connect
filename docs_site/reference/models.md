# Models & Enums

## Instrument models

| Model | Required fields | Notes |
|---|---|---|
| `Instrument` | `exchange`, `symbol` | Base canonical instrument |
| `Index` | `exchange`, `symbol` | Not tradeable for order placement |
| `Equity` | `exchange`, `symbol` | Cash market instrument |
| `Future` | `exchange`, `symbol`, `expiry` | Derivative keyed by expiry |
| `Option` | `exchange`, `symbol`, `expiry`, `strike`, `option_type` | Derivative keyed by strike + CE/PE |
| `Currency` | `exchange`, `symbol` | Currency derivative |
| `Commodity` | `exchange`, `symbol` | Commodity derivative |

## GTT leg model

Order and GTT methods take keyword arguments directly — no request objects. The one exception is `GttLeg`:

| Model | Required fields | Notes |
|---|---|---|
| `GttLeg` | `trigger_price`, `price`, `side`, `qty`, `product` | One entry per GTT leg |

```python
from tt_connect import GttLeg
from tt_connect.enums import Side, ProductType

leg = GttLeg(trigger_price=790.0, price=789.5, side=Side.BUY, qty=1, product=ProductType.CNC)
```

## Response models

| Model | Required fields | Optional/default fields |
|---|---|---|
| `Profile` | `client_id`, `name`, `email` | `phone=None` |
| `Fund` | `available`, `used`, `total` | `collateral=0.0`, `m2m_unrealized=0.0`, `m2m_realized=0.0` |
| `Holding` | `instrument`, `qty`, `avg_price`, `ltp`, `pnl` | `pnl_percent=0.0` |
| `Position` | `instrument`, `qty`, `avg_price`, `ltp`, `pnl`, `product` | — |
| `Order` | `id`, `side`, `qty`, `filled_qty`, `product`, `order_type`, `status` | `instrument=None`, `price=None`, `trigger_price=None`, `avg_price=None`, `timestamp=None` |
| `Trade` | `order_id`, `instrument`, `side`, `qty`, `avg_price`, `trade_value`, `product` | `timestamp=None` |
| `Tick` | `instrument`, `ltp` | `volume=None`, `oi=None`, `bid=None`, `ask=None`, `timestamp=None` |
| `Candle` | `instrument`, `timestamp`, `open`, `high`, `low`, `close`, `volume` | `oi=None` |
| `Gtt` | `gtt_id`, `status`, `symbol`, `exchange`, `legs` | — |
| `Margin` | `total`, `span`, `exposure`, `final_total`, `benefit` | `option_premium=0.0` |

## Mutability

| Model class | Mutability |
|---|---|
| `GttLeg` | Mutable |
| All response models | Frozen / read-only |

## Public enums

Import from `tt_connect.enums`:

| Enum | Values | Typical usage |
|---|---|---|
| `Exchange` | `NSE`, `BSE`, `NFO`, `BFO`, `CDS`, `MCX` | Instrument exchange/segment |
| `OptionType` | `CE`, `PE` | Option side |
| `ProductType` | `CNC`, `MIS`, `NRML` | Order product/margin type |
| `OrderType` | `MARKET`, `LIMIT`, `SL`, `SL_M` | Order execution style |
| `Side` | `BUY`, `SELL` | Order direction |
| `OrderStatus` | `PENDING`, `OPEN`, `COMPLETE`, `CANCELLED`, `REJECTED` | Normalized order state |
| `FeedState` | `connecting`, `connected`, `reconnecting`, `stale`, `closed` | WebSocket feed health |
| `CandleInterval` | `1minute`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `60minute`, `day` | Historical candle interval |

## Internal enums

These are used by config dicts and client internals — do not import in user code:

| Enum | Used where |
|---|---|
| `OnStale` | `on_stale` config key (`"fail"` or `"warn"`) |
| `AuthMode` | `auth_mode` config key (`"manual"` or `"auto"`) |
| `ClientState` | Internal client lifecycle tracking |
