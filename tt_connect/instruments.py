from __future__ import annotations
from datetime import date
from pydantic import BaseModel, model_validator
from tt_connect.enums import Exchange, OptionType


class Instrument(BaseModel, frozen=True):
    exchange: Exchange
    symbol: str


class Equity(Instrument):
    exchange: Exchange


class Future(Instrument):
    expiry: date

    @model_validator(mode="after")
    def _validate(self) -> Future:
        # Validated against instrument DB after TTConnect is initialized
        return self


class Option(Instrument):
    expiry: date
    strike: float
    option_type: OptionType

    @model_validator(mode="after")
    def _validate(self) -> Option:
        # Validated against instrument DB after TTConnect is initialized
        return self


class Currency(Instrument):
    exchange: Exchange


class Commodity(Instrument):
    exchange: Exchange
