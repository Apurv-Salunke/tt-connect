"""Unit tests for typed broker configuration models and validation."""

from __future__ import annotations

import pytest

from tt_connect.config import AngelOneConfig, ZerodhaConfig, validate_config
from tt_connect.enums import AuthMode, OnStale
from tt_connect.exceptions import ConfigurationError


# ---------------------------------------------------------------------------
# AngelOneConfig — AUTO mode (default)
# ---------------------------------------------------------------------------


def test_angelone_auto_valid():
    cfg = AngelOneConfig(
        api_key="key123",
        client_id="A001",
        pin="1234",
        totp_secret="ABCDEF",
    )
    assert cfg.auth_mode == AuthMode.AUTO
    assert cfg.api_key == "key123"
    assert cfg.on_stale == OnStale.FAIL
    assert cfg.cache_session is False


def test_angelone_auto_missing_client_id():
    with pytest.raises(ValueError, match="client_id"):
        AngelOneConfig(api_key="key", pin="1234", totp_secret="ABC")


def test_angelone_auto_missing_pin():
    with pytest.raises(ValueError, match="pin"):
        AngelOneConfig(api_key="key", client_id="A001", totp_secret="ABC")


def test_angelone_auto_missing_totp_secret():
    with pytest.raises(ValueError, match="totp_secret"):
        AngelOneConfig(api_key="key", client_id="A001", pin="1234")


def test_angelone_auto_missing_api_key():
    with pytest.raises(ValueError, match="api_key"):
        AngelOneConfig(client_id="A001", pin="1234", totp_secret="ABC")


# ---------------------------------------------------------------------------
# AngelOneConfig — MANUAL mode
# ---------------------------------------------------------------------------


def test_angelone_manual_valid():
    cfg = AngelOneConfig(
        auth_mode=AuthMode.MANUAL,
        api_key="key123",
        access_token="jwt-token",
    )
    assert cfg.auth_mode == AuthMode.MANUAL
    assert cfg.access_token == "jwt-token"


def test_angelone_manual_missing_access_token():
    with pytest.raises(ValueError, match="access_token"):
        AngelOneConfig(auth_mode=AuthMode.MANUAL, api_key="key123")


# ---------------------------------------------------------------------------
# AngelOneConfig — extra field (typo guard)
# ---------------------------------------------------------------------------


def test_angelone_extra_field_raises():
    with pytest.raises(ValueError, match="Extra inputs"):
        AngelOneConfig(
            api_key="key",
            client_id="A001",
            pin="1234",
            totp_secret="ABC",
            acess_token="typo",  # deliberate typo — should be caught
        )


# ---------------------------------------------------------------------------
# AngelOneConfig — optional fields and defaults
# ---------------------------------------------------------------------------


def test_angelone_cache_session_and_on_stale():
    cfg = AngelOneConfig(
        api_key="key",
        client_id="A001",
        pin="1234",
        totp_secret="ABC",
        cache_session=True,
        on_stale=OnStale.WARN,
    )
    assert cfg.cache_session is True
    assert cfg.on_stale == OnStale.WARN


def test_angelone_to_dict_round_trips():
    cfg = AngelOneConfig(api_key="k", client_id="c", pin="p", totp_secret="t")
    d = cfg.to_dict()
    assert d["api_key"] == "k"
    assert d["auth_mode"] == AuthMode.AUTO


# ---------------------------------------------------------------------------
# ZerodhaConfig
# ---------------------------------------------------------------------------


def test_zerodha_valid():
    cfg = ZerodhaConfig(api_key="h7pk", access_token="tokxyz")
    assert cfg.api_key == "h7pk"
    assert cfg.access_token == "tokxyz"
    assert cfg.on_stale == OnStale.FAIL


def test_zerodha_missing_api_key():
    with pytest.raises(ValueError, match="api_key"):
        ZerodhaConfig(access_token="tok")


def test_zerodha_missing_access_token():
    with pytest.raises(ValueError, match="access_token"):
        ZerodhaConfig(api_key="h7pk")


def test_zerodha_extra_field_raises():
    with pytest.raises(ValueError, match="Extra inputs"):
        ZerodhaConfig(api_key="k", access_token="t", acces_token="typo")


# ---------------------------------------------------------------------------
# validate_config helper
# ---------------------------------------------------------------------------


def test_validate_config_angelone_dict():
    cfg = validate_config("angelone", {
        "api_key": "k", "client_id": "c", "pin": "p", "totp_secret": "t",
    })
    assert isinstance(cfg, AngelOneConfig)


def test_validate_config_zerodha_dict():
    cfg = validate_config("zerodha", {"api_key": "k", "access_token": "t"})
    assert isinstance(cfg, ZerodhaConfig)


def test_validate_config_passes_through_model():
    model = ZerodhaConfig(api_key="k", access_token="t")
    result = validate_config("zerodha", model)
    assert result is model


def test_validate_config_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="zerodha"):
        validate_config("zerodha", {"api_key": "k"})  # missing access_token


def test_validate_config_error_message_is_readable():
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config("angelone", {"api_key": "k"})  # AUTO mode, missing creds
    msg = str(exc_info.value)
    assert "angelone" in msg
    assert "client_id" in msg or "AUTO" in msg


def test_validate_config_unknown_broker_does_not_raise():
    # Unknown brokers skip validation — adapter registry will raise later
    validate_config("unknown_broker", {"some_key": "val"})


# ---------------------------------------------------------------------------
# Adapter-level integration — ConfigurationError raised at construction
# ---------------------------------------------------------------------------


def test_angelone_adapter_raises_on_bad_config():
    from tt_connect.adapters.angelone.adapter import AngelOneAdapter
    with pytest.raises(ConfigurationError):
        AngelOneAdapter({"api_key": "k"})  # missing client_id, pin, totp_secret


def test_zerodha_adapter_raises_on_bad_config():
    from tt_connect.adapters.zerodha.adapter import ZerodhaAdapter
    with pytest.raises(ConfigurationError):
        ZerodhaAdapter({"api_key": "k"})  # missing access_token
