# Troubleshooting

Common errors and how to fix them.

---

## Authentication Errors

### `AuthenticationError: Invalid token` / `AuthenticationError: Session expired`

**Cause:** Broker tokens expire at end-of-day (SEBI requirement). A token issued on Monday is invalid on Tuesday.

**Fix:**
- **Zerodha:** Repeat the daily OAuth flow to obtain a fresh `access_token` (see [Zerodha OAuth flow](#zerodha-oauth-flow) below).
- **AngelOne (auto mode):** Token refresh is automatic — re-run your script and `init()` will re-authenticate via TOTP.
- **AngelOne (manual mode):** Supply a fresh `access_token` obtained from a new login.

---

### `AuthenticationError: Invalid API key`

**Cause:** The `api_key` value is wrong or the app has been disabled.

**Fix:** Log in to your broker's developer portal and verify the key is active:
- Zerodha: https://kite.trade/
- AngelOne: https://smartapi.angelbroking.com/

---

### `AuthenticationError: Invalid TOTP` (AngelOne)

**Cause:** The `totp_secret` is wrong or your system clock is out of sync (TOTP codes are time-based and valid for only 30 seconds).

**Fix:**
1. Verify the `totp_secret` by generating a TOTP code manually using your authenticator app and confirming it matches what `pyotp.TOTP(secret).now()` produces.
2. Sync your system clock: `sudo ntpdate -u pool.ntp.org` (Linux/macOS) or use Windows Time service.

---

## Zerodha OAuth Flow

Zerodha uses a standard OAuth flow. There is no automatic TOTP login — you must complete this manually each trading day:

1. **Get your login URL:**
   ```
   https://kite.trade/connect/login?api_key=<your_api_key>&v=3
   ```
2. **Log in** in the browser. After authorization you'll be redirected to your configured redirect URL with a `request_token` in the query string:
   ```
   https://your-redirect-url.com/callback?request_token=<token>&action=login&status=success
   ```
3. **Exchange the `request_token` for an `access_token`** using the Kite Connect SDK or a direct API call:
   ```python
   import hashlib
   import requests

   checksum = hashlib.sha256(
       f"{api_key}{request_token}{api_secret}".encode()
   ).hexdigest()

   resp = requests.post("https://api.kite.trade/session/token", data={
       "api_key": api_key,
       "request_token": request_token,
       "checksum": checksum,
   }, headers={"X-Kite-Version": "3"})

   access_token = resp.json()["data"]["access_token"]
   ```
4. Use the `access_token` in your `ZerodhaConfig`. Repeat each morning.

---

## AngelOne TOTP Setup

When enabling TOTP in the AngelOne mobile app:

1. Go to **Profile → Settings → Enable TOTP**.
2. You will see a QR code. **Do not scan it with your authenticator app yet.**
3. Tap **"Copy key"** or **"Show key"** — this reveals the raw Base32 secret (e.g. `JBSWY3DPEHPK3PXP`).
4. Copy this secret and use it as `totp_secret` in your config.
5. You can also scan the QR with your authenticator app for phone-based TOTP — both will work in parallel.

If you already scanned the QR and never saved the secret, you must reset and re-enable TOTP to get the secret again.

---

## Instrument Errors

### `InstrumentNotFoundError: Could not resolve <instrument>`

**Cause:** The symbol, expiry, or strike does not exist in the broker's instrument master.

Common causes:
- Symbol typo (`"RELIANCEINDS"` instead of `"RELIANCE"`)
- Expired contract (expiry date in the past)
- Strike that does not trade (wrong increment — e.g. 25001 instead of 25000)
- Wrong exchange (`Exchange.BSE` for an NFO contract)

**Fix:**
```python
# Search for the correct symbol first
results = broker.search_instruments("RELIANCE", exchange=Exchange.NSE)
print([r.symbol for r in results])

# List available expiries
expiries = broker.get_expiries(Equity(Exchange.NSE, "NIFTY"))
print(expiries)

# List available options for a given expiry
options = broker.get_options(Equity(Exchange.NSE, "NIFTY"), expiry=expiries[0])
print([(o.strike, o.option_type) for o in options[:10]])
```

---

### `InstrumentManagerError: Instrument manager not initialized`

**Cause:** A method that requires the instrument DB was called before `init()` completed.

**Fix:** Always use the context manager or call `init()` before any data methods:
```python
with TTConnect("zerodha", config) as broker:   # init() is called here
    results = broker.search_instruments("NIFTY")
```

---

## Order Errors

### `UnsupportedFeatureError: ... segment not supported`

**Cause:** You're placing an order on an exchange the broker doesn't support (e.g. MCX on Zerodha).

**Fix:** Check the broker capability table in the [README](../README.md). Use a broker that supports the segment you need.

---

### `InvalidOrderError: ...`

**Cause:** The order parameters violate broker rules. Common cases:
- Limit order with no `price`
- Stop-loss order with no `trigger_price`
- Quantity below minimum lot size
- CNC product on a futures/options contract (use NRML)

**Fix:** Check the error message — it usually contains the broker's reason. Validate params before placing:
```python
broker.place_order(
    instrument=Equity(Exchange.NSE, "SBIN"),
    side=Side.BUY,
    qty=1,
    order_type=OrderType.LIMIT,
    product=ProductType.CNC,
    price=800.00,   # required for LIMIT orders
)
```

---

### `InsufficientFundsError`

**Cause:** Not enough margin or available funds for the order.

**Fix:**
```python
funds = broker.get_funds()
print(f"Available: ₹{funds.available:,.2f}")
```

---

## Connection / Setup Errors

### `ClientNotConnectedError`

**Cause:** A data method was called before the client finished initializing.

**Fix:** Use the context manager (recommended) or call `init()` explicitly:
```python
# Context manager — init() and close() are automatic
with TTConnect("zerodha", config) as broker:
    profile = broker.get_profile()

# Manual lifecycle
broker = TTConnect("zerodha", config)
# init() is called in __init__ — broker is ready immediately
profile = broker.get_profile()
broker.close()
```

---

### `ClientClosedError`

**Cause:** A method was called after `close()`. The client cannot be reused.

**Fix:** Create a new client instance.

---

## Installation Issues

### `ModuleNotFoundError: No module named 'tt_connect'`

**Fix:** Install the package:
```bash
pip install tt-connect
```
Or for local development from the repo:
```bash
cd connect
poetry install
```

---

### Poetry environment not activated

If you installed via Poetry and `import tt_connect` still fails, activate the environment:
```bash
poetry shell
python your_script.py
# or without activating:
poetry run python your_script.py
```
