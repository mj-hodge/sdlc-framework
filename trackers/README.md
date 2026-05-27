# Task Tracker Integration

The SDLC framework supports multiple task trackers. The tracker is configured in `config.yaml`:

```yaml
task_tracker:
  platform: asana       # asana, monday, linear, jira, custom
  project_prefix: sdlc  # prefix for project/board names
```

## Supported Trackers

| Tracker | Status | File |
|---------|--------|------|
| [Asana](asana.md) | Full support (MCP + shell wrapper) | `trackers/asana.md` |
| [Monday.com](monday.md) | Community template (needs wrapper) | `trackers/monday.md` |
| Linear | Not yet — PRs welcome | — |
| Jira | Not yet — PRs welcome | — |

## Required Board Structure

All trackers must have these columns/sections/statuses:

| Column | Purpose | Who Moves Here |
|--------|---------|----------------|
| **Backlog** | Specced but not prioritized | Phase 1 agent |
| **Ready** | Prioritized, available for agent to claim | Repository owner (product decision) |
| **In Progress** | Agent actively working (Phases 1-8b) | Agent at Phase 8 start |
| **Review** | Agent finished. PR open. Waiting for merge. | Agent at story completion |
| **UAT** | PR merged to main. Feature flag ON in UAT. Stakeholder testing. | Repository owner after merge + flag flip |
| **E2E Gate** | Epic stories waiting for integration tests | Agent (epic workflow only) |
| **Done** | Verified in production. Feature flag ON in prod. | Repository owner after production release |
| **Do Not Do** | Rejected/deferred (ignored by agents) | Repository owner |

## Adding a New Tracker

1. Create `trackers/<tracker-name>.md` with setup, commands, and board structure
2. Optionally create `scripts/<tracker>-api.sh` implementing the same interface as `scripts/asana-api.sh`
3. Submit a PR

### Required API Operations

Any tracker integration must support:
- **Create task** with name and description
- **Move task** between columns/statuses
- **Add comment** to a task
- **Read task** details (name, status, assignee)
- **List tasks** in a column/status
- **Assign task** to a worker
- **Create subtask** (for epic hierarchy)
