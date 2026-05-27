# Monday.com Integration

## Setup

### API Token

Generate at Monday.com → Admin → API → Personal API Tokens

```bash
export MONDAY_TOKEN="<your-api-token>"
```

### MCP Server (Claude Code)

If a Monday.com MCP server is available, add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "monday": {
      "command": "npx",
      "args": ["-y", "@mondaydotcomorg/monday-api-mcp"],
      "env": {
        "MONDAY_API_TOKEN": "<your-api-token>"
      }
    }
  }
}
```

### MCP Server (Codex CLI)

Codex uses `~/.codex/config.toml`. Add/update via command:
```bash
codex mcp add monday --env MONDAY_API_TOKEN=<your-api-token> -- npx -y @mondaydotcomorg/monday-api-mcp
```

### Permissions (Claude Code)

Add to `~/.claude/settings.json` under `permissions.allow`:
```json
"mcp__monday__*"
```

## Board Setup

Create a Monday.com board with these status labels (exact names):
- **Backlog**
- **Ready**
- **In Progress**
- **Review** — agent finished, PR waiting for merge
- **UAT** — PR merged, feature flag ON in UAT, stakeholder testing
- **E2E Gate**
- **Done** — verified in production
- **Do Not Do**

Name the board to match the repo/directory name (e.g., `advertising-amazon`). No prefix needed — boards are organized in a folder.

### Required Columns

| Column | Type | Purpose |
|--------|------|---------|
| Status | Status | Maps to SDLC sections (Backlog, Ready, etc.) |
| Assignee | People | Story claiming for multi-worker mode |
| Story ID | Text | `STORY-XXX` identifier |
| Phase | Text | Current SDLC phase |
| Scope | Dropdown | trivial / small / medium / large |

## Epic Hierarchy

Monday.com uses **groups** for epic organization:
- Create a group named `EPIC: <name>` for each epic
- Story items within the group: `[E-1] STORY-XXX: <name>`
- E2E gate items: `[E2E] STORY-XXX: <name>`
- Non-epic stories go in a default "Stories" group

## Commands

> **Contributing:** If you build a `monday-api.sh` wrapper, submit a PR to add it to `scripts/`. It should implement the same subcommand interface as `asana-api.sh`.

Until a wrapper exists, use the Monday.com API directly or via MCP tools:

### Task Operations (via Monday.com API v2)

```graphql
# Read item details
query { items(ids: [ITEM_ID]) { name, column_values { id, text } } }

# Create item
mutation { create_item(board_id: BOARD_ID, item_name: "STORY-XXX: name") { id } }

# Update status (move between sections)
mutation { change_column_value(board_id: BOARD_ID, item_id: ITEM_ID, column_id: "status", value: "{\"label\": \"In Progress\"}") { id } }

# Add update (comment)
mutation { create_update(item_id: ITEM_ID, body: "Phase X completed. Summary...") { id } }

# Assign person
mutation { change_column_value(board_id: BOARD_ID, item_id: ITEM_ID, column_id: "person", value: "{\"personsAndTeams\":[{\"id\":PERSON_ID,\"kind\":\"person\"}]}") { id } }
```

## Phase Progress Tracking

Every phase transition MUST update the item with an update (comment) showing SDLC progress — completed/current/remaining phases.

## Contributing

This tracker integration is community-maintained. To improve it:
1. Create `scripts/monday-api.sh` implementing the same interface as `scripts/asana-api.sh`
2. Test with a real Monday.com board
3. Submit a PR to the `sdlc-framework` repo
