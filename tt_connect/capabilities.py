from dataclasses import dataclass
from tt_connect.enums import Exchange, OrderType, ProductType
from tt_connect.exceptions import UnsupportedFeatureError
from tt_connect.instruments import Instrument, Index


@dataclass(frozen=True)
class Capabilities:
    broker_id: str
    segments: frozenset[Exchange]
    order_types: frozenset[OrderType]
    product_types: frozenset[ProductType]

    def verify(
        self,
        instrument: Instrument,
        order_type: OrderType,
        product_type: ProductType,
    ) -> None:
        if isinstance(instrument, Index):
            raise UnsupportedFeatureError(
                f"Indices are not tradeable. Use Equity, Future, or Option instead."
            )
        if instrument.exchange not in self.segments:
            raise UnsupportedFeatureError(
                f"{self.broker_id} does not support {instrument.exchange} segment"
            )
        if order_type not in self.order_types:
            raise UnsupportedFeatureError(
                f"{self.broker_id} does not support {order_type} order type"
            )
        if product_type not in self.product_types:
            raise UnsupportedFeatureError(
                f"{self.broker_id} does not support {product_type} product type"
            )
