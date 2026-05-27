#!/bin/bash

# Setup script to distribute SDLC config via git submodules
# Usage:
#   setup-project.sh --init [--all | /path/to/project]    # First-time submodule setup
#   setup-project.sh --update [--all | /path/to/project]   # Pull latest + regenerate AI docs
#   setup-project.sh --deploy [--all | /path/to/project]   # Update + commit + push

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$(dirname "$SCRIPT_DIR")"
SUBMODULE_URL="${SDLC_SUBMODULE_URL:-https://github.com/YOUR-ORG/coding-ai-config.git}"
SUBMODULE_DIR=".sdlc"

usage() {
  echo "Usage:"
  echo "  $(basename "$0") --init [--all | /path/to/project]"
  echo "  $(basename "$0") --update [--all | /path/to/project]"
  echo "  $(basename "$0") --deploy [--all | /path/to/project]"
  echo ""
  echo "Options:"
  echo "  --init     First-time submodule setup (add submodule, symlinks, generate files)"
  echo "  --update   Pull latest submodule + regenerate CLAUDE.md/GEMINI.md/CODEX.md"
  echo "  --deploy   Update + commit + push (works even with dirty working trees)"
  echo "  --all      Apply to all projects in ~/projects/"
  exit 1
}

# --- File generation ---

