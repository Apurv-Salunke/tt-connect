"""Public package entrypoint for tt-connect clients."""

import logging

from tt_connect.core.client import AsyncTTConnect, TTConnect
from tt_connect.core.logging import setup_logging
from tt_connect.core.models.requests import GttLeg
from tt_connect.core.models.responses import Candle, Gtt, Tick
from tt_connect.core.store.store import AsyncInstrumentStore, InstrumentStore
from tt_connect.exceptions import ConfigurationError
from tt_connect.enums import CandleInterval
from tt_connect.instruments import (
    Equity,
    Future,
    Index,
    Option,
)

# Auto-discover and register all broker packages (adapters + configs)
import tt_connect.brokers  # noqa: F401

# Re-export broker configs for user convenience
from tt_connect.brokers.zerodha.config import ZerodhaConfig
from tt_connect.brokers.angelone.config import AngelOneConfig

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "TTConnect",
    "AsyncTTConnect",
    "AsyncInstrumentStore",
    "InstrumentStore",
    # Config
    "AngelOneConfig",
    "ZerodhaConfig",
    "ConfigurationError",
    # GTT models
    "GttLeg",
    "Gtt",
    # Historical
    "Candle",
    "CandleInterval",
    # Quotes
    "Tick",
    # Instruments
    "Equity",
    "Future",
    "Index",
    "Option",
    # Logging
    "setup_logging",
]
