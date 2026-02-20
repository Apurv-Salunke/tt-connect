import json
from pathlib import Path
import pytest

@pytest.fixture
def zerodha_csv() -> str:
    return (Path(__file__).parent / "fixtures/zerodha_instruments.csv").read_text()

@pytest.fixture
def zerodha_response(request) -> dict:
    name = request.param  # e.g. "profile", "funds"
    path = Path(__file__).parent / f"fixtures/responses/zerodha/{name}.json"
    if not path.exists():
        pytest.fail(f"Fixture response file not found: {path}")
    return json.loads(path.read_text())
