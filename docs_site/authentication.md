# Authentication

## Auth modes

| Mode | How it works | Broker support |
|------|-------------|----------------|
| `manual` | You provide a fresh access token each trading day | All brokers |
| `auto` | tt-connect logs in automatically (e.g. via TOTP) | Brokers that support it |

## Basic usage

=== "Sync"

    ```python
    from tt_connect import TTConnect

    config = {
        "api_key": "YOUR_API_KEY",
        "access_token": "YOUR_ACCESS_TOKEN",
    }

    with TTConnect(broker_id, config) as broker:
        print(broker.get_profile().name)
    ```

=== "Async"

    ```python
    import asyncio
    from tt_connect import AsyncTTConnect

    async def main() -> None:
        config = {
            "api_key": "YOUR_API_KEY",
            "access_token": "YOUR_ACCESS_TOKEN",
        }

        async with AsyncTTConnect(broker_id, config) as broker:
            profile = await broker.get_profile()
            print(profile.name)

    asyncio.run(main())
    ```

## Config keys

### Common keys (all brokers)

| Key | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | Broker app API key |
| `access_token` | `str` | required (manual mode) | Daily session token |
| `on_stale` | `"fail"` or `"warn"` | `"fail"` | Behavior when instrument cache refresh fails |
| `cache_session` | `bool` | `False` | Persist session to disk for reuse within same day |

### Auto mode keys (brokers that support it)

| Key | Type | Description |
|---|---|---|
| `auth_mode` | `"auto"` | Enable automatic login |
| `client_id` | `str` | Broker client code |
| `pin` | `str` | Trading PIN |
| `totp_secret` | `str` | Base32 TOTP secret for 2FA |

??? note "Broker-specific config details"
    See [Broker Differences](broker-differences.md) for the exact config keys required by each broker.

## Instrument cache behavior (`on_stale`)

| Value | Meaning |
|---|---|
| `"fail"` | If instrument refresh fails at startup, client init fails (safest for production) |
| `"warn"` | If refresh fails and a cache exists, continue with stale data |

## Environment variables

Keep credentials out of code:

```python
import os
from tt_connect import TTConnect

config = {
    "api_key": os.environ["BROKER_API_KEY"],
    "access_token": os.environ["BROKER_ACCESS_TOKEN"],
}

with TTConnect(broker_id, config) as broker:
    print(broker.get_profile().name)
```

## Session lifecycle

- Client creation triggers login and instrument initialization
- Sessions are valid for the current trading day only

!!! warning "Daily token expiry (SEBI requirement)"
    All Indian broker tokens expire at end of day. This is a SEBI mandate. You must re-authenticate each trading day. If your token expires mid-session, API calls raise `AuthenticationError`.

## Good practices

- Keep credentials in environment variables or a secret manager
- Never hardcode tokens in source code
- Always close the client (the `with` statement does this automatically)

## Common mistakes

- Using `auto` auth mode on a broker that only supports `manual`
- Missing required keys for auto mode (e.g. `totp_secret`)
- Using an expired access token
- Mixing environment variables from different brokers
