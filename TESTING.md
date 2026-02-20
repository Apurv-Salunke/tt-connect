# tt-connect — Testing Strategy

> This document is the definitive reference for how the project is tested.
> Every intern and contributor should read it before writing a single test.

---

## 1. Philosophy

### The three rules

1. **A test that requires credentials to pass is not a unit test.** Call it a live test and put it in the right place.
2. **Don't mock what you own.** Mock HTTP responses and SQLite? No — use a real in-memory DB and a real httpx mock library. Mock your own `InstrumentManager`? Never — test it directly.
3. **Speed is a feature.** Unit and integration tests must run in under 30 seconds total on any developer laptop. If a test is slow, it belongs in `live/`.

### Why three tiers?

The project has three distinct kinds of IO:

| IO type | Controlled by us? | Mock strategy |
|---|---|---|
| SQLite (instruments DB) | Yes | Real in-memory DB (`:memory:`) |
| HTTP (broker REST APIs) | No | `respx` HTTPX interceptor |
| Real broker network | No | Don't fake it — run live tests manually |

Unit tests use **none** of these. Integration tests use **real SQLite + mocked HTTP**. Live tests use **everything real**.

---

## 2. Test Pyramid

```
        /\
       /  \
      / L  \   Live tests   — real network, real credentials
     /------\               — run manually before a release
    /        \
   /    I     \  Integration — real SQLite, mocked HTTP
  /------------\             — run on every PR
 /              \
/       U        \ Unit     — pure Python, no IO at all
/------------------\         — run on every commit / pre-commit hook
```

| Tier | Speed | Count | When to run |
|---|---|---|---|
| Unit (U) | < 1 ms each | ~150 | Every commit, pre-commit hook |
| Integration (I) | < 200 ms each | ~40 | Every PR (CI) |
| Live (L) | 5–30 s each | ~15 | Manual, before any release |

---

## 3. Directory Structure

```
connect/
├── tests/
│   ├── conftest.py                     # top-level shared fixtures
│   │
│   ├── fixtures/                       # static data files — never generated at runtime
│   │   ├── zerodha_instruments.csv     # minimal CSV: 1 index, 2 equities, 2 futures, 4 options
│   │   └── responses/
│   │       ├── zerodha/
│   │       │   ├── profile.json
│   │       │   ├── funds.json
│   │       │   ├── holdings.json
│   │       │   ├── positions.json
│   │       │   ├── orders.json
│   │       │   └── trades.json
│   │       └── angelone/
│   │           ├── login_success.json
│   │           ├── login_failure.json
│   │           ├── renew_token.json
│   │           └── profile.json
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_enums.py               # AuthMode, Exchange, OptionType, OrderStatus etc.
│   │   ├── test_models.py              # Pydantic validation, field types, frozen behaviour
│   │   ├── test_capabilities.py        # verify(), verify_auth_mode(), broker declarations
│   │   ├── test_parser_zerodha.py      # parse() with fixture CSV — index/equity/future/option counts
│   │   └── test_transformer_zerodha.py # to_profile/fund/holding/position/trade/order/margin
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # in-memory DB fixtures, parsed instrument fixtures
│   │   ├── test_instrument_manager.py  # insert pipeline — counts, FK integrity, idempotency
│   │   ├── test_instrument_resolver.py # resolve() for all four instrument types
│   │   └── test_client_init.py         # AsyncTTConnect.init() with mocked HTTP adapter
│   │
│   └── live/
│       ├── README.md                   # How to run live tests + credential setup
│       ├── conftest.py                 # loads .env, skips all if no credentials present
│       ├── test_zerodha_live.py        # auth → instruments → portfolio → F&O resolution
│       └── test_angelone_live.py       # auth (auto + manual) → instruments → profile
│
├── dev/                                # Developer scripts — NOT tests, not run by pytest
│   ├── get_token.py
│   ├── test_live_*.py                  # ad-hoc exploratory scripts (not collected by pytest)
│   └── ...
```

