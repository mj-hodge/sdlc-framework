#!/bin/bash

# DEPRECATED: Use setup-project.sh instead
# This script forwards to setup-project.sh --update --all for backwards compatibility

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "⚠️  DEPRECATED: setup-project-links.sh is replaced by setup-project.sh"
echo ""
echo "  New usage:"
echo "    setup-project.sh --init --all     # First-time submodule setup"
echo "    setup-project.sh --update --all   # Pull latest + regenerate AI docs (CLAUDE/GEMINI/CODEX)"
echo ""
echo "Forwarding to: setup-project.sh --update --all"
echo ""

exec "$SCRIPT_DIR/setup-project.sh" --update --all