generate_claude_md() {
  local project="$1"
  local project_name
  project_name=$(basename "$project")

  if [ -f "$project/CLAUDE.md" ]; then
    mv "$project/CLAUDE.md" "$project/CLAUDE.md.bak"
  fi

  cat > "$project/CLAUDE.md" << 'EOF'
# CLAUDE.md

> **DIRECTIVE:** This file contains critical guidance that MUST be followed for all work.
> After context compaction, re-read this file and `.project` to restore phase context.

---

## SDLC Process (REQUIRED)

See [AGENTS.md](./AGENTS.md) for: phase paths, advance categories, data mutation policy, skills, tech stack, writing rules, and git conventions.

**"spec" trigger:** Any prompt starting with "spec" MUST initiate Phase 1. Treat "spec ..." as equivalent to `/phase-1 ...`. When `multi_worker: true`, spec also auto-runs `/start-story` after Phase 1.

**Story switching (CRITICAL — NEVER auto-switch stories, even with auto-accept):**
`auto` advance means auto-advance to the next **phase within the same story**. It NEVER means switch to a different story/ticket. When a story is complete:
1. Output the completion summary
2. **STOP. END YOUR RESPONSE. Do NOT claim, start, or begin the next story.**
3. Wait for the user to explicitly tell you which story to work on next
4. This rule applies even if auto-accept is enabled — auto-accept controls phase transitions, NEVER story transitions

**Full phase details:** See [software-development-guidance.md](.sdlc/software-development-guidance.md)

---

## Deliverable Location (REQUIRED)

**All phase deliverables MUST be written to:** `features/<story-folder>/`

**Folder naming:** `features/story-XXX-kebab-case-slug/` where XXX is the story number and slug is derived from the Asana task name.

Example: `features/story-014-str-automations/seed.md`

**NEVER write deliverables to the project root or a `docs/` directory.** The `features/` directory is the single source of truth for all SDLC artifacts.

**Multi-worker mode:** When using worktrees, deliverables still go in `features/<story-folder>/` within the worktree.

---

## Phase Deliverables (REQUIRED — every phase MUST produce its file)

All files below are written to `features/<story-folder>/`:

| Phase | Output File(s) | Scope |
|-------|---------------|-------|
| 1 | `seed.md` | All |
| 2 | `research.md` | Large/New |
| 3 | `expansion.md` | Large/New |
| 4 | `analysis.md` | Medium+ |
| 5 | `selection.md` | Large/New |
| 6 | `feature-spec.md` (Medium) OR `specification.md`, `architecture.md`, `api-design.md`, `database-schema.md`, `implementation-plan.md` (Large/New) | Medium+ |
| 6b | `security-review.md` | Medium+ |
| 6c | `ux-review.md` | Medium+ |
| 7 | `test-design.md` + runnable test code in `tests/`/`e2e/` (RED state) | All |
| 8 | Implementation code (all tests GREEN) | All |
| 8b | `code-review.md` | Medium+ |
| 11 | `predeploy-gate.md` | Medium+ |
| 9 | `refinement-report.md` | Large/New |
| 10 | `site-reliability.md` | Large/New |

**Every phase MUST also update:** `.project`, `backlog.md`, `development-tasks.md`, Asana task (add comment summarizing work)

**A phase is NOT complete until its output file exists in `features/<story-folder>/` and tracking docs are updated.**

---

## Model Policy (CRITICAL)

| Phase | Model | Effort |
|-------|-------|--------|
| 1 (Seed) | Opus (always) | high |
| 2-5 | Sonnet (default), Opus for large/complex | medium |
| 6 (Design) | Opus (default), Sonnet ok for small | high |
| 7 (Test Design) | Sonnet (default) | medium |
| 8 (Implementation) | Sonnet (default), Opus requires approval | medium |
| 8b (Code Review) | Sonnet (default) | medium |
| 11 (Pre-Deploy Gate) | Sonnet (default) | medium |
| 9 (Refinement) | Opus (always) | high |
| 10 (Operations) | Opus (always) | high |

**Model Enforcement (HARD GATE — no exceptions):**
- Before starting ANY phase work, check: does your current model match the phase's required model?
- **Opus doing Sonnet work (e.g., Phase 8):** Delegate ALL work to Sonnet subagents. Opus orchestrates only. This prevents ~15x cost overrun.
- **Sonnet doing Opus work (e.g., Phase 1, 9, 10):** Delegate ALL work to an Opus subagent. Never ask the user to switch models.
- **config.yaml override:** If `models.opus_allowed: true`, Opus may do Sonnet-default phases directly.

---

## Context Management (CRITICAL)

- `/clear` between context groups, not every phase (default: `grouped` strategy)
- Use `/next` to auto-determine when `/clear` is needed
- Use subagents for research (Phases 2-3) — never pollute main context
- After 2 failed corrections, `/clear` and restart with a better prompt
- Commit after each logical unit in Phase 8
- Never implement more than one function/endpoint per prompt

**Context groups:** Seed | Research (2,3) | Evaluation (4,5) | Design (6,[6b,6c,6d]) | Test (7) | Implementation (8,8b) | Deploy (11) | Polish ([9,10])

**After `/clear` — "continue", "next step", or `/next`:**
1. Read `.project` → Phase Routing section to find current phase and status
2. Read the agent persona for that phase
3. Begin or resume the phase — no re-explanation needed

---

## Asana Integration (Claude-specific)

See [AGENTS.md](./AGENTS.md) § Asana Integration for wrapper policy, script commands, hierarchy, and general Asana rules.

**Claude-specific MCP Tools:** `asana_search_tasks`, `asana_create_task`, `asana_update_task`, `asana_get_projects`, `asana_get_tasks`

**Long text arguments (REQUIRED):** For `update-notes` and `comment` with multi-line text, write to a temp file then pipe via stdin with `-` as the text arg:
```bash
cat > /tmp/asana-comment.txt << 'COMMENT'
Phase X completed. Summary...
COMMENT
cat /tmp/asana-comment.txt | cai asana-api.sh comment <task_gid> -
```

---

## Git (Claude-specific)

See [AGENTS.md](./AGENTS.md) § Git for commit format and check-in commands.

**Worktree git commands (REQUIRED):** Always use `git -C <path>` instead of `cd <path> && git ...`. This avoids the compound-command approval prompt triggered by bare repository attack prevention.

---

## Reference

- [AGENTS.md](./AGENTS.md) — Canonical SDLC policy (phase paths, skills, tech stack, advance categories, Asana, git)
- [software-development-guidance.md](.sdlc/software-development-guidance.md) — Phase details, gates, hooks, lessons learned
- [templates/](.sdlc/templates/) — File and config templates
EOF
}

