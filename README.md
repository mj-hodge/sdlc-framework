# coding-ai-config

SDLC framework for AI-assisted software development. Distributes agent personas, phase skills, and project templates via a lightweight CLI.

---

## What's Included

| Directory | Purpose |
|-----------|---------|
| `agents/` | Phase agent personas (phase-1 through phase-10, plus sub-agents) |
| `skills/` | Slash command skills (`/spec`, `/next`, `/phase-N`, etc.) |
| `templates/` | Project scaffolding (`config.yaml`, `project.md`) |
| `trackers/` | Task tracker integration guides (Asana, Monday.com, etc.) |
| `scripts/` | Task tracker API helpers |
| `bin/sdlc` | CLI tool for setup, updates, and project management |

---

## Quick Start

### 1. Install (once per machine)

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR-ORG/sdlc-framework/main/install.sh | bash
```

This clones the framework to `~/.sdlc/` and adds `sdlc` to your PATH.

### 2. Set up a project

```bash
cd /path/to/your-project
sdlc init
```

This creates:

| File | Type | Purpose |
|------|------|---------|
| `CLAUDE.md` | Generated (committed) | Claude Code instructions |
| `GEMINI.md` | Generated (committed) | Gemini CLI instructions |
| `CODEX.md` | Generated (committed) | Codex CLI instructions |
| `config.yaml` | Template (committed) | Project-specific settings |
| `.project` | Template (committed) | Project state tracking |
| `AGENTS.md` | Symlink (gitignored) | → `~/.sdlc/AGENTS.md` |
| `.claude/skills/` | Symlink (gitignored) | → `~/.sdlc/skills/` |
| `.gemini/skills/` | Symlink (gitignored) | → `~/.sdlc/skills/` |
| `.codex/skills/` | Symlink (gitignored) | → `~/.sdlc/skills/` |

### 3. Configure your project

Edit `config.yaml`:
```yaml
project:
  name: my-app
  scope: medium

task_tracker:
  platform: asana       # asana, monday, linear, jira, custom
  project_prefix: sdlc

tech_stack:
  backend: python/fastapi
  frontend: react/vite
  database: postgresql
```

### 4. Commit

```bash
git add CLAUDE.md GEMINI.md CODEX.md config.yaml .project .gitignore
git commit -m "sdlc: add AI development framework"
```

Only 5 files committed — everything else is symlinked from `~/.sdlc/`.

---

## Updating the Framework

```bash
sdlc update
```

Pulls the latest `~/.sdlc/`. Since agent personas, skills, and guidance docs are symlinked, **every project gets the update instantly** — no commits, no PRs, no deploy step.

To also regenerate the AI instruction files:
```bash
sdlc update --regenerate
```

---

## New Dev Joining an Existing Project

```bash
# 1. Install the framework (one-liner)
curl -fsSL https://raw.githubusercontent.com/YOUR-ORG/sdlc-framework/main/install.sh | bash
source ~/.zshrc  # or restart shell

# 2. Clone the project
git clone <repo-url>
cd <project>

# 3. Set up symlinks (the 5 committed files are already there from git)
sdlc init
```

---

## Task Tracker

The framework supports multiple task trackers. Set your tracker in `config.yaml`:

```yaml
task_tracker:
  platform: monday      # asana, monday, linear, jira, custom
  project_prefix: sdlc
