"""Stable public façade for exception types.

Import exceptions from here rather than from ``tt_connect.core``::

    from tt_connect.exceptions import TTConnectError, InstrumentNotFoundError
    from tt_connect.exceptions import AuthenticationError, BrokerError

``tt_connect.core`` is an internal module whose layout may change between
releases. This module is the stable, supported import path.
"""

from tt_connect.core.exceptions import (
    AuthenticationError,
    BrokerError,
    ClientClosedError,
    ClientNotConnectedError,
    ConfigurationError,
    InstrumentNotFoundError,
    InstrumentStoreNotInitializedError,
    InsufficientFundsError,
    InvalidOrderError,
    OrderError,
    OrderNotFoundError,
    RateLimitError,
    TTConnectError,
    UnsupportedFeatureError,
)

__all__ = [
    "AuthenticationError",
    "BrokerError",
    "ClientClosedError",
    "ClientNotConnectedError",
    "ConfigurationError",
    "InstrumentNotFoundError",
    "InstrumentStoreNotInitializedError",
    "InsufficientFundsError",
    "InvalidOrderError",
    "OrderError",
    "OrderNotFoundError",
    "RateLimitError",
    "TTConnectError",
    "UnsupportedFeatureError",
]

# Correct __module__ so repr, tracebacks, and IDE tooltips show the public
# import path rather than the internal definition site.
for _e in [
    AuthenticationError, BrokerError, ClientClosedError, ClientNotConnectedError,
    ConfigurationError, InstrumentNotFoundError, InstrumentStoreNotInitializedError, InsufficientFundsError,
    InvalidOrderError, OrderError, OrderNotFoundError,
    RateLimitError, TTConnectError, UnsupportedFeatureError,
]:
    _e.__module__ = __name__
del _e
