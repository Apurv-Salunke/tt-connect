class UpstoxAuth:
    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self, config: dict, client):
        self._config = config
        self._client = client
        self._access_token: str | None = None

    async def login(self) -> None:
        raise NotImplementedError

    async def refresh(self) -> None:
        raise NotImplementedError

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }
