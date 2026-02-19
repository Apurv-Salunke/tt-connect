from tt_connect.models import Profile, Fund, Holding, Position, Order, Tick
from tt_connect.enums import Side, ProductType, OrderType, OrderStatus
from tt_connect.exceptions import (
    TTConnectError, AuthenticationError, OrderError,
    InvalidOrderError, InsufficientFundsError, BrokerError,
)

ERROR_MAP: dict[str, type[TTConnectError]] = {
    "TokenException":      AuthenticationError,
    "PermissionException": AuthenticationError,
    "OrderException":      OrderError,
    "InputException":      InvalidOrderError,
    "NetworkException":    BrokerError,
}


class ZerodhaTransformer:

    # --- Outgoing ---

    @staticmethod
    def to_order_params(instrument_token: str, qty: int, side: Side,
                        product: ProductType, order_type: OrderType,
                        price: float | None, trigger_price: float | None) -> dict:
        params = {
            "tradingsymbol": instrument_token,
            "transaction_type": side.value,
            "quantity": qty,
            "product": product.value,
            "order_type": order_type.value,
        }
        if price:
            params["price"] = price
        if trigger_price:
            params["trigger_price"] = trigger_price
        return params

    # --- Incoming ---

    @staticmethod
    def to_profile(raw: dict) -> Profile:
        return Profile(
            client_id=raw["user_id"],
            name=raw["user_name"],
            email=raw["email"],
            phone=raw.get("mobile"),
        )

    @staticmethod
    def to_fund(raw: dict) -> Fund:
        equity = raw["equity"]
        return Fund(
            available=equity["available"]["live_balance"],
            used=equity["utilised"]["debits"],
            total=equity["net"],
        )

    @staticmethod
    def to_order(raw: dict, instrument) -> Order:
        return Order(
            id=raw["order_id"],
            instrument=instrument,
            side=Side(raw["transaction_type"]),
            qty=raw["quantity"],
            filled_qty=raw["filled_quantity"],
            product=ProductType(raw["product"]),
            order_type=OrderType(raw["order_type"]),
            status=OrderStatus(raw["status"]),
            price=raw.get("price"),
            trigger_price=raw.get("trigger_price"),
            avg_price=raw.get("average_price"),
        )

    # --- Errors ---

    @staticmethod
    def parse_error(raw: dict) -> TTConnectError:
        code = raw.get("error_type", "")
        message = raw.get("message", "Unknown error")
        exc_class = ERROR_MAP.get(code, BrokerError)
        return exc_class(message, broker_code=code)
