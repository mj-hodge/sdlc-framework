# MCP Server Template

Starter files for building an MCP server with the proven patterns from the SDLC framework.

## Files

| File | Purpose | Copy to |
|------|---------|---------|
| `server.py` | FastMCP server with identity middleware, lifespan, health check | `src/server.py` |
| `helpers.py` | Auth helpers (get_user_id_from_context) | `src/auth/helpers.py` |
| `api_client.py` | Template API client with httpx, auto-pagination | `src/amazon/client.py` (rename) |
| `mcp.json.template` | Client config template | `.mcp.json` |
| `refresh-token.py` | Azure AD token refresh script | `scripts/refresh-mcp-token.py` |
| `stdio-proxy.py` | Stdio-to-HTTP proxy with per-request az CLI token refresh | `scripts/mcp-stdio-proxy` |
| `compose-mcp.yaml` | Docker Compose with Postgres, Redis, Prometheus, Grafana | `docker-compose.yml` |

## Key Patterns

1. **No MCP SDK auth** — ASGI middleware handles Bearer → user_id
2. **Module-level identity** — not contextvars (they don't propagate to tool handlers)
3. **Direct httpx** — no SDK wrappers, auto-pagination, graceful degradation
4. **Token refresh** — cron job every 45 min, stale token fallback in middleware
5. **Agent-friendly docstrings** — every tool describes when/how to use it
6. **Usage dashboard** — React SPA with audit logs, stats, config (see STORY-003 reference)
7. **Prometheus metrics** — instrument from day 1

## Quick Start

```bash
# Copy template files
cp ~/.sdlc/templates/mcp-server/server.py src/server.py
cp ~/.sdlc/templates/mcp-server/helpers.py src/auth/helpers.py
cp ~/.sdlc/templates/mcp-server/api_client.py src/clients/template.py
cp ~/.sdlc/templates/mcp-server/refresh-token.py scripts/refresh-mcp-token.py
cp ~/.sdlc/templates/mcp-server/compose-mcp.yaml docker-compose.yml
cp ~/.sdlc/templates/mcp-server/mcp.json.template .mcp.json

# Customize: server name, Azure AD tenant/client IDs, API endpoints
# Then: docker compose up -d
```

---

## Azure AD Auth — Critical Lessons

> From mcp-advertising-amazon (2026-03-17). These are easy to get wrong.

### 1. Use `api://` scopes, NOT Graph scopes

MSAL with `User.Read` returns a Microsoft Graph token. Graph tokens have a `nonce` in the JWT header — **JWKS cannot verify them**. They are opaque by design.

**Always register an Application ID URI and custom scope:**
```bash
az ad app update --id <CLIENT_ID> --identifier-uris "api://<CLIENT_ID>"
# Then add an oauth2PermissionScopes entry (e.g., "access_as_user")
# Pre-authorize the SPA client for the scope
```

```typescript
// CORRECT — token for our app, JWKS-verifiable
scopes: [`api://${CLIENT_ID}/access_as_user`, "openid", "profile"]

// WRONG — Graph token, nonce-signed, can't be verified
scopes: ["User.Read", "openid", "profile"]
```

### 2. Use `accessToken`, not `idToken`

```typescript
// CORRECT
return response.accessToken;

// WRONG — idToken has nonce-based signatures, JWKS rejects it
return response.idToken;
```

### 3. CSP must whitelist Azure AD

If you add a `Content-Security-Policy` header, MSAL.js will be blocked:

```
connect-src 'self' https://login.microsoftonline.com https://login.microsoft.com https://login.windows.net;
form-action 'self' https://login.microsoftonline.com https://login.microsoft.com https://login.windows.net;
```

### 4. MCP SDK `AccessToken` is Pydantic — can't set arbitrary attrs

```python
# WRONG — silently fails, .groups is never set
from mcp.server.auth.provider import AccessToken
t = AccessToken(token=token, client_id="x", scopes=["user"])
t.groups = ["admin"]  # raises "no field groups" — swallowed by except

# CORRECT — use a plain class
class _AzureADToken:
    def __init__(self, token, client_id, scopes, groups):
        self.token = token
        self.client_id = client_id
        self.scopes = scopes
        self.groups = groups
```

### 5. Azure AD `groups` claim uses GUIDs, not names

```python
# WRONG
ADMIN_GROUP = "Technology Team"
return ADMIN_GROUP in token.groups

# CORRECT
ADMIN_GROUP_ID = "080c315b-7bc8-42b9-a939-115ce6be0ce1"
return ADMIN_GROUP_ID in token.groups
```

### 6. Docker Compose must set Azure AD env vars

JWKS verification requires `AZURE_TENANT_ID`. Without it, the server falls back to unsafe base64 decode (no signature verification):

```yaml
environment:
  - AZURE_TENANT_ID=<your-tenant-id>
  - AZURE_CLIENT_ID=<your-client-id>
```

### 7. Every service needs `/health`

Docker healthchecks fail silently if the endpoint doesn't exist. The container stays `unhealthy` forever. Add to **every** FastAPI service:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 8. SPA redirect URIs must be type "SPA" in Azure AD

Register `http://localhost:8000/dashboard/` as **SPA** (not Web). Web type won't work with MSAL.js PKCE flow.

```bash
az ad app show --id <CLIENT_ID> --query "spa.redirectUris"
```

### 9. Claude Code stdio proxy — tokens per request, not cached

Claude Code's MCP client doesn't refresh Bearer tokens in `.mcp.json`. A static token expires after ~1 hour. Two solutions:

**Option A: Stdio proxy (preferred for CLI agents)**

Write a small Python script that reads JSON-RPC from stdin, fetches a fresh Azure AD token via `az account get-access-token` on **every request**, and forwards to the HTTP server. The `az` CLI caches tokens internally, so per-request calls are cheap (~10ms).

```json
// .mcp.json — stdio mode, no static token
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/scripts/mcp-stdio-proxy"]
    }
  }
}
```

Key: initial mcp-datalake version cached the token at proxy startup — this broke after 1 hour. Fix: call `az account get-access-token` per request (commit `eb5f0e3`).

**Option B: Login script with MSAL token cache**

Use `scripts/refresh-mcp-token.py` with a cron job every 45 min. Works but requires cron setup and has a window where the token is stale.

### 10. Exempt `/mcp` from auth middleware — self-auth inside the endpoint

Don't put the MCP JSON-RPC endpoint behind the auth middleware. Instead:
- Let `initialize` and `tools/list` work **without** a token (so clients can discover tools)
- Only require auth on `tools/call` (where actual data access happens)
- Do JWT validation inline in the endpoint handler

```python
# In create_app():
wrapped = AuthGuardrailMiddleware(
    wrapped,
    exempt_paths={"/mcp", "/mcp/"},  # Exempt from middleware
)

# In mcp_endpoint():
if method in ("initialize", "tools/list"):
    return result  # No auth needed
if method == "tools/call":
    # Validate JWT here
    token = auth_header[len("Bearer "):]
    claims = await validate_token(token=token, jwks_cache=jwks_cache)
```

This prevents OAuth discovery loops — clients that hit `/.well-known/` get 404 instead of 401.

### 11. Accept both v1 and v2 Azure AD token formats

Azure AD issues tokens with different issuer and audience formats depending on the app manifest version:

```python
# Audience: accept both formats
audience = [
    settings.azure_ad_client_id,                    # v2: raw GUID
    f"api://{settings.azure_ad_client_id}",         # v1: api:// prefix
]
# Issuer: accept both formats
issuer = [
    f"https://login.microsoftonline.com/{tid}/v2.0",  # v2
    f"https://sts.windows.net/{tid}/",                 # v1
]
```

### 12. SQL `ActiveDirectoryDefault` shares the Azure AD credential

Use `Authentication=ActiveDirectoryDefault` in SQL connection strings. This picks up:
- **Production:** Managed Identity (no secrets needed)
- **Dev:** `az login` credential (same as the server process)

No separate SQL credentials to manage — the Azure AD identity is the single auth source.

### Checklist for New MCP Server

- [ ] Application ID URI set (`api://<CLIENT_ID>`)
- [ ] Custom scope created and pre-authorized for SPA
- [ ] MSAL requests `api://<CLIENT_ID>/<scope>`, not `User.Read`
- [ ] Dashboard sends `accessToken`, not `idToken`
- [ ] CSP includes Azure AD origins in `connect-src` and `form-action`
- [ ] Dashboard auth token wrapper is a plain class (not Pydantic AccessToken)
- [ ] Admin group check uses GUID, not display name
- [ ] `AZURE_TENANT_ID` and `AZURE_CLIENT_ID` in docker-compose.yml
- [ ] Every service has `/health` endpoint
- [ ] SPA redirect URIs registered as type SPA
- [ ] `.mcp.json` template uses `oauth` field (not static `headers.Authorization`)
- [ ] Stdio proxy fetches token per-request (not cached at startup)
- [ ] `/mcp` endpoint exempt from auth middleware, self-validates on `tools/call`
- [ ] JWT validation accepts both v1 and v2 issuer/audience formats
- [ ] SQL uses `ActiveDirectoryDefault` (shares Azure AD credential)
