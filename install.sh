#!/bin/bash
# SDLC Framework Installer
# Usage: curl -fsSL <url> | bash
#
# Environment variables:
#   SDLC_REPO_URL  - Git repo URL (default: https://github.com/YOUR-ORG/sdlc-framework.git)
#   SDLC_NONINTERACTIVE - Set to 1 to skip interactive prompts (token setup skipped)

set -euo pipefail

SDLC_DIR="$HOME/.sdlc"
REPO_URL="${SDLC_REPO_URL:-https://github.com/YOUR-ORG/sdlc-framework.git}"

# --- Color support ---
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
  GREEN=$(tput setaf 2)
  RED=$(tput setaf 1)
  YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6)
  BOLD=$(tput bold)
  RESET=$(tput sgr0)
else
  GREEN="" RED="" YELLOW="" CYAN="" BOLD="" RESET=""
fi

info()  { echo "${GREEN}[+]${RESET} $*"; }
warn()  { echo "${YELLOW}[!]${RESET} $*"; }
error() { echo "${RED}[x]${RESET} $*"; }
prompt() { echo "${CYAN}[?]${RESET} $*"; }

# --- Prerequisites ---
if ! command -v git >/dev/null 2>&1; then
  error "git is required but not found. Install git and try again."
  exit 1
fi

# --- Clone or pull ---
if [ -d "$SDLC_DIR" ]; then
  info "Updating existing installation at $SDLC_DIR..."
  git -C "$SDLC_DIR" pull --ff-only
else
  info "Cloning SDLC framework to $SDLC_DIR..."
  git clone "$REPO_URL" "$SDLC_DIR"
fi

# --- Make CLI executable ---
chmod +x "$SDLC_DIR/bin/sdlc"
info "Made bin/sdlc executable"

# --- Add to PATH ---
add_to_path() {
  local rc_file="$1"
  local path_line='export PATH="$HOME/.sdlc/bin:$PATH"'

  if [ ! -f "$rc_file" ]; then
    return
  fi

  if grep -qF '.sdlc/bin' "$rc_file" 2>/dev/null; then
    info "PATH already configured in $(basename "$rc_file")"
  else
    echo "" >> "$rc_file"
    echo "# SDLC Framework" >> "$rc_file"
    echo "$path_line" >> "$rc_file"
    info "Added ~/.sdlc/bin to PATH in $(basename "$rc_file")"
  fi
}

# Detect shell and add to appropriate rc file
current_shell="$(basename "${SHELL:-/bin/bash}")"
case "$current_shell" in
  zsh)
    add_to_path "$HOME/.zshrc"
    ;;
  bash)
    add_to_path "$HOME/.bashrc"
    # Also handle .bash_profile on macOS where .bashrc may not be sourced by login shells
    if [ -f "$HOME/.bash_profile" ]; then
      add_to_path "$HOME/.bash_profile"
    fi
    ;;
  *)
    add_to_path "$HOME/.bashrc"
    add_to_path "$HOME/.zshrc"
    ;;
esac

# =============================================================================
# Token & Tool Setup (interactive)
# =============================================================================

# Skip interactive setup if non-interactive or stdin is not a terminal
if [ "${SDLC_NONINTERACTIVE:-0}" = "1" ] || [ ! -t 0 ]; then
  warn "Non-interactive mode — skipping token setup"
  warn "Run ${BOLD}sdlc setup-token${RESET} later to configure credentials"
