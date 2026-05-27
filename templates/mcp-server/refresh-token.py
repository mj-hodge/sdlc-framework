#!/usr/bin/env python3
"""
Refresh the Azure AD token in .mcp.json.

Uses MSAL Python with the same app registration as the dashboard.
Caches tokens so you only need to log in once — subsequent runs use
the refresh token silently.

Usage:
    python scripts/refresh-mcp-token.py          # interactive login (first time)
    python scripts/refresh-mcp-token.py --silent  # silent refresh only (for cron)

Cron (refresh every 45 minutes — Azure AD tokens expire after 1 hour):
    */45 * * * * cd /path/to/project && python3 scripts/refresh-mcp-token.py --silent
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import msal

# TODO: Set your Azure AD app registration values
TENANT_ID = "YOUR_TENANT_ID"
CLIENT_ID = "YOUR_CLIENT_ID"
# IMPORTANT: Use api:// scope, NOT User.Read — Graph tokens have nonce and JWKS can't verify them
SCOPES = ["api://YOUR_CLIENT_ID/user_impersonation"]

MCP_JSON = Path(".mcp.json")
CACHE_FILE = Path.home() / ".msal-mcp-cache.json"
# TODO: Set your server name (must match .mcp.json key)
SERVER_NAME = "my-server"


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if CACHE_FILE.exists():
        cache.deserialize(CACHE_FILE.read_text())
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        CACHE_FILE.write_text(cache.serialize())


def _get_app(cache: msal.SerializableTokenCache) -> msal.PublicClientApplication:
    return msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=cache,
    )


def _update_mcp_json(token: str) -> None:
    config = json.loads(MCP_JSON.read_text()) if MCP_JSON.exists() else {}
    servers = config.setdefault("mcpServers", {})
    server = servers.setdefault(SERVER_NAME, {})
    server["type"] = "http"
    server["url"] = "http://127.0.0.1:8000/mcp"
    server["headers"] = {"Authorization": f"Bearer {token}"}
    MCP_JSON.write_text(json.dumps(config, indent=2) + "\n")


def main():
    silent = "--silent" in sys.argv
    cache = _load_cache()
    app = _get_app(cache)

    accounts = app.get_accounts()
    result = None

    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if result and "access_token" in result:
        _update_mcp_json(result["access_token"])
        _save_cache(cache)
        print(f"Token refreshed silently for {accounts[0].get('username', '?')}")
        print(f"Updated {MCP_JSON}")
        return

    if silent:
        print("No cached token available. Run without --silent to log in interactively.")
        sys.exit(1)

    # Interactive login
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print("Failed to create device flow:", flow.get("error_description", ""))
        sys.exit(1)

    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        _update_mcp_json(result["access_token"])
        _save_cache(cache)
        name = result.get("id_token_claims", {}).get("name", "?")
        print(f"Token acquired for {name}")
        print(f"Updated {MCP_JSON}")
    else:
        print("Login failed:", result.get("error_description", ""))
        sys.exit(1)


if __name__ == "__main__":
    main()