```

Tracker-specific setup guides live in `~/.sdlc/trackers/`:

| Tracker | Guide | Status |
|---------|-------|--------|
| Asana | `trackers/asana.md` | Full support (MCP + shell wrapper) |
| Monday.com | `trackers/monday.md` | Template (needs API wrapper) |
| Linear | — | PRs welcome |
| Jira | — | PRs welcome |

### Required Board Structure (all trackers)

| Column | Purpose |
|--------|---------|
| **Backlog** | Unrefined ideas and future work |
| **Ready** | Scoped and ready for an agent to pick up |
| **In Progress** | Currently being worked on |
| **E2E Gate** | Epic stories waiting for integration tests |
| **Done** | Completed work |
| **Do Not Do** | Rejected/deferred (ignored by agents) |

### Adding a New Tracker

1. Create `trackers/<tracker>.md` with setup, commands, and board mapping
2. Optionally create `scripts/<tracker>-api.sh` (same interface as `asana-api.sh`)
3. Submit a PR

---

## CLI Reference

```bash
sdlc init [path]          # Set up a project (default: current dir)
sdlc update               # Pull latest framework
sdlc update --regenerate  # Pull + regenerate CLAUDE.md/GEMINI.md/CODEX.md
sdlc regenerate           # Regenerate AI config files from latest templates
sdlc doctor               # Check installation and project health
sdlc distribute [org]     # Create clean copy for sharing
sdlc version              # Print version
sdlc help                 # Show all commands
```

---

## Per-Developer Setup

Each developer needs to configure their local AI tool permissions.

### Claude Code

Add to `~/.claude/settings.json` under `permissions.allow`:
```json
[
  "Bash(git *)",
  "Bash(python *)",
  "Bash(pytest *)",
  "Bash(npm *)",
  "Bash(npx *)",
  "Bash(node *)",
  "Bash(docker *)",
  "Bash(docker-compose *)",
  "Bash(playwright *)"
]
```

Add tracker-specific permissions:
```json
"Bash(cai asana-api.sh *)", "mcp__asana__*"
// or
"mcp__monday__*"
```

### Gemini CLI

Add to `~/.gemini/settings.json`:
```json
{
  "defaultApprovalMode": "auto_edit",
  "tools": {
    "allowed": [
      "run_shell_command(git *)",
      "run_shell_command(python *)",
      "run_shell_command(pytest *)",
      "run_shell_command(npm *)",
      "run_shell_command(npx *)",
      "run_shell_command(node *)",
      "run_shell_command(docker *)",
      "run_shell_command(docker-compose *)",
      "run_shell_command(playwright *)"
    ]
  }
}
```

### Codex CLI

Codex stores MCP/server config in `~/.codex/config.toml` (not `settings.json`).

Configure tracker MCP servers with:
```bash
# Asana
codex mcp add asana --env ASANA_ACCESS_TOKEN=<your-asana-pat> -- npx -y @anthropic-ai/mcp-server-asana

# Monday.com
codex mcp add monday --env MONDAY_API_TOKEN=<your-monday-token> -- npx -y @mondaydotcomorg/monday-api-mcp
```

For SSE servers, use:
```bash
codex mcp add asana --url https://mcp.asana.com/sse
```

### Permission Security Notes

Global permissions apply to **every project** on your machine. Recommendations:
- **Start with project-level permissions** (`.claude/settings.json` in the project root) to limit blast radius
- Move to global only after the team is comfortable with agent behavior
- Use read-only API tokens for task trackers during evaluation

---

## Customization

### Tech Stack

Edit `config.yaml` → `tech_stack`. Agents read this at runtime. To change the hardcoded defaults in generated docs, run `sdlc regenerate` after modifying the templates in `~/.sdlc/bin/sdlc`.

### Skipping Phases

```yaml
phases:
  skip: [2, 3]  # Skip Research and Expansion
```

### Model Overrides

```yaml
models:
  opus_allowed: true  # Allow Opus for all phases (higher cost)
```

---

## How the SDLC Works

Every feature follows a scope-based phase path:

| Scope | Phase Path |
|-------|-----------|
| Trivial | 8 (just implement) |
| Small | 1 → 7 → 8 |
| Medium | 1 → 4 → 6 → 6b → 6c → 7 → 8 → 8b |
| Large | 1 → 2 → 3 → 4 → 5 → 6 → 6b → 6c → 7 → 8 → 8b → 9 → 10 |

| Phase | Name | What It Does |
|-------|------|-------------|
| 1 | Seed | Business requirements, acceptance criteria, scope classification |
| 2 | Research | Market research, library discovery, prior art |
| 3 | Expansion | Alternative approaches from multiple perspectives |
| 4 | Analysis | Technical, business, and risk evaluation |
| 5 | Selection | Choose the approach, justify the decision |
| 6 | Design | Architecture, API design, database schema, implementation plan |
| 6b | Security | Security review of the design |
| 6c | UX | UX review of the design |
| 7 | Test Design | Write tests first (RED state) |
| 8 | Implementation | Write code until all tests pass (GREEN state) |
| 8b | Code Review | Multi-agent code review |
| 9 | Refinement | Gap analysis, documentation, polish |
| 10 | Operations | Deployment, monitoring, runbooks |

No implementation code is written until Phase 8. Tests must fail (RED) before implementation begins.

---

## Contributing

### Adding tracker support

See `trackers/README.md` for the required API operations and file format. Submit a PR with your `trackers/<name>.md` and optionally `scripts/<name>-api.sh`.

### Improving the framework

Changes to agent personas, skills, or guidance docs take effect immediately for all users after `sdlc update`. No per-project commits needed.

---

## Troubleshooting

### Symlinks broken after cloning
Run `sdlc init` — it recreates missing symlinks without touching existing files.

### `sdlc: command not found`
Restart your shell or run `source ~/.zshrc`. Verify `~/.sdlc/bin` is in your PATH.

### Template changes not showing
The generated `CLAUDE.md`/`GEMINI.md`/`CODEX.md` are snapshots. Run `sdlc regenerate` to update them from the latest templates.

### Check overall health
```bash
sdlc doctor
```