### Why `dev/` is NOT `tests/live/`

`dev/` scripts are **exploratory and disposable** — they print output, get rewritten, and don't assert anything formally. `tests/live/` contains **real pytest tests** with `assert` statements that produce pass/fail results. Move a `dev/` script to `tests/live/` only once it has been hardened into assertions.

---

## 4. Fixture Strategy

### 4a. The fixture CSV (`tests/fixtures/zerodha_instruments.csv`)

A minimal but representative CSV used by all parser and DB tests. It must contain:

| Row | What it tests |
|---|---|
| 1 × INDICES row | Index parsing, canonical name mapping |
| 2 × NSE EQ rows | Equity parsing, ISIN field |
| 1 × BSE EQ row | BSE equity, separate exchange |
| 2 × NFO FUT rows | Future parsing, expiry, lot size |
| 1 × BFO FUT row | BSE-linked future |
| 2 × NFO CE rows | Option parsing, strike, option_type |
| 2 × NFO PE rows | Option parsing, PE side |

Keep it small — 11 rows is enough. Never use the full 77k-row production CSV in automated tests.

### 4b. JSON response fixtures (`tests/fixtures/responses/`)

One JSON file per endpoint, matching the exact shape Zerodha/AngelOne returns. These are used by integration tests to mock HTTP responses. Copy real responses (with personal data scrubbed) and commit them.

Example `zerodha/profile.json`:
```json
{
  "status": "success",
  "data": {
    "user_id": "ZZ0001",
    "user_name": "Test User",
    "email": "test@example.com",
    "mobile": "9999999999"
  }
}
```

### 4c. Pytest fixtures (`conftest.py` files)

**`tests/conftest.py`** — available to all tiers:
```python
@pytest.fixture
def zerodha_csv() -> str:
    return (Path(__file__).parent / "fixtures/zerodha_instruments.csv").read_text()

@pytest.fixture
def zerodha_response(request) -> dict:
    name = request.param  # e.g. "profile", "funds"
    path = Path(__file__).parent / f"fixtures/responses/zerodha/{name}.json"
    return json.loads(path.read_text())
```

**`tests/integration/conftest.py`** — DB fixtures:
```python
@pytest_asyncio.fixture
async def db():
    """Fresh in-memory SQLite DB with schema applied."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")
    await init_schema(conn)
    yield conn
    await conn.close()

@pytest_asyncio.fixture
async def populated_db(db, zerodha_csv):
    """DB with fixture CSV already parsed and inserted."""
    parsed = parse(zerodha_csv)
    manager = InstrumentManager(broker_id="zerodha", on_stale=OnStale.FAIL)
    manager._conn = db
    await manager._insert(parsed)
    yield db
```

---

## 5. Unit Tests — What to Test

Unit tests live in `tests/unit/`. They import only from `tt_connect` and use no IO whatsoever.

### `test_enums.py`
- Every enum member has the expected string value
- `StrEnum` construction from string works (`AuthMode("manual")`)
- Invalid string raises `ValueError`

### `test_models.py`
- Required fields missing → `ValidationError`
- Optional fields default correctly
- Frozen models reject mutation (`model.field = x` raises)
- `Fund.collateral` defaults to `0.0`
- `Holding.pnl_percent` defaults to `0.0`
- `Order.instrument` accepts `None`

### `test_capabilities.py` *(already written)*
- `verify()` rejects Index instruments, unknown segments/order types/products
- `verify_auth_mode()` rejects unsupported modes with helpful error message
- Zerodha: only MANUAL; AngelOne: MANUAL + AUTO

### `test_parser_zerodha.py`
Test `parse()` using the fixture CSV only.

