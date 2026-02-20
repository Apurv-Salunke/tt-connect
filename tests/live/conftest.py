import pytest
import os
from tt_connect.client import AsyncTTConnect

@pytest.fixture
def broker_config() -> dict:
    return {
        "api_key":      os.environ.get("ZERODHA_API_KEY"),
        "access_token": os.environ.get("ZERODHA_ACCESS_TOKEN"),
    }

def pytest_collection_modifyitems(items):
    """Skip all live tests if credentials are missing."""
    if not os.environ.get("ZERODHA_API_KEY") or not os.environ.get("ZERODHA_ACCESS_TOKEN"):
        skip = pytest.mark.skip(reason="ZERODHA_API_KEY or ACCESS_TOKEN not set — skipping live tests")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip)

@pytest.fixture
async def broker(broker_config):
    b = AsyncTTConnect("zerodha", broker_config)
    await b.init()
    yield b
    await b.close()
