"""Stable public façade for instrument and discovery types.

Import instrument classes from here rather than from ``tt_connect.core``::

    from tt_connect.instruments import Equity, Option, Index, Future
    from tt_connect.instruments import OptionChain, OptionChainEntry, InstrumentInfo

``tt_connect.core`` is an internal module whose layout may change between
releases. This module is the stable, supported import path.
"""

from tt_connect.core.models.instruments import (
    Commodity,
    Currency,
    Equity,
    Future,
    Index,
    Instrument,
    InstrumentInfo,
    Option,
    OptionChain,
    OptionChainEntry,
)

__all__ = [
    "Commodity",
    "Currency",
    "Equity",
    "Future",
    "Index",
    "Instrument",
    "InstrumentInfo",
    "Option",
    "OptionChain",
    "OptionChainEntry",
]

# Correct __module__ so repr, tracebacks, and IDE tooltips show the public
# import path rather than the internal definition site.
for _t in [
    Commodity, Currency, Equity, Future, Index, Instrument,
    InstrumentInfo, Option, OptionChain, OptionChainEntry,
]:
    _t.__module__ = __name__
del _t