```python
def test_parse_counts(zerodha_csv):
    result = parse(zerodha_csv)
    assert len(result.indices)  == 1
    assert len(result.equities) == 3
    assert len(result.futures)  == 3
    assert len(result.options)  == 4

def test_index_canonical_name(zerodha_csv):
    result = parse(zerodha_csv)
    nifty = next(i for i in result.indices if i.symbol == "NIFTY")
    assert nifty.exchange == "NSE"

def test_future_underlying_exchange(zerodha_csv):
    result = parse(zerodha_csv)
    fut = next(f for f in result.futures if f.exchange == "NFO")
    assert fut.underlying_exchange == "NSE"

def test_option_strike_is_float(zerodha_csv):
    result = parse(zerodha_csv)
    for opt in result.options:
        assert isinstance(opt.strike, float)

def test_option_type_values(zerodha_csv):
    result = parse(zerodha_csv)
    types = {o.option_type for o in result.options}
    assert types == {"CE", "PE"}

def test_unknown_exchange_skipped(zerodha_csv):
    # MCX rows in CSV should be silently skipped
    result = parse(zerodha_csv)
    assert all(i.exchange != "MCX" for i in result.indices)
```

### `test_transformer_zerodha.py`
Test every `to_*` method using raw dicts that mirror real API responses. No HTTP, no DB.

```python
# Fixture
PROFILE_RAW = {
    "user_id": "ZZ0001", "user_name": "Test User",
    "email": "t@e.com", "mobile": "9999999999"
}

def test_to_profile_maps_fields():
    t = ZerodhaTransformer()
    p = t.to_profile(PROFILE_RAW)
    assert p.client_id == "ZZ0001"
    assert p.name == "Test User"

def test_to_holding_computes_pnl_percent():
    raw = {"tradingsymbol": "SBIN", "exchange": "NSE",
           "quantity": 10, "average_price": 400.0,
           "last_price": 440.0, "pnl": 400.0}
    h = ZerodhaTransformer.to_holding(raw)
    assert h.pnl_percent == pytest.approx(10.0)

def test_to_holding_zero_avg_price_does_not_crash():
    raw = {**HOLDING_RAW, "average_price": 0.0, "last_price": 0.0}
    h = ZerodhaTransformer.to_holding(raw)
    assert h.pnl_percent == 0.0

def test_to_order_maps_trigger_pending_status():
    raw = {**ORDER_RAW, "status": "TRIGGER PENDING"}
    o = ZerodhaTransformer.to_order(raw)
    assert o.status == OrderStatus.PENDING

def test_to_trade_computes_trade_value():
    raw = {**TRADE_RAW, "quantity": 5, "average_price": 200.0}
    t = ZerodhaTransformer.to_trade(raw)
    assert t.trade_value == pytest.approx(1000.0)
```

---

## 6. Integration Tests — What to Test

Integration tests live in `tests/integration/`. They use a real in-memory SQLite DB and mock HTTP with `respx`. No network calls, no credentials.

### `test_instrument_manager.py`

```python
async def test_insert_counts(populated_db):
    async with populated_db.execute("SELECT COUNT(*) FROM instruments") as c:
        total = (await c.fetchone())[0]
    assert total == 11  # matches fixture CSV row count

async def test_futures_fk_integrity(populated_db):
    async with populated_db.execute("""
        SELECT COUNT(*) FROM futures f
        LEFT JOIN instruments u ON u.id = f.underlying_id
        WHERE u.id IS NULL
    """) as c:
        orphans = (await c.fetchone())[0]
    assert orphans == 0

async def test_idempotent_insert(db, zerodha_csv):
    """Inserting the same CSV twice (after truncate) yields same counts."""
    manager = InstrumentManager(broker_id="zerodha", on_stale=OnStale.FAIL)
    manager._conn = db
    parsed = parse(zerodha_csv)
    await manager._insert(parsed)
    first_count = await _count(db, "instruments")

    await truncate_all(db)
    await manager._insert(parsed)
    second_count = await _count(db, "instruments")

    assert first_count == second_count
```

### `test_instrument_resolver.py`

