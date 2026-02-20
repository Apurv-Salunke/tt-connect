# Live Tests — Credential Setup

> **WARNING**: Live tests perform real network requests against broker APIs.
> They are never run in CI. Use them only for manual pre-release validation.

## 1. Environment Setup

Create a `.env` file in the `connect/` root (or set these in your shell):

```bash
# Zerodha
ZERODHA_API_KEY=your_api_key
ZERODHA_ACCESS_TOKEN=your_access_token

# AngelOne
ANGEL_API_KEY=your_api_key
ANGEL_CLIENT_ID=your_id
ANGEL_PASSWORD=your_pin
ANGEL_TOTP_SECRET=your_totp_seed
```

## 2. Running Live Tests

```bash
# Run all live tests
pytest tests/live/ -v

# Run only Zerodha
pytest tests/live/test_zerodha_live.py -v
```

## 3. Order Policy

Currently, live tests **only read data** (profile, funds, holdings). 
Tests that place real orders are marked with `@pytest.mark.skip` or require explicit opt-in. 
Never commit a test that places a market order without a safety check.

## 4. Troubleshooting

* **Instrument DB**: Live tests will download the full instrument master (~5-10MB). 
  If you have a slow connection, reuse an existing `_cache/instruments.db` by setting `ON_STALE=warn` in your config.
* **Token Expiry**: Zerodha tokens expire at 6 AM IST. You must provide a fresh `ACCESS_TOKEN` daily.
