# GEMINI.md

## Project Overview

**tt-connect** is a unified API layer for Indian stock brokers (e.g., Zerodha, AngelOne). It provides a standardized interface for authentication, order management, portfolio tracking, and real-time data streaming, shielding developers from broker-specific implementation details.

### Key Technologies

- **Python 3.11+**: Core language.
- **Pydantic v2**: For runtime type enforcement and data normalization.
- **HTTPX**: Asynchronous HTTP client for REST APIs.
- **aiosqlite**: Async interface for SQLite, used for the instrument master.
- **websockets**: For real-time data streaming (ticks and order updates).

### Architecture

1.  **Unified API (Async-First):** The library is built with `AsyncTTConnect` as the core, and `TTConnect` provides a synchronous wrapper for ease of use in non-async environments.
2.  **Adapter Pattern:** Broker-specific logic is isolated in `adapters/`. Each adapter includes:
    - `adapter.py`: Main adapter class.
    - `auth.py`: Automated login and session management.
    - `transformer.py`: Bidirectional translation between broker-specific and canonical data shapes.
    - `capabilities.py`: Declares supported segments and features.
3.  **Instrument Resolver:** A SQLite-backed engine that translates canonical instrument objects (Equity, Future, Option) into broker-specific tokens.
4.  **Reactive Streaming Engine:** A unified WebSocket client that emits standardized `Tick` objects.

---

## Building and Running

### Setup

Ensure you have Python 3.11 or higher installed.

```bash
# Install dependencies
pip install .

# Install development dependencies (testing, linting, typing)
pip install ".[dev]"
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your broker credentials:

```bash
cp .env.example .env
```

### Testing

Tests are located in the `tests/` directory and use `pytest`.

```bash
# Run all tests
pytest

# Run tests with coverage (if configured)
pytest --cov=tt_connect
```

### Development Tools

- **Linting:** `ruff check .`
- **Formatting:** `ruff format .`
- **Type Checking:** `mypy .`

---

## Development Conventions

### Adding a New Broker

To add support for a new broker, create a new directory in `tt_connect/adapters/` and implement the following files:

1.  `adapter.py`: Inherit from `BrokerAdapter` and set the `broker_id`.
2.  `auth.py`: Implement the login and token refresh logic.
3.  `transformer.py`: Implement static methods for mapping broker data to/from `tt_connect` models.
4.  `capabilities.py`: Define the `Capabilities` object for the broker.

### Coding Style

- **Strict Typing:** Always use type hints. `mypy` is used in strict mode.
- **Async-First:** Implement new features in `AsyncTTConnect` first, then expose them in `TTConnect`.
- **Immutable Models:** Pydantic models in `models.py` are frozen by default.
- **Canonical Symbols:** Symbols must follow NSE naming conventions.

### Instrument Resolution

Resolution happens via the SQLite database in `_cache/instruments.db`. The database is rebuilt daily or on startup if stale. Use `InstrumentManager` to handle instrument master refreshes.

---

## Key Files & Directories

- `tt_connect/client.py`: Main entry points (`TTConnect` and `AsyncTTConnect`).
- `tt_connect/adapters/base.py`: Base class for all broker adapters.
- `tt_connect/instrument_manager/`: Logic for managing the SQLite instrument database.
- `tt_connect/ws/`: WebSocket client and tick normalization.
- `docs/ARCHITECTURE.md`: Detailed architectural design.
- `docs/DESIRED_STATE.md`: Goals and developer experience vision.