```python
async def test_resolve_index(populated_db, zerodha_csv):
    resolver = InstrumentResolver(populated_db, "zerodha")
    token = await resolver.resolve(Index(exchange=Exchange.NSE, symbol="NIFTY"))
    assert token  # non-empty string

async def test_resolve_unknown_instrument_raises(populated_db):
    resolver = InstrumentResolver(populated_db, "zerodha")
    with pytest.raises(InstrumentNotFoundError):
        await resolver.resolve(Equity(exchange=Exchange.NSE, symbol="DOESNOTEXIST"))

async def test_resolve_future_by_underlying_exchange(populated_db, zerodha_csv):
    """Future resolution uses Exchange.NSE (underlying), not Exchange.NFO."""
    parsed = parse(zerodha_csv)
    fut = parsed.futures[0]
    resolver = InstrumentResolver(populated_db, "zerodha")
    # Must pass underlying exchange, not NFO
    instrument = Future(
        exchange=Exchange.NSE,
        symbol=fut.symbol,
        expiry=fut.expiry,
    )
    token = await resolver.resolve(instrument)
    assert token == fut.broker_token
```

### `test_client_init.py`

Use `respx` to intercept HTTP calls made by `httpx.AsyncClient`:

```python
import respx
import httpx

@respx.mock
async def test_init_calls_login_and_instruments(zerodha_csv, tmp_path):
    # Mock the instruments endpoint
    respx.get("https://api.kite.trade/instruments").mock(
        return_value=httpx.Response(200, text=zerodha_csv)
    )

    import tt_connect.instrument_manager.db as db_module
    db_module.DB_PATH = tmp_path / "test.db"

    broker = AsyncTTConnect("zerodha", {
        "api_key": "testkey",
        "access_token": "testtoken",
    })
    await broker.init()
    await broker.close()

    # Instruments endpoint was called exactly once
    assert respx.calls.call_count == 1
```

---

## 7. Live Tests — What to Test

Live tests live in `tests/live/`. They are **never run in CI**. They require real credentials in a `.env` file.

### `tests/live/README.md` must explain:
1. How to set up `.env`
2. How to run: `pytest tests/live/ -v --no-header`
3. Which tests write orders (currently none, but document the policy)
4. That the instrument DB is re-downloaded every time (or how to reuse)

### `tests/live/conftest.py`

```python
import pytest
import os

def pytest_collection_modifyitems(items):
    """Skip all live tests if credentials are missing."""
    if not os.environ.get("ZERODHA_API_KEY"):
        skip = pytest.mark.skip(reason="ZERODHA_API_KEY not set — skipping live tests")
        for item in items:
            item.add_marker(skip)
```

### What live tests should assert

```python
async def test_profile_returns_real_client_id(broker):
    profile = await broker.get_profile()
    assert profile.client_id       # non-empty
    assert "@" in profile.email    # looks like an email

async def test_funds_are_non_negative(broker):
    fund = await broker.get_funds()
    assert fund.available >= 0
    assert fund.total >= 0

async def test_nifty_future_resolves(broker):
    # Query nearest expiry from the live DB
    expiry = await _nearest_expiry(broker, "NSE", "NIFTY")
    token = await broker._resolve(Future(
        exchange=Exchange.NSE, symbol="NIFTY", expiry=expiry
    ))
    assert token.isdigit()   # Zerodha tokens are numeric strings
```

---

## 8. Markers and Running Tests

