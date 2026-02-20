from tt_connect.capabilities import Capabilities
from tt_connect.enums import Exchange, OrderType, ProductType

UPSTOX_CAPABILITIES = Capabilities(
    broker_id="upstox",
    segments=frozenset({Exchange.NSE, Exchange.BSE, Exchange.NFO, Exchange.BFO, Exchange.CDS, Exchange.MCX}),
    order_types=frozenset({OrderType.MARKET, OrderType.LIMIT, OrderType.SL, OrderType.SL_M}),
    product_types=frozenset({ProductType.CNC, ProductType.MIS, ProductType.NRML}),
)
