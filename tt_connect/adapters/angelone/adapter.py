from tt_connect.adapters.base import BrokerAdapter
from tt_connect.adapters.angelone.auth import AngelOneAuth
from tt_connect.adapters.angelone.transformer import AngelOneTransformer
from tt_connect.adapters.angelone.capabilities import ANGELONE_CAPABILITIES
from tt_connect.adapters.angelone.parser import parse, ParsedInstruments
from tt_connect.capabilities import Capabilities

BASE_URL = "https://apiconnect.angelbroking.com"


class AngelOneAdapter(BrokerAdapter, broker_id="angelone"):

    def __init__(self, config: dict):
        super().__init__(config)
        self.auth = AngelOneAuth(config, self._client)
        self._transformer = AngelOneTransformer()

    @property
    def transformer(self) -> AngelOneTransformer:
        return self._transformer

    # --- Lifecycle ---

    async def login(self) -> None:
        await self.auth.login()

    async def refresh_session(self) -> None:
        await self.auth.refresh()

    async def fetch_instruments(self) -> ParsedInstruments:
        # TODO: Implement AngelOne-specific instrument fetch (usually a JSON endpoint)
        raise NotImplementedError

    # --- REST ---

    async def get_profile(self) -> dict:
        return await self._request("GET", f"{BASE_URL}/rest/auth/angelbroking/user/v1/getProfile",
                                   headers=self.auth.headers)

    async def get_funds(self) -> dict:
        return await self._request("GET", f"{BASE_URL}/rest/auth/angelbroking/user/v1/getRMS",
                                   headers=self.auth.headers)

    async def get_holdings(self) -> list[dict]:
        return await self._request("GET", f"{BASE_URL}/rest/auth/angelbroking/portfolio/v1/getHolding",
                                   headers=self.auth.headers)

    async def get_positions(self) -> list[dict]:
        return await self._request("GET", f"{BASE_URL}/rest/auth/angelbroking/order/v1/getPosition",
                                   headers=self.auth.headers)

    async def place_order(self, params: dict) -> dict:
        return await self._request("POST", f"{BASE_URL}/rest/auth/angelbroking/order/v1/placeOrder",
                                   headers=self.auth.headers, json=params)

    async def modify_order(self, order_id: str, params: dict) -> dict:
        # AngelOne uses orderid in the body for modification
        return await self._request("POST", f"{BASE_URL}/rest/auth/angelbroking/order/v1/modifyOrder",
                                   headers=self.auth.headers, json=params)

    async def cancel_order(self, order_id: str) -> dict:
        # AngelOne uses orderid in the body for cancellation
        params = {"orderid": order_id}
        return await self._request("POST", f"{BASE_URL}/rest/auth/angelbroking/order/v1/cancelOrder",
                                   headers=self.auth.headers, json=params)

    async def get_order(self, order_id: str) -> dict:
        # AngelOne doesn't have a single order fetch? It's usually orderbook filter.
        raise NotImplementedError

    async def get_orders(self) -> list[dict]:
        return await self._request("GET", f"{BASE_URL}/rest/auth/angelbroking/order/v1/getOrderBook",
                                   headers=self.auth.headers)

    # --- Capabilities ---

    @property
    def capabilities(self) -> Capabilities:
        return ANGELONE_CAPABILITIES

    # --- Internal ---

    def _is_error(self, raw: dict, status_code: int) -> bool:
        return raw.get("status") == False or status_code >= 400