generate_gemini_md() {
  local project="$1"

  if [ -f "$project/GEMINI.md" ]; then
    mv "$project/GEMINI.md" "$project/GEMINI.md.bak"
  fi

  cat > "$project/GEMINI.md" << 'EOF'
# GEMINI.md

> **DIRECTIVE:** This file contains critical guidance that MUST be followed for all work.
> After context compaction, re-read this file and `.project` to restore phase context.
> Read and follow [AGENTS.md](./AGENTS.md) for complete development guidance.

---

## SDLC Process (REQUIRED)

See [AGENTS.md](./AGENTS.md) for: phase paths, advance categories, data mutation policy, skills, tech stack, writing rules, and git conventions.

**"spec" trigger:** Any prompt starting with "spec" MUST immediately initiate Phase 1 by activating the `phase-1` skill. Treat "spec" as a Directive to enter Phase 1.

**Story switching (CRITICAL — NEVER auto-switch stories, even with auto-accept):**
`auto` advance means auto-advance to the next **phase within the same story**. It NEVER means switch to a different story/ticket. When a story is complete:
1. Output the completion summary
2. **STOP. END YOUR RESPONSE. Do NOT claim, start, or begin the next story.**
3. Wait for the user to explicitly tell you which story to work on next
4. This rule applies even if auto-accept is enabled — auto-accept controls phase transitions, NEVER story transitions

**Full phase details:** See [software-development-guidance.md](.sdlc/software-development-guidance.md)

---

## Deliverable Location (REQUIRED)

**All phase deliverables MUST be written to:** `features/<story-folder>/`

**Folder naming:** `features/story-XXX-kebab-case-slug/` where XXX is the story number and slug is derived from the Asana task name.

**NEVER write deliverables to the project root or a `docs/` directory.**

---

## Phase Deliverables (REQUIRED — every phase MUST produce its file)

All files below are written to `features/<story-folder>/`:

| Phase | Output File(s) | Scope |
|-------|---------------|-------|
| 1 | `seed.md` | All |
| 2 | `research.md` | Large/New |
| 3 | `expansion.md` | Large/New |
| 4 | `analysis.md` | Medium+ |
| 5 | `selection.md` | Large/New |
| 6 | `feature-spec.md` (Medium) OR `specification.md`, `architecture.md`, `api-design.md`, `database-schema.md`, `implementation-plan.md` (Large/New) | Medium+ |
| 6b | `security-review.md` | Medium+ |
| 6c | `ux-review.md` | Medium+ |
| 7 | `test-design.md` + runnable test code in `tests/`/`e2e/` (RED state) | All |
| 8 | Implementation code (all tests GREEN) | All |
| 8b | `code-review.md` | Medium+ |
| 11 | `predeploy-gate.md` | Medium+ |
| 9 | `refinement-report.md` | Large/New |
| 10 | `site-reliability.md` | Large/New |

**Every phase MUST also update:** `.project`, `backlog.md`, `development-tasks.md`, Asana task (add comment summarizing work)

---

## Model Policy (Gemini-specific)

| Phase | Model | Effort |
|-------|-------|--------|
| 1 (Seed) | Pro (always) | high |
| 2-5 | Flash (default), Pro for large/complex | medium |
| 6 (Design) | Pro (default), Flash ok for small | high |
| 7 (Test Design) | Flash (default) | medium |
| 8 (Implementation) | Flash (default) | medium |
| 8b (Code Review) | Flash (default) | medium |
| 11 (Pre-Deploy Gate) | Flash (default) | medium |
| 9 (Refinement) | Pro (always) | high |
| 10 (Operations) | Pro (always) | high |

**Model Enforcement (HARD GATE — no exceptions):**
- Before starting ANY phase, check: does your current model match the phase's required model?
- **Pro doing Flash work (e.g., Phase 8):** Delegate ALL work to Flash. Pro orchestrates only.
- **Flash doing Pro work (e.g., Phase 1, 9, 10):** Delegate ALL work to a Pro sub-agent. Never ask the user to switch models.

---

## Context Management (CRITICAL)

- Clear context between context groups, not every phase (default: grouped strategy)
- Use separate searches for research (Phases 2-3) — don't pollute main context
- After 2 failed corrections, start a new session with a better prompt
- Commit after each logical unit in Phase 8

**Context groups:** Seed | Research (2,3) | Evaluation (4,5) | Design (6,[6b,6c,6d]) | Test (7) | Implementation (8,8b) | Deploy (11) | Polish ([9,10])

---

## Reference

- [AGENTS.md](./AGENTS.md) — Canonical SDLC policy (phase paths, skills, tech stack, Asana, git)
- [software-development-guidance.md](.sdlc/software-development-guidance.md) — Phase details, gates, hooks, lessons learned
- [templates/](.sdlc/templates/) — File and config templates
EOF
}

