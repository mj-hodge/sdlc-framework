# Asana Integration

## Setup

### MCP Server (Claude Code)

Add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "asana": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-asana"],
      "env": {
        "ASANA_ACCESS_TOKEN": "<your-asana-pat>"
      }
    }
  }
}
```

### MCP Server (Codex CLI)

Codex uses `~/.codex/config.toml`. Add/update via command:
```bash
codex mcp add asana --env ASANA_ACCESS_TOKEN=<your-asana-pat> -- npx -y @anthropic-ai/mcp-server-asana
```

For Asana's hosted SSE endpoint:
```bash
codex mcp add asana --url https://mcp.asana.com/sse
```

**MCP Tools:** `asana_search_tasks`, `asana_create_task`, `asana_update_task`, `asana_get_projects`, `asana_get_tasks`

### API Token

Get a Personal Access Token at https://app.asana.com/0/developer-console

```bash
export ASANA_TOKEN="<your-asana-pat>"
```

### Permissions (Claude Code)

Add to `~/.claude/settings.json` under `permissions.allow`:
```json
"Bash(cai asana-api.sh *)",
"mcp__asana__*"
```

## Project Setup

Create an Asana project with these sections (exact names):
- **Backlog**
- **Ready**
- **In Progress**
- **Review** — agent finished, PR waiting for merge
- **UAT** — PR merged, feature flag ON in UAT, stakeholder testing
- **E2E Gate**
- **Done** — verified in production
- **Do Not Do**

Name the project to match the repo/directory name (e.g., `advertising-amazon`). No prefix needed.

## Epic Hierarchy

- **Epic parent task:** `EPIC: <name>` — top-level task in Asana
- **Story subtasks:** `[E-1] STORY-XXX: <name>` — subtasks of the epic, prefixed with epic delivery phase number
- **E2E gate stories:** `[E2E] STORY-XXX: <name>` — integration test stories between delivery phases
- Non-epic stories use the standard `STORY-XXX: <name>` format (no prefix, no parent)
- Epic stories completing their SDLC move to **E2E Gate** section (not Done) until the E2E gate story passes
- After E2E gate passes → batch-move stories to Done

## Commands

Use the `asana-api.sh` wrapper for all operations:

```bash
cai asana-api.sh get <task_gid>                      # Read task details
cai asana-api.sh update-name <task_gid> <name>        # Update task name
cai asana-api.sh update-notes <task_gid> <notes>      # Update task notes
cai asana-api.sh comment <task_gid> <text>            # Add comment to task
cai asana-api.sh move <task_gid> <section_gid>        # Move task to section
cai asana-api.sh complete <task_gid>                  # Mark task completed
cai asana-api.sh create <project_gid> <name> [notes]  # Create task
cai asana-api.sh find-project <name>                  # Find project GID by name
cai asana-api.sh find-section <project_gid> <name>    # Find section GID by name
cai asana-api.sh create-subtask <parent_gid> <name> [notes]  # Create subtask
cai asana-api.sh subtasks <task_gid>                  # List subtasks
cai asana-api.sh set-parent <task_gid> <parent_gid>   # Make task a subtask
```

### Wrapper Policy

- Use `cai asana-api.sh ...` for all Asana API helper operations
- Do NOT shell-wrap, pipe, redirect, use command substitution, or chain
- Run one Asana command at a time

### Long Text Arguments

For `update-notes` and `comment` with multi-line text, write to a temp file and pipe via stdin:

```bash
cat > /tmp/asana-notes.txt << 'NOTES'
Your multi-line notes here...
NOTES
cat /tmp/asana-notes.txt | cai asana-api.sh update-notes <task_gid> -
```

## Phase Progress Tracking

Every phase transition MUST update the Asana task notes with an SDLC Progress block showing completed/current/remaining phases. See `/next` skill for format.
