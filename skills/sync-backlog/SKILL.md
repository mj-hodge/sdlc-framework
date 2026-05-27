---
name: sync-backlog
description: Sync active stories from Asana to local backlog.md file.
---

# Sync Backlog

Sync active stories from Asana to local `backlog.md` file.

## Prerequisites

- `ASANA_TOKEN` environment variable set
- Project has corresponding Asana project (`sdlc-<project-name>`)

> **Note:** Asana MCP tools (`asana_*`) are Claude Code specific. All CLIs must use the wrapper form: `cai asana-api.sh ...`.

## Steps

1. **Get Asana project** — Use `asana_get_projects` to find `sdlc-<project-name>`

2. **Get sections:**
   ```bash
   PROJECT_GID=$(cai asana-api.sh find-project "sdlc-<project-name>")
   cai asana-api.sh sections "$PROJECT_GID"
   ```

3. **Fetch stories** — Use `asana_get_tasks` to get all tasks from project

4. **Group by section:**
   - In Progress
   - Ready
   - Backlog (summary only)
   - **Skip "Do Not Do"** — these tasks are invisible to agents

5. **Read existing backlog.md** if present

6. **Update backlog.md:**
   - Add sync timestamp
   - Group by section
   - Include acceptance criteria for Ready/In Progress
   - Summary only for Backlog items

7. **Report changes** — List added, updated, removed stories

## Output

Updated `backlog.md` (template: `templates/backlog.md`)

Include a count-only line at the bottom: `*N tasks parked in Do Not Do*`

## Moving Stories Between Sections

To move a story to a different section:
```bash
# Find section GID
SECTION_GID=$(cai asana-api.sh find-section "$PROJECT_GID" "Ready")

# Move task
cai asana-api.sh move "<task_gid>" "$SECTION_GID"
```