generate_codex_md() {
  local project="$1"

  if [ -f "$project/CODEX.md" ]; then
    mv "$project/CODEX.md" "$project/CODEX.md.bak"
  fi

  cat > "$project/CODEX.md" << 'EOF'
# CODEX.md

> **DIRECTIVE:** Follow [AGENTS.md](./AGENTS.md) as the primary SDLC policy.
> At session start and after context resets, re-read `AGENTS.md`, `config.yaml`, and `.project`.

---

## SDLC Process (Required)

- Treat prompts like "spec ..." as a Phase 1 start.
- Follow the scope path and phase gates defined in `AGENTS.md`.
- Read the phase persona from `.sdlc/agents/phase-X-*.md` before each phase.
- Produce required phase deliverables in `features/<story-folder>/`.
- Keep `.project`, `backlog.md`, `development-tasks.md`, and Asana synchronized at every transition.

## Execution Notes For Codex

- Codex does not rely on slash commands; execute the same workflow through plain-language directives.
- Treat `spec ...` and `/spec ...` as equivalent.
- Treat `next STORY-XXX` and `/next STORY-XXX` as equivalent.
- Codex MCP configuration lives in `~/.codex/config.toml` and should be managed via `codex mcp add ...` / `codex mcp list` (not `~/.codex/settings.json`).
- Use `skills/*/SKILL.md` as procedural references when a phase or workflow is requested.
- For platform-specific behavior, prefer:
  - `.sdlc/skills/next/codex.md`
  - `.sdlc/skills/spec/codex.md`
- For phase advancement, follow the same `advance` semantics (`gate`, `confirm`, `auto`) from agent personas.
- Respect model-tier gates in `AGENTS.md` and `config.yaml`.

## Required Files

`AGENTS.md` | `config.yaml` | `.project` | `backlog.md` | `development-tasks.md`

## References

- [AGENTS.md](./AGENTS.md)
- [software-development-guidance.md](.sdlc/software-development-guidance.md)
- [agents/README.md](.sdlc/agents/README.md)
- [skills/](.sdlc/skills/)
EOF
}

link_skills() {
  local project="$1"
  mkdir -p "$project/.claude"
  mkdir -p "$project/.gemini"
  mkdir -p "$project/.codex"

  # Link for Claude
  if [ -L "$project/.claude/skills" ]; then
    rm "$project/.claude/skills"
  fi
  ln -s "../$SUBMODULE_DIR/skills" "$project/.claude/skills"
  echo "  ✓ .claude/skills → ../$SUBMODULE_DIR/skills"

  # Link for Gemini
  if [ -L "$project/.gemini/skills" ]; then
    rm "$project/.gemini/skills"
  fi
  ln -s "../$SUBMODULE_DIR/skills" "$project/.gemini/skills"
  echo "  ✓ .gemini/skills → ../$SUBMODULE_DIR/skills"

  # Link for Codex
  if [ -L "$project/.codex/skills" ]; then
    rm "$project/.codex/skills"
  fi
  ln -s "../$SUBMODULE_DIR/skills" "$project/.codex/skills"
  echo "  ✓ .codex/skills → ../$SUBMODULE_DIR/skills"
}

generate_gemini_ignore() {
  local project="$1"
  if [ -f "$project/.gitignore" ]; then
    cp "$project/.gitignore" "$project/.geminiignore"
    echo "  ✓ .geminiignore (generated from .gitignore)"
  fi
}