else
  echo ""
  echo "${BOLD}=== Credential & Tool Setup ===${RESET}"
  echo ""
  echo "The SDLC framework integrates with a task tracker and AI coding tools."
  echo "Each team member needs their own personal API token."
  echo ""

  # --- Task Tracker Selection ---
  prompt "Which task tracker does your team use?"
  echo "  1) Asana"
  echo "  2) Monday.com"
  echo "  3) None / I'll set this up later"
  echo ""
  read -rp "  Choice [1-3]: " tracker_choice
  echo ""

  tracker_platform=""
  tracker_token_var=""
  tracker_token_url=""
  tracker_token=""

  case "${tracker_choice:-3}" in
    1)
      tracker_platform="asana"
      tracker_token_var="ASANA_TOKEN"
      tracker_token_url="https://app.asana.com/0/developer-console"
      ;;
    2)
      tracker_platform="monday"
      tracker_token_var="MONDAY_TOKEN"
      tracker_token_url="https://monday.com → Admin → Connections → API → Personal API Token"
      ;;
    3)
      info "Skipping tracker setup — run ${BOLD}sdlc setup-token${RESET} later"
      ;;
  esac

  if [ -n "$tracker_platform" ]; then
    echo "  Get your personal token from:"
    echo "  ${BOLD}${tracker_token_url}${RESET}"
    echo ""
    read -rsp "  Paste your ${tracker_platform} token (hidden): " tracker_token
    echo ""

    if [ -n "$tracker_token" ]; then
      # Write token to shell rc file
      rc_file="$HOME/.${current_shell}rc"
      if [ ! -f "$rc_file" ]; then
        rc_file="$HOME/.bashrc"
      fi

      # Remove any existing token line for this var, then append
      if grep -qF "export ${tracker_token_var}=" "$rc_file" 2>/dev/null; then
        # Use a temp file to avoid sed -i portability issues
        grep -vF "export ${tracker_token_var}=" "$rc_file" > "${rc_file}.sdlc-tmp"
        mv "${rc_file}.sdlc-tmp" "$rc_file"
      fi
      echo "export ${tracker_token_var}=\"${tracker_token}\"" >> "$rc_file"
      info "Saved ${tracker_token_var} to $(basename "$rc_file")"

      # Export for use in MCP config below
      export "${tracker_token_var}=${tracker_token}"
    else
      warn "No token entered — skipping. Run ${BOLD}sdlc setup-token${RESET} later"
    fi
  fi

  # --- AI Tool Selection ---
  echo ""
  prompt "Which AI coding tools do you use? (comma-separated, e.g. 1,2)"
  echo "  1) Claude Code"
  echo "  2) Gemini CLI"
  echo "  3) Codex CLI"
  echo "  4) Kiro"
  echo "  5) None / I'll set this up later"
  echo ""
  read -rp "  Choice: " tool_choices
  echo ""

  # Parse comma-separated choices
  setup_claude=false
  setup_gemini=false
  setup_codex=false
  setup_kiro=false

  IFS=',' read -ra choices <<< "${tool_choices:-5}"
  for choice in "${choices[@]}"; do
    choice="$(echo "$choice" | tr -d ' ')"
    case "$choice" in
      1) setup_claude=true ;;
      2) setup_gemini=true ;;
      3) setup_codex=true ;;
      4) setup_kiro=true ;;
    esac
  done

  # --- Helper: merge JSON into settings file ---
  # Uses jq if available, otherwise writes fresh config
  ensure_jq() {
    if ! command -v jq >/dev/null 2>&1; then
      warn "jq not found — writing config from scratch (existing settings will be preserved if possible)"
      return 1
    fi
    return 0
  }

  # --- Claude Code Setup ---
  if [ "$setup_claude" = true ]; then
    echo "${BOLD}--- Claude Code ---${RESET}"
    claude_settings_dir="$HOME/.claude"
    claude_settings="$claude_settings_dir/settings.json"
    mkdir -p "$claude_settings_dir"

    # Build MCP server config based on tracker
    if [ -n "$tracker_platform" ] && [ -n "${tracker_token:-}" ]; then
      if ensure_jq; then
        # Start with existing settings or empty object
        existing="{}"
        if [ -f "$claude_settings" ]; then
          existing=$(cat "$claude_settings")
        fi

        if [ "$tracker_platform" = "asana" ]; then
          updated=$(printf '%s' "$existing" | jq --arg token "$tracker_token" '
            .mcpServers.asana = {
              "command": "npx",
              "args": ["-y", "@anthropic-ai/mcp-server-asana"],
              "env": { "ASANA_ACCESS_TOKEN": $token }
            }
            | .permissions.allow = ((.permissions.allow // []) + [
              "Bash(cai asana-api.sh *)",
              "mcp__asana__*"
            ] | unique)
          ')
        elif [ "$tracker_platform" = "monday" ]; then
          updated=$(printf '%s' "$existing" | jq --arg token "$tracker_token" '
            .mcpServers.monday = {
              "command": "npx",
              "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
              "env": { "MONDAY_API_TOKEN": $token }
            }
            | .permissions.allow = ((.permissions.allow // []) + [
              "mcp__monday__*"
            ] | unique)
          ')
        fi

        printf '%s' "$updated" | jq '.' > "$claude_settings"
        info "Configured Claude Code MCP server for ${tracker_platform}"
        info "Updated permissions in ~/.claude/settings.json"
      else
        # No jq — write minimal config (only if file doesn't exist)
        if [ ! -f "$claude_settings" ]; then
          if [ "$tracker_platform" = "asana" ]; then
            cat > "$claude_settings" << CLAUDE_EOF
{
  "mcpServers": {
    "asana": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-asana"],
      "env": {
        "ASANA_ACCESS_TOKEN": "${tracker_token}"
      }
    }
  },
  "permissions": {
    "allow": [
      "Bash(cai asana-api.sh *)",
      "mcp__asana__*"
    ]
  }
}
CLAUDE_EOF
          elif [ "$tracker_platform" = "monday" ]; then
            cat > "$claude_settings" << CLAUDE_EOF
{
  "mcpServers": {
    "monday": {
      "command": "npx",
      "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
      "env": {
        "MONDAY_API_TOKEN": "${tracker_token}"
      }
    }
  },
  "permissions": {
    "allow": [
      "mcp__monday__*"
    ]
  }
}
CLAUDE_EOF
          fi
          info "Created ~/.claude/settings.json for ${tracker_platform}"
        else
          warn "~/.claude/settings.json exists and jq not available — manual merge needed"
          warn "See: ~/.sdlc/trackers/${tracker_platform}.md for config to add"
        fi
      fi
    else
      info "No tracker token — skipping Claude Code MCP config"
    fi
  fi

  # --- Gemini CLI Setup ---
  if [ "$setup_gemini" = true ]; then
    echo "${BOLD}--- Gemini CLI ---${RESET}"
    gemini_settings_dir="$HOME/.gemini"
    gemini_settings="$gemini_settings_dir/settings.json"
    mkdir -p "$gemini_settings_dir"

    if [ -n "$tracker_platform" ] && [ -n "${tracker_token:-}" ]; then
      if ensure_jq; then
        existing="{}"
        if [ -f "$gemini_settings" ]; then
          existing=$(cat "$gemini_settings")
        fi

        if [ "$tracker_platform" = "asana" ]; then
          updated=$(printf '%s' "$existing" | jq --arg token "$tracker_token" '
            .mcpServers.asana = {
              "command": "npx",
              "args": ["-y", "@anthropic-ai/mcp-server-asana"],
              "env": { "ASANA_ACCESS_TOKEN": $token }
            }
          ')
        elif [ "$tracker_platform" = "monday" ]; then
          updated=$(printf '%s' "$existing" | jq --arg token "$tracker_token" '
            .mcpServers.monday = {
              "command": "npx",
              "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
              "env": { "MONDAY_API_TOKEN": $token }
            }
          ')
        fi

        printf '%s' "$updated" | jq '.' > "$gemini_settings"
        info "Configured Gemini CLI MCP server for ${tracker_platform}"
      else
        if [ ! -f "$gemini_settings" ]; then
          if [ "$tracker_platform" = "asana" ]; then
            cat > "$gemini_settings" << GEMINI_EOF
{
  "mcpServers": {
    "asana": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-asana"],
      "env": {
        "ASANA_ACCESS_TOKEN": "${tracker_token}"
      }
    }
  }
}
GEMINI_EOF
          elif [ "$tracker_platform" = "monday" ]; then
            cat > "$gemini_settings" << GEMINI_EOF
{
  "mcpServers": {
    "monday": {
      "command": "npx",
      "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
      "env": {
        "MONDAY_API_TOKEN": "${tracker_token}"
      }
    }
  }
}
GEMINI_EOF
          fi
          info "Created ~/.gemini/settings.json for ${tracker_platform}"
        else
          warn "~/.gemini/settings.json exists and jq not available — manual merge needed"
        fi
      fi
    else
      info "No tracker token — skipping Gemini MCP config"
    fi
  fi

  # --- Codex CLI Setup ---
  if [ "$setup_codex" = true ]; then
    echo "${BOLD}--- Codex CLI ---${RESET}"
    mkdir -p "$HOME/.codex"

    if [ -n "$tracker_platform" ] && [ -n "${tracker_token:-}" ]; then
      if command -v codex >/dev/null 2>&1; then
        if [ "$tracker_platform" = "asana" ]; then
          codex mcp remove asana >/dev/null 2>&1 || true
          codex mcp add asana --env "ASANA_ACCESS_TOKEN=${tracker_token}" -- npx -y @anthropic-ai/mcp-server-asana
        elif [ "$tracker_platform" = "monday" ]; then
          codex mcp remove monday >/dev/null 2>&1 || true
          codex mcp add monday --env "MONDAY_API_TOKEN=${tracker_token}" -- npx -y @mondaydotcomorg/monday-api-mcp
        fi
        info "Configured Codex CLI MCP server for ${tracker_platform} (stored in ~/.codex/config.toml)"
      else
        warn "codex command not found — skipping Codex MCP auto-configuration"
        if [ "$tracker_platform" = "asana" ]; then
          echo "Run later: codex mcp add asana --env ASANA_ACCESS_TOKEN=<token> -- npx -y @anthropic-ai/mcp-server-asana"
        elif [ "$tracker_platform" = "monday" ]; then
          echo "Run later: codex mcp add monday --env MONDAY_API_TOKEN=<token> -- npx -y @mondaydotcomorg/monday-api-mcp"
        fi
      fi
    else
      info "No tracker token — skipping Codex MCP config"
    fi
  fi

  # --- Kiro Setup ---
  if [ "$setup_kiro" = true ]; then
    echo "${BOLD}--- Kiro ---${RESET}"
    kiro_settings_dir="$HOME/.kiro/settings"
    kiro_settings="$kiro_settings_dir/mcp.json"
    mkdir -p "$kiro_settings_dir"

    if [ -n "$tracker_platform" ] && [ -n "${tracker_token:-}" ]; then
      if ensure_jq; then
        existing='{"mcpServers":{}}'
        if [ -f "$kiro_settings" ]; then
          existing=$(cat "$kiro_settings")
        fi

        if [ "$tracker_platform" = "asana" ]; then
          updated=$(printf '%s' "$existing" | jq --arg token "$tracker_token" '
            .mcpServers.asana = {
              "command": "npx",
              "args": ["-y", "@anthropic-ai/mcp-server-asana"],
              "env": { "ASANA_ACCESS_TOKEN": $token },
              "disabled": false,
              "autoApprove": []
            }
          ')
        elif [ "$tracker_platform" = "monday" ]; then
          updated=$(printf '%s' "$existing" | jq --arg token "$tracker_token" '
            .mcpServers.monday = {
              "command": "npx",
              "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
              "env": { "MONDAY_API_TOKEN": $token },
              "disabled": false,
              "autoApprove": []
            }
          ')
        fi

        printf '%s' "$updated" | jq '.' > "$kiro_settings"
        info "Configured Kiro MCP server for ${tracker_platform} (${kiro_settings})"
      else
        if [ ! -f "$kiro_settings" ]; then
          if [ "$tracker_platform" = "asana" ]; then
            cat > "$kiro_settings" << KIRO_EOF
{
  "mcpServers": {
    "asana": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-asana"],
      "env": {
        "ASANA_ACCESS_TOKEN": "${tracker_token}"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
KIRO_EOF
          elif [ "$tracker_platform" = "monday" ]; then
            cat > "$kiro_settings" << KIRO_EOF
{
  "mcpServers": {
    "monday": {
      "command": "npx",
      "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
      "env": {
        "MONDAY_API_TOKEN": "${tracker_token}"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
KIRO_EOF
          fi
          info "Created ${kiro_settings} for ${tracker_platform}"
        else
          warn "${kiro_settings} exists and jq not available — manual merge needed"
        fi
      fi
    else
      info "No tracker token — skipping Kiro MCP config"
    fi
  fi
fi

# --- Done ---
echo ""
echo "${BOLD}SDLC Framework installed successfully!${RESET}"
echo ""
echo "Next steps:"
echo "  1. Restart your shell or run: ${BOLD}source ~/.${current_shell}rc${RESET}"
echo "  2. Initialize a project:     ${BOLD}cd /path/to/project && sdlc init${RESET}"
echo "  3. Check installation:       ${BOLD}sdlc doctor${RESET}"
echo ""
echo "To reconfigure tokens later:   ${BOLD}sdlc setup-token${RESET}"
echo "Run ${BOLD}sdlc help${RESET} for all available commands."
