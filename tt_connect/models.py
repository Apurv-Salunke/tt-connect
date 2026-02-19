from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from tt_connect.enums import Side, ProductType, OrderType, OrderStatus
from tt_connect.instruments import Instrument


class Profile(BaseModel):
    model_config = ConfigDict(frozen=True)

    client_id: str
    name: str
    email: str
    phone: str | None = None


class Fund(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: float
    used: float
    total: float


class Holding(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument: Instrument
    qty: int
    avg_price: float
    ltp: float
    pnl: float


class Position(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument: Instrument
    qty: int
    avg_price: float
    ltp: float
    pnl: float
    product: ProductType


class Order(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    instrument: Instrument
    side: Side
    qty: int
    filled_qty: int
    product: ProductType
    order_type: OrderType
    status: OrderStatus
    price: float | None = None
    trigger_price: float | None = None
    avg_price: float | None = None
    timestamp: datetime | None = None


class Tick(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument: Instrument
    ltp: float
    volume: int | None = None
    oi: int | None = None
    bid: float | None = None
    ask: float | None = None
    timestamp: datetime | None = None