generate_claude_settings() {
  local project="$1"
  local settings_file="$project/.claude/settings.json"

  # Read task_tracker.platform from config.yaml if it exists
  local platform=""
  if [ -f "$project/config.yaml" ]; then
    # Extract platform with grep (no jq/yq dependency)
    platform=$(grep -A1 'task_tracker:' "$project/config.yaml" | grep 'platform:' | sed 's/.*platform:\s*//' | tr -d '[:space:]' | cut -d'#' -f1)
  fi

  # Default to monday if no config.yaml yet
  platform="${platform:-monday}"

  mkdir -p "$project/.claude"

  # Build MCP servers block based on platform
  local mcp_block=""
  local permissions=""

  if [ "$platform" = "asana" ]; then
    mcp_block='"asana": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-asana"],
      "env": {
        "ASANA_ACCESS_TOKEN": "${ASANA_ACCESS_TOKEN}"
      }
    }'
    permissions='"Bash(cai asana-api.sh *)", "mcp__asana__*"'
  elif [ "$platform" = "monday" ]; then
    mcp_block='"monday": {
      "command": "npx",
      "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
      "env": {
        "MONDAY_API_TOKEN": "${MONDAY_API_TOKEN}"
      }
    }'
    permissions='"mcp__monday__*"'
  fi

  cat > "$settings_file" << SETTINGS_EOF
{
  "mcpServers": {
    ${mcp_block}
  },
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(sdlc *)",
      "Bash(cai *)",
      ${permissions}
    ]
  }
}
SETTINGS_EOF

  echo "  ✓ .claude/settings.json (generated for ${platform})"
}

generate_gemini_settings() {
  local project="$1"
  local settings_file="$project/.gemini/settings.json"

  local platform=""
  if [ -f "$project/config.yaml" ]; then
    platform=$(grep -A1 'task_tracker:' "$project/config.yaml" | grep 'platform:' | sed 's/.*platform:\s*//' | tr -d '[:space:]' | cut -d'#' -f1)
  fi

  platform="${platform:-monday}"

  mkdir -p "$project/.gemini"

  local mcp_block=""

  if [ "$platform" = "asana" ]; then
    mcp_block='"asana": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-asana"],
      "env": {
        "ASANA_ACCESS_TOKEN": "${ASANA_ACCESS_TOKEN}"
      }
    }'
  elif [ "$platform" = "monday" ]; then
    mcp_block='"monday": {
      "command": "npx",
      "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
      "env": {
        "MONDAY_API_TOKEN": "${MONDAY_API_TOKEN}"
      }
    }'
  fi

  cat > "$settings_file" << SETTINGS_EOF
{
  "mcpServers": {
    ${mcp_block}
  }
}
SETTINGS_EOF

  echo "  ✓ .gemini/settings.json (generated for ${platform})"
}

cleanup_bak_files() {
  local project="$1"
  rm -f "$project/CLAUDE.md.bak" "$project/GEMINI.md.bak" "$project/CODEX.md.bak" "$project/AGENTS.md.bak"
}

# --- Modes ---

init_project() {
  local project="$1"
  local project_name
  project_name=$(basename "$project")

  # Skip non-git directories
  if [ ! -d "$project/.git" ]; then
    echo "⊘ $project_name (not a git repo, skipping)"
    return
  fi

  echo "→ $project_name"

  # Remove old absolute AGENTS.md symlink if present
  if [ -L "$project/AGENTS.md" ]; then
    rm "$project/AGENTS.md"
    echo "  ✓ Removed old AGENTS.md symlink"
  elif [ -f "$project/AGENTS.md" ]; then
    mv "$project/AGENTS.md" "$project/AGENTS.md.bak"
    echo "  ✓ Backed up existing AGENTS.md"
  fi

  # Add git submodule (skip if already exists)
  if [ -d "$project/$SUBMODULE_DIR" ]; then
    echo "  ✓ $SUBMODULE_DIR submodule already exists"
  else
    (cd "$project" && git submodule add "$SUBMODULE_URL" "$SUBMODULE_DIR")
    echo "  ✓ Added $SUBMODULE_DIR submodule"
  fi

  # Create relative symlink for AGENTS.md
  ln -sf "$SUBMODULE_DIR/AGENTS.md" "$project/AGENTS.md"
  echo "  ✓ AGENTS.md → $SUBMODULE_DIR/AGENTS.md"

  # Generate CLAUDE.md, GEMINI.md, and CODEX.md
  generate_claude_md "$project"
  echo "  ✓ CLAUDE.md (generated)"
  generate_gemini_md "$project"
  echo "  ✓ GEMINI.md (generated)"
  generate_codex_md "$project"
  echo "  ✓ CODEX.md (generated)"

  # Generate .geminiignore
  generate_gemini_ignore "$project"

  # Link skills
  link_skills "$project"

  # Generate project-level AI tool settings
  generate_claude_settings "$project"
  generate_gemini_settings "$project"

  # Copy dependabot config
  mkdir -p "$project/.github"
  cp "$SCRIPT_DIR/templates/dependabot.yml" "$project/.github/dependabot.yml"
  echo "  ✓ .github/dependabot.yml (copied)"

  # Clean up .bak files
  cleanup_bak_files "$project"

  echo "  ✓ Done"
  echo ""
}

