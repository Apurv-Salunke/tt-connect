from tt_connect.exceptions import AuthenticationError


class ZerodhaAuth:
    def __init__(self, config: dict, client):
        self._config = config
        self._access_token: str | None = None

    async def login(self) -> None:
        token = self._config.get("access_token")
        if not token:
            raise AuthenticationError(
                "Zerodha requires 'access_token' in config. "
                "Obtain it from https://kite.trade/connect/login?api_key=<your_key>&v=3"
            )
        self._access_token = token

    async def refresh(self) -> None:
        # Zerodha tokens expire at midnight IST. Re-login requires a new access_token
        # from the user — there is no programmatic refresh endpoint.
        await self.login()

    @property
    def headers(self) -> dict:
        return {
            "X-Kite-Version": "3",
            "Authorization": f"token {self._config['api_key']}:{self._access_token}",
        }
