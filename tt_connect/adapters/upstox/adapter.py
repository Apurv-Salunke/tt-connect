from tt_connect.adapters.base import BrokerAdapter
from tt_connect.adapters.upstox.auth import UpstoxAuth
from tt_connect.adapters.upstox.transformer import UpstoxTransformer
from tt_connect.adapters.upstox.capabilities import UPSTOX_CAPABILITIES
from tt_connect.capabilities import Capabilities

BASE_URL = "https://api.upstox.com/v2"


class UpstoxAdapter(BrokerAdapter, broker_id="upstox"):

    def __init__(self, config: dict):
        super().__init__(config)
        self.auth = UpstoxAuth(config, self._client)
        self.transformer = UpstoxTransformer()

    async def login(self) -> None:
        await self.auth.login()

    async def refresh_session(self) -> None:
        await self.auth.refresh()

    async def fetch_instruments(self) -> list[dict]:
        raise NotImplementedError

    async def get_profile(self) -> dict:
        return await self._request("GET", f"{BASE_URL}/user/profile",
                                   headers=self.auth.headers)

    async def get_funds(self) -> dict:
        return await self._request("GET", f"{BASE_URL}/user/get-funds-and-margin",
                                   headers=self.auth.headers)

    async def get_holdings(self) -> list[dict]:
        return await self._request("GET", f"{BASE_URL}/portfolio/long-term-holdings",
                                   headers=self.auth.headers)

    async def get_positions(self) -> list[dict]:
        return await self._request("GET", f"{BASE_URL}/portfolio/short-term-positions",
                                   headers=self.auth.headers)

    async def place_order(self, params: dict) -> dict:
        return await self._request("POST", f"{BASE_URL}/order/place",
                                   headers=self.auth.headers, json=params)

    async def modify_order(self, order_id: str, params: dict) -> dict:
        return await self._request("PUT", f"{BASE_URL}/order/modify",
                                   headers=self.auth.headers, json={"order_id": order_id, **params})

    async def cancel_order(self, order_id: str) -> dict:
        return await self._request("DELETE", f"{BASE_URL}/order/cancel",
                                   headers=self.auth.headers, params={"order_id": order_id})

    async def get_order(self, order_id: str) -> dict:
        return await self._request("GET", f"{BASE_URL}/order/details",
                                   headers=self.auth.headers, params={"order_id": order_id})

    async def get_orders(self) -> list[dict]:
        return await self._request("GET", f"{BASE_URL}/order/retrieve-all",
                                   headers=self.auth.headers)

    @property
    def capabilities(self) -> Capabilities:
        return UPSTOX_CAPABILITIES

    def _is_error(self, raw: dict, status_code: int) -> bool:
        return raw.get("status") == "error" or status_code >= 400
