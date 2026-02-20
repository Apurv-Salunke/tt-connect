from tt_connect.models import Profile, Fund, Holding, Position, Order, Tick
from tt_connect.enums import Side, ProductType, OrderType, OrderStatus
from tt_connect.exceptions import (
    TTConnectError, AuthenticationError, OrderError,
    InvalidOrderError, InsufficientFundsError, BrokerError,
)

# TODO: Add AngelOne specific error codes
ERROR_MAP: dict[str, type[TTConnectError]] = {
    # e.g., "AG8001": AuthenticationError
}

class AngelOneTransformer:

    # --- Outgoing ---

    @staticmethod
    def to_order_params(instrument_token: str, qty: int, side: Side,
                        product: ProductType, order_type: OrderType,
                        price: float | None, trigger_price: float | None) -> dict:
        # TODO: Implement mapping
        return {}

    # --- Incoming ---

    @staticmethod
    def to_profile(raw: dict) -> Profile:
        # TODO: Implement mapping
        pass

    @staticmethod
    def to_fund(raw: dict) -> Fund:
        # TODO: Implement mapping
        pass

    @staticmethod
    def to_order(raw: dict, instrument) -> Order:
        # TODO: Implement mapping
        pass

    # --- Errors ---

    @staticmethod
    def parse_error(raw: dict) -> TTConnectError:
        # TODO: Parse AngelOne-specific error
        pass
