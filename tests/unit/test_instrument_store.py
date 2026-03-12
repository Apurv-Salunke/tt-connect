"""Unit tests for AsyncInstrumentStore / InstrumentStore lifecycle."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tt_connect.core.store.store import AsyncInstrumentStore, InstrumentStore


def _patch_manager():
    """Return a mock InstrumentManager that skips DB I/O."""
    mock_manager = MagicMock()
    mock_manager._conn = MagicMock()
    mock_manager.open_existing = AsyncMock()
    mock_manager._conn.close = AsyncMock()
    mock_manager.queries = MagicMock()
    mock_manager.queries.bind = MagicMock()
    return mock_manager


@pytest.mark.asyncio
async def test_init_opens_existing_db():
    mock_manager = _patch_manager()

    store = AsyncInstrumentStore.__new__(AsyncInstrumentStore)
    store._manager = mock_manager
    store._queries = mock_manager.queries

    await store.init()

    mock_manager.open_existing.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_closes_db_connection_and_unbinds_queries():
    mock_manager = _patch_manager()
    original_conn = mock_manager._conn

    store = AsyncInstrumentStore.__new__(AsyncInstrumentStore)
    store._manager = mock_manager
    store._queries = mock_manager.queries

    await store.close()

    original_conn.close.assert_awaited_once()
    mock_manager.queries.bind.assert_called_once_with(None)
    assert mock_manager._conn is None


@pytest.mark.asyncio
async def test_close_is_idempotent_when_conn_is_none():
    mock_manager = MagicMock()
    mock_manager._conn = None
    mock_manager.queries = MagicMock()
    mock_manager.queries.bind = MagicMock()

    store = AsyncInstrumentStore.__new__(AsyncInstrumentStore)
    store._manager = mock_manager
    store._queries = mock_manager.queries

    await store.close()

    mock_manager.queries.bind.assert_not_called()


@pytest.mark.asyncio
async def test_context_manager():
    mock_manager = _patch_manager()
    original_conn = mock_manager._conn

    store = AsyncInstrumentStore.__new__(AsyncInstrumentStore)
    store._manager = mock_manager
    store._queries = mock_manager.queries

    async with store:
        mock_manager.open_existing.assert_awaited_once()

    original_conn.close.assert_awaited_once()


def test_init_failure_cleans_up_thread():
    """If init() raises, the background thread must be stopped."""
    mock_manager = _patch_manager()
    mock_manager.open_existing = AsyncMock(side_effect=RuntimeError("db missing"))

    with (
        patch("tt_connect.core.store.store.InstrumentManager", return_value=mock_manager),
        pytest.raises(RuntimeError),
    ):
        InstrumentStore("zerodha")
