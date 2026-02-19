from tt_connect.exceptions import (
    TTConnectError, AuthenticationError, OrderError,
    InvalidOrderError, BrokerError,
)

ERROR_MAP: dict[str, type[TTConnectError]] = {
    "UDAPI100068": AuthenticationError,
    "UDAPI100010": InvalidOrderError,
}


class UpstoxTransformer:

    @staticmethod
    def parse_error(raw: dict) -> TTConnectError:
        errors = raw.get("errors", [{}])
        code = errors[0].get("errorCode", "") if errors else ""
        message = errors[0].get("message", "Unknown error") if errors else "Unknown error"
        exc_class = ERROR_MAP.get(code, BrokerError)
        return exc_class(message, broker_code=code)
