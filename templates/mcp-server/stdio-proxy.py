#!/usr/bin/env python3
"""
Stdio-to-HTTP proxy for MCP — reads JSON-RPC from stdin, forwards to HTTP server with auth.

Template from SDLC framework. Handles token refresh automatically via `az` CLI.

Usage in .mcp.json:
    {
      "mcpServers": {
        "my-server": {
          "type": "stdio",
          "command": "python3",
          "args": ["/path/to/scripts/mcp-stdio-proxy"]
        }
      }
    }

Prerequisites:
    - `az login` (Azure CLI must be authenticated)
    - MCP server running at MCP_URL
"""
import json
import sys
import subprocess

# TODO: Set your server URL and Azure AD resource
MCP_URL = "http://localhost:8002/mcp"
AZURE_AD_RESOURCE = "api://YOUR_CLIENT_ID"


def get_token():
    """Get Azure AD token via az CLI (uses cached login, handles refresh internally)."""
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token",
             "--resource", AZURE_AD_RESOURCE,
             "--query", "accessToken", "-o", "tsv"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def main():
    import urllib.request

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # Get fresh token every request (az CLI caches internally, this is cheap)
        token = get_token()
        sys.stderr.write(f"[proxy] token={'yes' if token else 'NO'}\n")
        sys.stderr.flush()

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(MCP_URL, data=line.encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode()
                sys.stdout.write(body + "\n")
                sys.stdout.flush()
        except urllib.error.HTTPError as e:
            if e.code == 401:
                # Token expired mid-request, refresh and retry once
                token = get_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    req = urllib.request.Request(MCP_URL, data=line.encode(), headers=headers, method="POST")
                    try:
                        with urllib.request.urlopen(req, timeout=30) as resp:
                            body = resp.read().decode()
                            sys.stdout.write(body + "\n")
                            sys.stdout.flush()
                    except Exception:
                        error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "Auth retry failed"}}
                        sys.stdout.write(json.dumps(error) + "\n")
                        sys.stdout.flush()
                else:
                    error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "Auth failed. Run: az login"}}
                    sys.stdout.write(json.dumps(error) + "\n")
                    sys.stdout.flush()
            else:
                error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": f"HTTP {e.code}"}}
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