### pytest markers (add to `pyproject.toml`)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "unit: pure logic, no IO",
    "integration: real SQLite, mocked HTTP",
    "live: real network — run manually with credentials",
]
testpaths = ["tests/unit", "tests/integration"]  # live/ excluded from default run
```

### CLI commands

| Command | What runs |
|---|---|
| `pytest` | Unit + integration (default — safe to always run) |
| `pytest tests/unit/` | Unit only (~1 second) |
| `pytest tests/integration/` | Integration only (~10 seconds) |
| `pytest tests/live/` | Live tests (requires credentials + network) |
| `pytest --co -q` | List all collected tests without running |
| `pytest -k "transformer"` | Run only tests matching a keyword |
| `pytest --cov=tt_connect --cov-report=term-missing` | Coverage report |

---

## 9. Tools — What to Add

Add to `pyproject.toml` `[project.optional-dependencies] dev`:

```toml
dev = [
    # existing
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.4",
    "mypy>=1.10",
    "pyotp>=2.9",
    # new
    "pytest-mock>=3.14",       # mocker fixture for simple mocking
    "respx>=0.21",             # httpx-specific request interceptor
    "pytest-cov>=5.0",         # coverage reports
    "freezegun>=1.5",          # freeze datetime for token expiry tests
]
```

### Why `respx` and not `unittest.mock.patch`?

`respx` is designed specifically for `httpx`. It intercepts at the transport layer, so the real `httpx.AsyncClient` is used — meaning any bug in how we call httpx (wrong method, missing headers, wrong content-type) is still caught. `patch` would let those bugs through.

---

## 10. Coverage Targets

| Module | Target | Notes |
|---|---|---|
| `enums.py` | 100% | Trivial, no excuse |
| `models.py` | 100% | Pydantic, no branches |
| `capabilities.py` | 100% | Already tested |
| `parser/zerodha` | 95% | Exclude MCX/CDS skip paths |
| `transformer/zerodha` | 95% | Test all `to_*` methods |
| `instrument_manager/` | 90% | Cover insert + stale check paths |
| `instrument_resolver/` | 90% | Cover all four instrument types + not-found |
| `auth/zerodha` | 85% | Cover manual mode; auto raises |
| `auth/angelone` | 85% | Cover auto login + refresh fallback |
| `client.py` | 80% | Hard to test orchestration; integration covers it |

Run with: `pytest --cov=tt_connect --cov-report=html` → open `htmlcov/index.html`

---

## 11. What NOT to Do

### Never do this in unit tests
```python
# ❌ Real network call in a unit test
async def test_profile():
    broker = AsyncTTConnect("zerodha", real_config)
    profile = await broker.get_profile()
    assert profile.client_id == "ZZ0001"

# ❌ Real file system in a unit test
async def test_manager():
    manager = InstrumentManager("zerodha", OnStale.FAIL)  # writes to _cache/!
    await manager.init(fetch_fn)
```

### Never mock your own code
```python
# ❌ Mocking InstrumentManager to test the client
with patch("tt_connect.client.InstrumentManager") as mock_mgr:
    ...
# Instead: use a real in-memory DB and a real InstrumentManager
```

### Never use the production CSV in automated tests
```python
# ❌ 77k rows — makes tests slow and fragile (file path, data changes)
CSV_PATH = "/Users/apurv/Desktop/algo-trading/master-instruments/data/zerodha.csv"
raw = CSV_PATH.read_text()
parsed = parse(raw)
# Instead: use tests/fixtures/zerodha_instruments.csv (11 rows)
```

### Never assert on floating point with `==`
```python
# ❌
assert holding.pnl_percent == 10.0

# ✅
assert holding.pnl_percent == pytest.approx(10.0)
```

---

## 12. CI Pipeline (GitHub Actions sketch)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-and-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e "connect/[dev]"
      - run: pytest connect/tests/unit connect/tests/integration --tb=short
      - run: pytest connect/tests/unit --cov=tt_connect --cov-fail-under=85

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff mypy
      - run: ruff check connect/
      - run: mypy connect/tt_connect/

# Live tests: run manually from your machine, never in CI
# pytest connect/tests/live/ -v
```

---

## 13. Checklist for Every New Feature

Before merging any PR that adds or changes behaviour:

- [ ] Unit tests for any new pure functions (parser, transformer, capabilities)
- [ ] Integration tests for any new DB operations (manager, resolver)
- [ ] Fixture JSON added for any new HTTP endpoint being mocked
- [ ] `tests/live/` test updated or noted as pending
- [ ] `pytest` (unit + integration) passes with zero failures
- [ ] Coverage doesn't drop below current baseline
- [ ] PLAN.md checkboxes updated
