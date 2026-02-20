import aiosqlite
from tt_connect.instruments import Instrument, Index, Equity, Future, Option
from tt_connect.exceptions import InstrumentNotFoundError


class InstrumentResolver:
    def __init__(self, conn: aiosqlite.Connection, broker_id: str):
        self._conn = conn
        self._broker_id = broker_id
        self._cache: dict[Instrument, str] = {}

    async def resolve(self, instrument: Instrument) -> str:
        if instrument in self._cache:
            return self._cache[instrument]
        token = await self._resolve(instrument)
        self._cache[instrument] = token
        return token

    async def _resolve(self, instrument: Instrument) -> str:
        if isinstance(instrument, Index):
            return await self._resolve_index(instrument)
        if isinstance(instrument, Equity):
            return await self._resolve_equity(instrument)
        if isinstance(instrument, Future):
            return await self._resolve_future(instrument)
        if isinstance(instrument, Option):
            return await self._resolve_option(instrument)
        raise InstrumentNotFoundError(f"Unsupported instrument type: {type(instrument)}")

    async def _resolve_index(self, instrument: Index) -> str:
        query = """
            SELECT bt.token FROM instruments i
            JOIN equities e ON e.instrument_id = i.id
            JOIN broker_tokens bt ON bt.instrument_id = i.id
            WHERE i.exchange = ? AND i.symbol = ? AND i.segment = 'INDICES' AND bt.broker_id = ?
        """
        async with self._conn.execute(query, (instrument.exchange, instrument.symbol, self._broker_id)) as cur:
            row = await cur.fetchone()
        if not row:
            raise InstrumentNotFoundError(f"No index found: {instrument.exchange}:{instrument.symbol}")
        return row[0]

    async def _resolve_equity(self, instrument: Equity) -> str:
        query = """
            SELECT bt.token FROM instruments i
            JOIN equities e ON e.instrument_id = i.id
            JOIN broker_tokens bt ON bt.instrument_id = i.id
            WHERE i.exchange = ? AND i.symbol = ? AND i.segment != 'INDICES' AND bt.broker_id = ?
        """
        async with self._conn.execute(query, (instrument.exchange, instrument.symbol, self._broker_id)) as cur:
            row = await cur.fetchone()
        if not row:
            raise InstrumentNotFoundError(f"No equity found: {instrument.exchange}:{instrument.symbol}")
        return row[0]

    async def _resolve_future(self, instrument: Future) -> str:
        query = """
            SELECT bt.token FROM instruments i
            JOIN futures f ON f.instrument_id = i.id
            JOIN broker_tokens bt ON bt.instrument_id = i.id
            WHERE i.exchange = ? AND i.symbol = ? AND f.expiry = ? AND bt.broker_id = ?
        """
        async with self._conn.execute(query, (
            instrument.exchange, instrument.symbol, instrument.expiry.isoformat(), self._broker_id
        )) as cur:
            row = await cur.fetchone()
        if not row:
            raise InstrumentNotFoundError(f"No future found: {instrument.exchange}:{instrument.symbol} {instrument.expiry}")
        return row[0]

    async def _resolve_option(self, instrument: Option) -> str:
        query = """
            SELECT bt.token FROM instruments i
            JOIN options o ON o.instrument_id = i.id
            JOIN broker_tokens bt ON bt.instrument_id = i.id
            WHERE i.exchange = ? AND i.symbol = ? AND o.expiry = ?
              AND o.strike = ? AND o.option_type = ? AND bt.broker_id = ?
        """
        async with self._conn.execute(query, (
            instrument.exchange, instrument.symbol, instrument.expiry.isoformat(),
            instrument.strike, instrument.option_type, self._broker_id
        )) as cur:
            row = await cur.fetchone()
        if not row:
            raise InstrumentNotFoundError(
                f"No option found: {instrument.exchange}:{instrument.symbol} "
                f"{instrument.expiry} {instrument.strike}{instrument.option_type}"
            )
        return row[0]
