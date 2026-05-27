"""
MCP server entry point — FastMCP with ASGI identity middleware.

Template from SDLC framework. Customize tool registrations and lifespan deps.

Auth strategy:
  - NO MCP SDK auth (no auth=AuthSettings, no _token_verifier)
  - ASGI _IdentityMiddleware resolves Bearer → user_id
  - Never returns 401 (prevents client OAuth discovery)
  - Identity stored in module-level var (not contextvars)
"""

from __future__ import annotations

try:
    from mcp.server.fastmcp import FastMCP
    from contextlib import asynccontextmanager
    from src.config import settings
    from src.auth.helpers import set_current_user_id

    # ---------------------------------------------------------------------------
    # Lifespan — create/close shared resources
    # ---------------------------------------------------------------------------

    @asynccontextmanager
    async def _lifespan(server: FastMCP):
        """Set up shared resources for server lifetime."""
        import httpx

        http_client = httpx.AsyncClient()

        # TODO: Add your resource initialization here
        # - Database session factory
        # - Redis client
        # - Rate limiter
        # - API client dependencies

        try:
            yield
        finally:
            await http_client.aclose()
            # TODO: Close other resources

    # ---------------------------------------------------------------------------
    # FastMCP instance — NO auth= or token_verifier
    # ---------------------------------------------------------------------------

    mcp = FastMCP(
        "my-server",  # TODO: Change to your server name
        stateless_http=True,
        lifespan=_lifespan,
    )

    # ---------------------------------------------------------------------------
    # Tool registration
    # ---------------------------------------------------------------------------

    @mcp.tool()
    async def health_check() -> dict:
        """Check server health: database connectivity, external service status.

        Use this tool to verify the server is operational before making
        other calls. Returns status for each dependency.

        Returns:
            {status: "healthy"|"degraded", db_status: str, ...}
        """
        return {"status": "healthy"}

    # TODO: Register your tools here. Each tool MUST have a detailed docstring:
    #
    # @mcp.tool()
    # async def my_tool(param1: str, param2: int = 10) -> dict:
    #     \"\"\"Short description of what this tool does in business terms.
    #
    #     Use this tool when you need to [specific use case]. For [alternative
    #     use case], use [other_tool] instead.
    #
    #     Args:
    #         param1: Description with example (e.g., "profile_123")
    #         param2: Description with default explained
    #
    #     Returns:
    #         {key1: "description", key2: [{nested: "shape"}], total_count: int}
    #
    #     Common patterns:
    #         - Filter by status: my_tool("id", status="active")
    #         - Get first page: my_tool("id", limit=10)
    #     \"\"\"
    #     user_id = get_user_id_from_context()  # Per-request auth check
    #     ...

    # ---------------------------------------------------------------------------
    # ASGI app with identity middleware
    # ---------------------------------------------------------------------------

    _raw_app = mcp.streamable_http_app()

    # Public health endpoint (no auth)
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    @_raw_app.route("/healthz", methods=["GET"])
    async def healthz(request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    # TODO: Mount dashboard, metrics, etc.
    # _raw_app.mount("/api", dashboard_router)
    # _raw_app.mount("/metrics", metrics_app)

    # ---------------------------------------------------------------------------
    # Security headers — CSP must whitelist Azure AD for MSAL.js
    # ---------------------------------------------------------------------------

    _AZURE_AD_ORIGINS = (
        "https://login.microsoftonline.com "
        "https://login.microsoft.com "
        "https://login.windows.net"
    )

    class _SecurityHeadersMiddleware:
        """Adds CSP, HSTS, X-Frame-Options to all HTTP responses."""
        _CSP_POLICY = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            f"connect-src 'self' {_AZURE_AD_ORIGINS}; "
            "object-src 'none'; "
            "base-uri 'self'; "
            f"form-action 'self' {_AZURE_AD_ORIGINS}; "
            "frame-ancestors 'none'"
        )

        def __init__(self, inner_app):
            self._app = inner_app

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                return await self._app(scope, receive, send)

            async def send_with_headers(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"content-security-policy", self._CSP_POLICY.encode()))
                    headers.append((b"x-content-type-options", b"nosniff"))
                    headers.append((b"x-frame-options", b"DENY"))
                    message = {**message, "headers": headers}
                await send(message)

            return await self._app(scope, receive, send_with_headers)

    # ---------------------------------------------------------------------------
    # Identity middleware — MUST wrap LAST after all mounts
    # ---------------------------------------------------------------------------

    class _IdentityMiddleware:
        """Resolves Bearer token → user_id. Never returns 401.

        Tries Azure AD JWT first, then API key fallback.
        Stores user_id in module-level var for tool handlers.
        Falls back to .mcp.json token when client sends stale cached token.
        """
        def __init__(self, inner_app):
            self._app = inner_app

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                return await self._app(scope, receive, send)

            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            user_id = None

            if auth_header.startswith("Bearer "):
                token = auth_header[len("Bearer "):]
                user_id = await self._resolve_identity(token)

            set_current_user_id(user_id)
            try:
                return await self._app(scope, receive, send)
            finally:
                set_current_user_id(None)

        async def _resolve_identity(self, token: str) -> int | None:
            """Resolve Bearer token to user_id. Returns None on failure."""
            # Try Azure AD JWT (tokens contain dots)
            if "." in token:
                try:
                    from src.auth.azure_ad import verify_azure_token
                    claims = verify_azure_token(
                        token,
                        expected_audience=settings.azure_client_id,
                    )
                    email = claims.get("preferred_username", "")
                    if email:
                        return await self._lookup_user_by_email(email)
                except ValueError:
                    # Token expired — try fresh from .mcp.json
                    try:
                        import json
                        fresh = json.load(open("/app/.mcp.json"))
                        fresh_token = fresh["mcpServers"][list(fresh["mcpServers"].keys())[0]]["headers"]["Authorization"].split(" ")[1]
                        claims = verify_azure_token(fresh_token, expected_audience=settings.azure_client_id)
                        email = claims.get("preferred_username", "")
                        if email:
                            return await self._lookup_user_by_email(email)
                    except Exception:
                        pass
                except Exception:
                    pass

            # TODO: Add API key fallback if needed
            return None

        async def _lookup_user_by_email(self, email: str) -> int | None:
            """Look up user_id by email in the users table."""
            try:
                from src.database import async_session
                from sqlalchemy import text
                async with async_session() as session:
                    result = await session.execute(
                        text("SELECT id FROM users WHERE email = :email AND is_active = true"),
                        {"email": email},
                    )
                    row = result.mappings().first()
                    return int(row["id"]) if row else None
            except Exception:
                return None

    # Wrap: SecurityHeaders → IdentityMiddleware → app
    app = _SecurityHeadersMiddleware(_IdentityMiddleware(_raw_app))

except ImportError:
    class _MissingDepsApp:
        async def __call__(self, scope, receive, send):
            raise ImportError("Server dependencies not installed.")

    app = _MissingDepsApp()
