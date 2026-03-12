"""Public import surface smoke tests."""

from __future__ import annotations

import importlib


def test_public_modules_import() -> None:
    assert importlib.import_module("tt_connect.instruments")
    assert importlib.import_module("tt_connect.enums")
    assert importlib.import_module("tt_connect.exceptions")


def test_documented_symbol_imports() -> None:
    from tt_connect import AsyncInstrumentStore, AsyncTTConnect, InstrumentStore, TTConnect, setup_logging
    from tt_connect.enums import Exchange, OptionType, OrderType, ProductType, Side
    from tt_connect.exceptions import ConfigurationError, TTConnectError
    from tt_connect.instruments import Equity, Future, Index, Option

    assert TTConnect
    assert AsyncTTConnect
    assert InstrumentStore
    assert AsyncInstrumentStore
    assert setup_logging
    assert Equity
    assert Future
    assert Option
    assert Index
    assert Exchange
    assert Side
    assert ProductType
    assert OrderType
    assert OptionType
    assert TTConnectError
    assert ConfigurationError
