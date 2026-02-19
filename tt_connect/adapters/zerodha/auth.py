import json
from pathlib import Path
import pyotp

SESSION_PATH = Path("_cache/session.json")


class ZerodhaAuth:
    BASE_URL = "https://api.kite.trade"

    def __init__(self, config: dict, client):
        self._config = config
        self._client = client
        self._access_token: str | None = None

    async def login(self) -> str:
        if self._load_session():
            return self._access_token

        totp = pyotp.TOTP(self._config["totp_secret"]).now()
        # Step 1: Get request token via Kite OAuth flow
        # Step 2: Exchange request token for access token
        # Step 3: Persist session
        raise NotImplementedError

    async def refresh(self) -> None:
        # Zerodha access tokens don't refresh — full re-login daily
        await self.login()

    def _load_session(self) -> bool:
        if not SESSION_PATH.exists():
            return False
        data = json.loads(SESSION_PATH.read_text())
        if data.get("broker") != "zerodha":
            return False
        self._access_token = data["access_token"]
        return True

    def _persist_session(self, access_token: str) -> None:
        SESSION_PATH.parent.mkdir(exist_ok=True)
        SESSION_PATH.write_text(json.dumps({
            "broker": "zerodha",
            "access_token": access_token,
        }))
        self._access_token = access_token

    @property
    def headers(self) -> dict:
        return {
            "X-Kite-Version": "3",
            "Authorization": f"token {self._config['api_key']}:{self._access_token}",
        }
