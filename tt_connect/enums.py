"""Stable public façade for canonical enum types.

Import enums from here rather than from ``tt_connect.core``::

    from tt_connect.enums import Exchange, Side, OrderType, ProductType, OptionType

``tt_connect.core`` is an internal module whose layout may change between
releases. This module is the stable, supported import path.
"""

from tt_connect.core.models.enums import (
    CandleInterval,
    Exchange,
    OptionType,
    OrderStatus,
    OrderType,
    ProductType,
    Side,
)

__all__ = [
    "CandleInterval",
    "Exchange",
    "OptionType",
    "OrderStatus",
    "OrderType",
    "ProductType",
    "Side",
]

# Correct __module__ so repr, tracebacks, and IDE tooltips show the public
# import path rather than the internal definition site.
for _e in [CandleInterval, Exchange, OptionType, OrderStatus, OrderType, ProductType, Side]:
    _e.__module__ = __name__
del _e
