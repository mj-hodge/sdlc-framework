#!/bin/bash
# Auto-format files after Claude edits them.
# Receives tool input as JSON on stdin.
# Requires: ruff (Python), eslint/prettier (TypeScript/JS)

FILE_PATH=$(cat | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

case "$FILE_PATH" in
  *.py)
    if command -v ruff &>/dev/null; then
      ruff check --fix --quiet "$FILE_PATH" 2>/dev/null
      ruff format --quiet "$FILE_PATH" 2>/dev/null
    fi
    ;;
  *.ts|*.tsx|*.js|*.jsx)
    if command -v npx &>/dev/null; then
      npx prettier --write --log-level error "$FILE_PATH" 2>/dev/null
      npx eslint --fix --quiet "$FILE_PATH" 2>/dev/null
    fi
    ;;
esac

exit 0