update_project() {
  local project="$1"
  local project_name
  project_name=$(basename "$project")

  # Skip if no submodule
  if [ ! -d "$project/$SUBMODULE_DIR" ]; then
    echo "⊘ $project_name (no $SUBMODULE_DIR submodule, skipping — use --init first)"
    return
  fi

  echo "→ $project_name"

  # Update submodule to latest
  (cd "$project" && git submodule update --remote "$SUBMODULE_DIR")
  echo "  ✓ $SUBMODULE_DIR updated to latest"

  # Regenerate CLAUDE.md, GEMINI.md, and CODEX.md
  generate_claude_md "$project"
  echo "  ✓ CLAUDE.md (regenerated)"
  generate_gemini_md "$project"
  echo "  ✓ GEMINI.md (regenerated)"
  generate_codex_md "$project"
  echo "  ✓ CODEX.md (regenerated)"

  # Fix skills symlink if needed
  link_skills "$project"

  # Generate project-level AI tool settings
  generate_claude_settings "$project"
  generate_gemini_settings "$project"

  # Clean up .bak files
  cleanup_bak_files "$project"

  echo "  ✓ Done"
  echo ""
}

deploy_project() {
  local project="$1"
  local project_name
  project_name=$(basename "$project")

  # Skip if no submodule
  if [ ! -d "$project/$SUBMODULE_DIR" ]; then
    echo "⊘ $project_name (no $SUBMODULE_DIR submodule, skipping — use --init first)"
    return
  fi

  # Run update first
  update_project "$project"

  # Check if there are actually changes to commit
  if (cd "$project" && git diff --quiet HEAD -- .sdlc CLAUDE.md GEMINI.md CODEX.md .claude/settings.json .gemini/settings.json 2>/dev/null); then
    echo "  ✓ No changes to deploy"
    return
  fi

  # Commit and push
  (cd "$project" && git add .sdlc CLAUDE.md GEMINI.md CODEX.md .claude/settings.json .gemini/settings.json && git commit -m "sdlc: update submodule to latest" && git push)
  echo "  ✓ Committed and pushed"
  echo ""
}

iterate_all() {
  local mode="$1"
  local count=0

  for project in "$PROJECTS_DIR"/*/; do
    project_name=$(basename "$project")

    # Skip coding-ai-config itself
    [ "$project_name" = "coding-ai-config" ] && continue
    # Skip archive
    [ "$project_name" = "archive" ] && continue

    case "$mode" in
      init)   init_project "$project" ;;
      update) update_project "$project" ;;
      deploy) deploy_project "$project" ;;
    esac
    ((count++))
  done

  echo "Processed $count projects."
}

# --- Main ---

if [ $# -lt 1 ]; then
  usage
fi

MODE=""
TARGET=""

while [ $# -gt 0 ]; do
  case "$1" in
    --init)   MODE="init"; shift ;;
    --update) MODE="update"; shift ;;
    --deploy) MODE="deploy"; shift ;;
    --all)    TARGET="all"; shift ;;
    -h|--help) usage ;;
    *)
      if [ -z "$TARGET" ]; then
        TARGET="$1"
      else
        echo "Error: unexpected argument '$1'"
        usage
      fi
      shift
      ;;
  esac
done

if [ -z "$MODE" ]; then
  echo "Error: must specify --init, --update, or --deploy"
  usage
fi

echo "SDLC Distribution — ${MODE} mode"
echo "Source: $SCRIPT_DIR"
echo ""

if [ "$TARGET" = "all" ]; then
  iterate_all "$MODE"
elif [ -n "$TARGET" ]; then
  # Resolve to absolute path
  TARGET="$(cd "$TARGET" 2>/dev/null && pwd)" || { echo "Error: '$TARGET' not found"; exit 1; }
  case "$MODE" in
    init)   init_project "$TARGET" ;;
    update) update_project "$TARGET" ;;
    deploy) deploy_project "$TARGET" ;;
  esac
else
  echo "Error: must specify --all or a project path"
  usage
fi
