"""
Zerodha instrument CSV parser.

Owns all parsing and classification logic for Zerodha's master dump.
Returns a ParsedInstruments container that the InstrumentManager can
insert without knowing anything about Zerodha's CSV format.

Processing order matches insert order (FK constraint):
  1. indices  — underlyings must exist before futures/options reference them
  2. equities — stocks on NSE/BSE (instrument_type=EQ)
  3. futures  — (future chunk)
  4. options  — (future chunk)
"""

import csv
import io
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Canonical parsed types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParsedIndex:
    exchange: str
    symbol: str         # canonical — what users write in their code
    broker_symbol: str  # Zerodha's tradingsymbol
    segment: str
    name: str | None
    lot_size: int
    tick_size: float
    broker_token: str


@dataclass(frozen=True)
class ParsedEquity:
    exchange: str
    symbol: str         # canonical — same as broker_symbol for equities
    broker_symbol: str  # Zerodha's tradingsymbol
    segment: str
    name: str | None
    lot_size: int
    tick_size: float
    broker_token: str


@dataclass
class ParsedInstruments:
    indices: list[ParsedIndex] = field(default_factory=list)
    equities: list[ParsedEquity] = field(default_factory=list)
    # futures, options added in subsequent chunks


# ---------------------------------------------------------------------------
# Exchange/segment filters
# ---------------------------------------------------------------------------

# Exchanges in scope for v1
_EQUITY_EXCHANGES = {"NSE", "BSE"}

# Segments we classify as indices (within in-scope exchanges)
_INDEX_SEGMENTS = {"INDICES"}

# Instrument types we classify as equities
_EQUITY_INSTRUMENT_TYPES = {"EQ"}

# ---------------------------------------------------------------------------
# Index name map
#
# Zerodha's F&O rows carry a `name` field that identifies the underlying index.
# These names do NOT always match the tradingsymbol stored in the INDICES segment.
# This map translates F&O `name` → (exchange, tradingsymbol) for DB lookup.
#
# Only the 7 indices with active F&O contracts are mapped here.
# ---------------------------------------------------------------------------

INDEX_NAME_MAP: dict[str, tuple[str, str]] = {
    "NIFTY":      ("NSE", "NIFTY 50"),
    "BANKNIFTY":  ("NSE", "NIFTY BANK"),
    "MIDCPNIFTY": ("NSE", "NIFTY MID SELECT"),
    "FINNIFTY":   ("NSE", "NIFTY FIN SERVICE"),
    "NIFTY500":   ("NSE", "NIFTY 500"),
    "SENSEX":     ("BSE", "SENSEX"),
    "BANKEX":     ("BSE", "BANKEX"),
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse(raw_csv: str) -> ParsedInstruments:
    """
    Parse Zerodha's raw CSV instrument dump into a ParsedInstruments container.
    Rows outside v1 scope are silently skipped.
    """
    result = ParsedInstruments()
    reader = csv.DictReader(io.StringIO(raw_csv))

    for row in reader:
        exchange      = row["exchange"]
        segment       = row["segment"]
        instrument_type = row["instrument_type"]

        # Skip exchanges outside v1 scope
        if exchange not in _EQUITY_EXCHANGES:
            continue

        if segment in _INDEX_SEGMENTS:
            result.indices.append(_parse_index(row))
            continue

        if instrument_type in _EQUITY_INSTRUMENT_TYPES:
            result.equities.append(_parse_equity(row))
            continue

        # futures, options — future chunks, skip for now

    return result


# ---------------------------------------------------------------------------
# Per-type parsers
# ---------------------------------------------------------------------------

# Reverse of INDEX_NAME_MAP: Zerodha tradingsymbol → canonical symbol
# e.g. "NIFTY 50" → "NIFTY", "NIFTY BANK" → "BANKNIFTY"
_BROKER_TO_CANONICAL: dict[str, str] = {v[1]: k for k, v in INDEX_NAME_MAP.items()}


def _parse_index(row: dict) -> ParsedIndex:
    broker_symbol = row["tradingsymbol"]

    # For indices not in the map, canonical == broker symbol
    canonical_symbol = _BROKER_TO_CANONICAL.get(broker_symbol, broker_symbol)

    return ParsedIndex(
        exchange      = row["exchange"],
        symbol        = canonical_symbol,
        broker_symbol = broker_symbol,
        segment       = row["segment"],
        name          = row["name"] or None,
        lot_size      = int(row["lot_size"]),
        tick_size     = float(row["tick_size"]),
        broker_token  = row["instrument_token"],
    )


def _parse_equity(row: dict) -> ParsedEquity:
    # For equities, canonical symbol == broker symbol (tradingsymbol)
    symbol = row["tradingsymbol"]

    return ParsedEquity(
        exchange      = row["exchange"],
        symbol        = symbol,
        broker_symbol = symbol,
        segment       = row["segment"],
        name          = row["name"] or None,
        lot_size      = int(row["lot_size"]),
        tick_size     = float(row["tick_size"]),
        broker_token  = row["instrument_token"],
    )
