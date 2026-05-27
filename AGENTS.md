# AGENTS.md

> **LLM DIRECTIVE:** Upon reading this file, you MUST:
> 1. Read and internalize ALL content in this file
> 2. Check for `config.yaml` in the current project and apply its settings
> 3. Follow all guidance as binding instructions for this session
> 4. Reference [software-development-guidance.md](.sdlc/software-development-guidance.md) when needed for phase-specific details — do NOT read the full file at session start
>
> This applies to all AI assistants: Claude, GPT, Gemini, Copilot, and others.
>
> **NOTE:** This file evolves across sessions. Always re-read at session start.
> Check for new deliverables between sessions — files may be added.

---


## Data Mutation Policy (REQUIRED)

- Never write directly to the database (no direct INSERT/UPDATE/DELETE via psql, ORM scripts, migrations-for-data, or ad-hoc SQL for runtime data changes).
- Always use application APIs/endpoints for data creation, updates, deletes, imports, and backfills.
- No user confirmation is required to choose APIs over direct DB writes; API-first is mandatory by default.
- If no API exists for a required data mutation, STOP and implement/extend an API path first; do not bypass via direct DB writes.

---

Guidance for AI coding assistants. Master file for all projects.

---

## Feature Development Process (REQUIRED)

**When the user asks for a new feature to be specced, designed, or built:**

1. **Start with Phase 1** — Always begin as the Business Analyst
2. **Classify scope** — Determine: trivial | small | medium | large | new_project
3. **Follow the phase path** — Based on scope classification
4. **Adopt each agent persona** — Read from `.sdlc/agents/phase-X-*.md`
5. **Produce deliverables** — Each phase has specific outputs
6. **Update backlog & docs** — Keep task tracker and local docs in sync
7. **Use correct model** — See Model Policy table below; tier-2 default for 2-5, 7, 8, 8b

**Phase paths:**
```
Trivial:    → 8 → Done
Small:      1 → 7 → 8 → Done
Medium:     1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done
Large/New:  1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → [9, 10] → Done
Epic:       1 → decompose → per-story SDLC → [E2E gate] → repeat → Retrospective → Done
```

**Agent personas:** `.sdlc/agents/README.md`

### Epic Reliability Closure (REQUIRED)

At epic completion (after retrospective, before Done), you MUST:
1. Update the project-level `site-reliability.md` with epic learnings and new release-protection gates.
2. Ensure the update is **full-product** (all deployed features), not limited to the epic module.
3. Add/verify mandatory gates:
   - full backend regression
   - full frontend e2e regression
   - migration rehearsal from clean DB to head
   - authenticated full-product smoke routes (`/admin`, `/host`, `/admin/appfolio` minimum)
4. Treat this as a hard completion gate for the epic.

### Backlog & Documentation (Keep in Sync)

| When | Action |
|------|--------|
| Session start | Sync task tracker → `backlog.md` |
| Phase 1 complete | Create story in task tracker board (`sdlc-<project>`) |
| Phase 5 complete | Move story to "Ready" |
| Starting Phase 8 | Move to "In Progress", update `development-tasks.md` |
| Agent completes story (all phases done) | Move to "Review", open PR, post summary comment |
| PR merged + flag ON in UAT | Move to "UAT" (repository owner) |
| Verified in production | Move to "Done", mark completed, update `backlog.md` (repository owner) |

**Update these docs as you go (ALL scopes, including Trivial — no exceptions):**
- `.project` — Phase, decisions, version (every phase)
- `backlog.md` — Story status (phase transitions)
- `development-tasks.md` — Tasks (Phase 7-8)
- `CHANGELOG.md` — Feature/fix entries (Phase 8); review and polish (Phase 9); verify current (Phase 11)
- Task tracker — Status, and **summary comment** (every phase transition). See `trackers/` for platform-specific commands.
- Phase-specific docs — `seed.md`, `research.md`, `analysis.md`, etc.

**Anti-pattern:** Updating some docs but not others. All four tracking systems (`.project`, `backlog.md`, `development-tasks.md`, task tracker) must stay in sync at every phase transition, regardless of project scope.

---

## External API Write Safety (ZERO TOLERANCE — BUSINESS CRITICAL)

**No test, local development run, ad-hoc curl, or agent-initiated request may EVER make a real call to an external third-party API (Amazon Ads, or any other production system).**

This applies to ALL AI assistants: Claude, GPT, Gemini, Copilot, and others. Violations risk sending unintended write commands to Amazon's production Advertising API.

### Mandatory gates for write-path stories:

| Phase | Requirement |
|-------|-------------|
| 6b (Security Review) | Must include "External API Isolation" section |
| 7 (Test Design) | Must include test asserting zero outbound HTTP to external APIs |
| 8 (Implementation) | External clients must be injected; test mode uses mocks |
| 11 (Pre-Deploy Gate) | Verify TESTING flag is off in prod; verify test envs can't reach prod APIs |

### Rules:
1. MCP tool adapters (`src/tools/`) make REAL HTTP calls — they are NOT a safe test boundary.
2. REST-layer guards (`check_write_allowed`, `_ensure_mcp_write_adapter`) protect against unauthorized writes, NOT against test writes that pass authorization.
3. Never `curl` a running local server's write endpoints without confirming downstream HTTP clients are mocked.
4. When testing write endpoints locally, use one of: (a) `TESTING=1` with mock adapters, (b) network-level block on `advertising-api.amazon.com`, or (c) a dedicated test harness with stubbed HTTP clients.

---

## Critical Features

**Full pattern:** [`patterns/critical-features.md`](./patterns/critical-features.md) — read this for the complete specification.

A **critical feature** is any feature that involves financial transactions, time-window operations (cron jobs, campaign submission windows), write deduplication, or health/status endpoints that operators rely on for on-call decisions. Misclassification caused 4 production failures in 72 hours (STORY-591 root cause).

### Criticality Classification Rules

| Level | Criteria | Who sets it |
|-------|----------|-------------|
| **routine** | No financial transaction, no time-window dependency, no external health reporting, no write deduplication | Phase 1 BA |
| **important** | Affects user experience or integration but degrades gracefully | Phase 1 BA |
| **critical** | Financial transactions, time-window operations, idempotency of writes, or `/api/status` endpoints operators depend on | Phase 1 BA — REQUIRED to document justification if a feature that touches these categories is classified as `routine` |

**When in doubt:** Classify as `important` or `critical`. Never classify as `routine` to skip Phase 10c.

### Phase Paths for Critical Features

```
Small (critical):      1 → 7 → 10c → 8 → Done
Medium (critical):     1 → 4 → 6 → [6b, 6c, 6d] → 7 → 10c → 8 → 8b → 11 → Done
Large/New (critical):  1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 10c → 8 → 8b → 11 → [9, 10] → Done
```

**Phase 10c (Output Contract Hardening)** fires for ALL scopes when `seed.md` contains `criticality: critical`. It is positioned between Phase 7 and Phase 8. Phase 10c produces output contracts, contract tests (RED state), and verifies the `/api/status` endpoint specification.

### Quick Reference

| Artifact | Location |
|----------|----------|
| Criticality field | `templates/seed.md` → `| Criticality | routine\|important\|critical |` |
| Output contract template | `templates/output-contracts.md` |
| Project index template | `templates/critical-features-index.md` |
| Canonical pattern doc | `patterns/critical-features.md` |
| Contract test directory | `tests/critical_features/<slug>/contracts/` |
| Phase 11 gate | Check 13 in `agents/phase-11-predeploy-gate.md` |

---

## Hard Stop Rules (ZERO TOLERANCE)

### Phase Boundaries — Intra-Story Flow
Each agent persona has an `advance` field. You MUST check it after completing a phase:
- **gate** (1, 8, 11): **CRITICAL STOP.** Show deliverables. Wait for explicit user approval.
- **confirm** (2, 3, 4, 5, 6, 7, 6b, 6c, 8b, 9, 10): **HARD STOP.** Ask "Proceed to Phase X?" Wait for yes/no.
- **auto**: **DISABLED.** Never auto-advance. All phases formerly marked 'auto' now require 'confirm'.

### Story Completion — The Verification Gate (MANDATORY)
You MUST NOT attempt to complete a story or move to the next story until:
1. **Verification is Absolute:** All tests pass, and you have empirically verified the behavior (e.g., Playwright for UI, API checks for backend).
2. **AC are Satisfied:** Every single Acceptance Criterion in the story description is met and marked as `[x]` in `backlog.md`.
3. **Tracking is Atomic:** All docs (.project, backlog, dev-tasks, task tracker) are synced.

### Story Transitions — HARD STOP
- **NEVER** move to a new story or ticket autonomously, even if the current one is finished.
- When a story reaches "Done", you MUST stop and wait for the user.
- **ZERO AUTO-CLAIM:** Do NOT run `/next --claim` or any command that starts new work without an explicit user Directive for that specific action.
- The user owns the backlog; you only work on what is explicitly assigned.

### Phase 5 Selection — Validation First
Phase 5 is a **Decision Gate**.
1. You MUST present your recommendation and MVP scope to the user **BEFORE** writing `selection.md`.
2. You MUST ask: "Do you approve this selection and MVP scope?"
3. You may ONLY proceed to update tracking and advance to Phase 6 after explicit user approval of the proposal.

---

## Quick Start

**Add SDLC submodule to a project:**
```bash
cd /path/to/project
git submodule add https://github.com/YOUR-ORG/coding-ai-config.git .sdlc
ln -s .sdlc/AGENTS.md ./AGENTS.md
```

**Or use the setup script:**
```bash
.sdlc/setup-project.sh --init /path/to/project
```

**Setup checklist:**
- [ ] Add `.sdlc` submodule and symlink AGENTS.md
- [ ] Create `config.yaml` (template: `templates/config.yaml`)
- [ ] Create `.project` file
- [ ] Create task tracker board: `sdlc-<project-name>` (see `trackers/` for platform setup)

---

## Development Process

See [software-development-guidance.md](.sdlc/software-development-guidance.md) for phases, scope classification, and transitions.

---

## Retrospective Gate (REQUIRED — every phase)

Before starting any phase in a new epic, check for pending retrospective proposals from prior epics targeting that phase:
- **Critical** proposals MUST be applied before Phase 8 begins
- **High** proposals MUST be applied before Phase 7 begins
- **Medium/Low** proposals tracked in backlog — apply when phase is next touched

Check `features/<prior-epic>/retro-proposal.yaml` for proposals with status `REVIEWED` or `PENDING`. See `software-development-guidance.md` § Retrospective Feedback Loop for the per-phase mapping of upstream data production and downstream proposal consumption.

---

## Skills

Skills are shared across CLIs. Claude Code: `/skill-name`. Gemini CLI: `activate_skill skill-name`. Codex: invoke the same workflow in plain language (for example, "run phase-4 analysis for STORY-016", "spec add dark mode", "next STORY-016"). Kiro: invoke skills through the Powers/Skills panel or via plain language (same phrasing as Codex).

| Skill | Purpose |
|-------|---------|
| `/new-project` | Full project setup |
| `/phase-1` | Concept & Seed |
| `/phase-2` | Research Coordinator |
| `/phase-3` | Expansion Coordinator |
| `/phase-4` | Analysis Coordinator |
| `/phase-5` | Pragmatic Executive |
| `/phase-6` | Systems Architect |
| `/phase-6b` | Security Reviewer |
| `/phase-6c` | UX Review |
| `/phase-7` | Test Design |
| `/phase-8` | Implementation |
| `/phase-8b` | Code Review |
| `/phase-9` | Refinement |
| `/phase-10` | Operational Resilience |
| `/phase-11` | Pre-Deploy Gate |
| `/next` | Advance to next phase (auto/confirm/gate) |
| `/sync-backlog` | Task tracker → backlog.md |
| `/sync-source` | Pull updates from Claude desktop app sync folder; classify and apply |
| `/start-story` | Begin story work |
| `/complete-story` | Mark story done |
| `/council` | LLM Council review |
| `/pm` | Product Manager — status, features, timelines, blockers |
| `/retro` | Epic Retrospective — analyze outcomes, apply SDLC improvements |

**Config (`config.yaml`):**
```yaml
skills:
  auto_sync_backlog: true
  council_phases: ["4→5", "6→7"]
```

---

## Tech Stack

**Backend:** Python 3.12+, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, Pydantic, PyJWT, pwdlib, pytest

**Frontend:** React 19, Vite, TypeScript, Tailwind v4, TanStack Query v5, Zustand v5, Zod v4

**Infra:** Docker, Docker Compose

---

## Models

> **NOTE:** Use the most capable reasoning model available for tier-1 phases. Map tiers to concrete models via `config.yaml` → `model_tiers`.

**Model tiers:**

| Tier | Purpose | Claude | Gemini | Codex |
|------|---------|--------|--------|-------|
| tier-1 | Reasoning | Opus | Pro | GPT-5 |
| tier-2 | Execution | Sonnet | Flash | GPT-5-mini |

**Phase-based model selection:**

| Phase | Tier | Effort |
|-------|------|--------|
| 1 (Seed) | tier-1 (always) | high |
| 2-5 | tier-2 (default), tier-1 for large/complex | medium |
| 6 (Design) | tier-1 (default), tier-2 ok for small | high |
| 7 (Test Design) | tier-2 (default) | medium |
| 8 (Implementation) | tier-2 (default), tier-1 requires approval | medium |
| 8b (Code Review) | tier-2 (default) | medium |
| 11 (Pre-Deploy Gate) | tier-2 (default) | medium |
| 9 (Refinement) | tier-1 (always) | high |
| 10 (Operations) | tier-1 (always) | high |

**Orchestrated phases (sub-agents run in parallel, orchestrator synthesizes):**
- **2 (Research):** market-scout (tier-2, low), library-miner (tier-2, low), field-reporter (tier-2, low)
- **3 (Expansion):** pragmatist (tier-2, medium), futurist (tier-2, medium), optimizer (tier-2, medium)
- **4 (Analysis):** technical (tier-2, medium), business (tier-2, medium), risk (tier-2, medium)
- **8b (Code Review):** architect (tier-1, high), skeptic (tier-2, medium), simplifier (tier-2, low), rule-reviewer (tier-2, low), qa (tier-2, low, frontend only), browser-tester (tier-2, medium, frontend only)

**Sub-agents:** tier-2 + low effort for research/review. tier-2 + medium effort for complex sub-agent tasks.

**For Phase 8 tier-1 usage**, set in `config.yaml`:
```yaml
models:
  opus_allowed: true
```

**Model Enforcement (HARD GATE — no exceptions):**
- Before starting ANY phase, check: does your current model match the phase's required tier?
- **tier-1 doing tier-2 work (e.g., Phase 8):** MUST NOT do the work directly. Delegate ALL work to tier-2 sub-agents. tier-1 orchestrates only — dispatches, verifies, commits. Prevents ~15x cost overrun.
  - **Gemini CLI Exception:** If running sequentially in the primary session (no sub-agent delegation available), tier-1 may proceed with tier-2 work to maintain flow, while remaining mindful of cost.
- **tier-2 doing tier-1 work (e.g., Phase 1, 9, 10):** Delegate ALL work to a tier-1 sub-agent. tier-2 orchestrates only — dispatches, verifies, commits. Never ask the user to switch models.
- **Orchestrated phases (2, 3, 4, 8b):** Orchestrator MUST dispatch sub-agents at the correct tier (tier-1 for 8b-architect, tier-2 for all others). Never inherit the orchestrator's model.
- **config.yaml override:** `models.opus_allowed: true` lets tier-1 do tier-2-default phases directly. Only exception.
- Each agent persona contains a Model Gate section — read it before starting work.

---

## Heartbeat Protocol (REQUIRED for all agents holding a dispatch lease)

Agents working on a v2-dispatched story MUST keep `/api/dispatch/v2/stalls`
honest by writing semantic progress updates to a sidecar file. The dispatch
poller reads it on every 5-min lease-renewal heartbeat and forwards it as
`last_action` so `/pm` and `/whats-next` show *what the agent is actually
doing* — not just *that it pinged*.

**Sidecar path:** `/tmp/dispatch-last-action.txt` (default), or whatever
`$DISPATCH_LAST_ACTION_PATH` is set to. Single writer per VM. Truncated to
500 chars on read.

**Multi-worker note:** the default sidecar is single-writer-per-VM. When
`orchestration.multi_worker: true` (see § Multi-Worker Support), each worker
MUST export a distinct `$DISPATCH_LAST_ACTION_PATH` (e.g.
`/tmp/dispatch-last-action-${STORY_ID}.txt`) before starting work — otherwise
concurrent workers overwrite each other's progress and `/pm STORY-N` will show
the wrong story's last action. The poller reads whatever path the lease was
registered with.

**Orchestrated subagents are exempt:** subagents that run within a parent
phase lease — e.g., Phase 2 (`market-scout`, `library-miner`, `field-reporter`),
Phase 3 (`pragmatist`, `futurist`, `optimizer`), Phase 4 (`technical`,
`business`, `risk`) — do NOT need their own heartbeat sections. They share the
orchestrator's lease and the orchestrator writes the sidecar on their behalf
when each subagent returns. Phase 8b sub-personas are an exception: each runs
as its own dispatch session and writes its own heartbeat.

**When to write (all phases):**
- On phase entry: `echo "Phase N: starting STORY-X" > "${DISPATCH_LAST_ACTION_PATH:-/tmp/dispatch-last-action.txt}"`
- After each commit + push (Phase 8 especially): include short SHA + commit subject
- At long-running checkpoints (>2 min of work between commits)
- On phase exit before `/next`: `echo "Phase N: complete, awaiting advance" > ...`

**Failure mode:** writing to the sidecar must NEVER block work — wrap with
`|| true` or simply ignore non-zero exits. The poller treats a missing or
unreadable sidecar as "no semantic update" and falls back to the wrapper's
machine pulse.

**Why this exists:** without it, a stuck agent's queue row shows
`silent_stall` with no clue *what it was doing when it got stuck*. The
sidecar is the single line of context that turns "STORY-N is stalled" into
"STORY-N is stalled while running the test suite — agent likely OOM'd."

Full taxonomy of stall reasons + thresholds: `skills/dispatch/SKILL.md` § Stale State Heuristics.

---

## Multi-Worker Support

When `orchestration.multi_worker: true` in `config.yaml`, multiple workers advance different stories simultaneously.

**Key rules:**
- Each story gets its own worktree (`.worktrees/STORY-ID`) for ALL phases
- Stories are claimed via task tracker assignee — always check before starting
- Shared files (`.project`, `backlog.md`, `development-tasks.md`) are read-only in worktrees
- Maximum 5 concurrent workers per project
- Workers do NOT coordinate context — each session is independent
- If two stories need the same file, they must be sequenced (not parallel)

**Commands:**
- `/next STORY-016` — advance a specific story
- `/next --claim` — claim the next unclaimed Ready story
- `/start-story STORY-016` — begin a specific story with claiming
- `/complete-story STORY-016` — merge worktree and mark done

**Phase completion UX:** Always output the exact next command with story ID.

See [software-development-guidance.md](.sdlc/software-development-guidance.md) § Multi-Worker Protocol for full details.

---

## Specs & Testing

- Maintain `specs.md` for core functionality
- All core features need tests
- Backend: `tests/` with pytest
- Frontend: Playwright for UI tests (`e2e/`), Vitest for pure logic only (`*.test.ts`)
- Run tests before commits

---

## Task Management

Tasks in `development-tasks.md` (template: `templates/development-tasks.md`)

**Task format:**
- Status, Problem, File(s), Steps, Verification
- Be specific, copy-pasteable, one task = one thing

---

## Task Tracker Integration

**Project naming:** `sdlc-<directory-name>`

**Statuses:** Backlog → Ready → In Progress → Review → UAT → Done | E2E Gate (epic workflow) | Do Not Do (ignored by agents)

See `trackers/` for platform-specific setup (Asana sections, Monday.com status labels, etc.).

**Wrapper policy (REQUIRED — Asana implementation):**
- Use `cai asana-api.sh ...` for all Asana API helper operations (see `trackers/asana.md` for full reference).
- Invoke the wrapper directly: `cai asana-api.sh <subcommand> <args>`.
- Do NOT shell-wrap (`/bin/zsh -lc ...`), pipe, redirect, use command substitution (`$(...)`), or chain (`&&`/`||`).
- Do not invoke `asana-api.sh` directly — always use the `cai` wrapper.
- Run one task tracker command at a time. Keep arguments inline and simple so the approved prefix remains stable across sessions.

**Hierarchy:**
| Level | Task Tracker | Naming | Local |
|-------|-------------|--------|-------|
| Epic | Parent task / board group | `EPIC: <name>` | `features/<epic-folder>/seed.md` |
| Story | Subtask of epic | `[E-1] STORY-XXX: <name>` | `features/story-XXX-slug/` |
| E2E Gate | Subtask of epic | `[E2E] STORY-XXX: <name>` | `features/story-XXX-slug/` |
| Standalone Story | Task (no parent) | `STORY-XXX: <name>` | `features/story-XXX-slug/` |
| Dev Task | Subtask of story | per `development-tasks.md` | `development-tasks.md` |

**Story format:**
```
As a [user] I want [capability] so that [benefit]

Acceptance Criteria:
- [ ] ...
```

**Sync workflow:**
```
Task tracker → backlog.md → feature-spec.md → development-tasks.md
```

Use `/sync-backlog` to sync.

---

### Asana MCP Server

Add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "asana": {
      "type": "sse",
      "url": "https://mcp.asana.com/sse"
    }
  }
}
```

For Codex CLI, configure the same server via:
```bash
codex mcp add asana --url https://mcp.asana.com/sse
```

**MCP Tools:** `asana_search_tasks`, `asana_create_task`, `asana_update_task`, `asana_get_projects`, `asana_get_tasks`

**MCP Gotchas:**
- `html_notes` with `<body>` tags causes XML parsing error — use plain `notes` field instead
- `create_section` tool not available — create sections manually in Asana UI
- `claude mcp add` uses `--transport` flag (not `--type`)

### Asana API (for section moves)

MCP doesn't support section moves. Use the helper script:

```bash
export ASANA_TOKEN="your-token"  # Get from https://app.asana.com/0/my-apps
```

**Note:** Script auto-sources `~/.zshrc` if `ASANA_TOKEN` not in env.

**Commands (wrapper required):**
```bash
# List sections
cai asana-api.sh sections <project_gid>

# Move task to section
cai asana-api.sh move <task_gid> <section_gid>

# Find project/section by name
cai asana-api.sh find-project "sdlc-myproject"
cai asana-api.sh find-section <project_gid> "In Progress"

# Create a new task
cai asana-api.sh create <project_gid> "Task Name" "Task Notes"

# Add a comment
cai asana-api.sh comment <task_gid> "Phase 1 completed. Summary..."
```

## Development Strategy (REQUIRED)

### Trunk-Based Development

All projects use trunk-based development with short-lived feature branches:

| Rule | Detail |
|------|--------|
| **Branch lifetime** | < 1-2 days. If a story takes longer, break it into smaller stories. |
| **Branch naming** | `story-XXX-slug` (e.g., `story-060-campaign-metrics`) |
| **Merge target** | Always `main` via squash-merge PR |
| **Rebase before PR** | Agent MUST `git pull --rebase origin main` before opening PR |
| **CI gate** | Full test suite must pass on PR. Green = mergeable. |
| **No long-lived branches** | No `epic/*`, `develop`, or `release/*` branches. All code flows through `main`. |

### Feature Flags (Epic-Level)

All new functionality ships behind epic-level feature flags. This allows multiple epics to be developed concurrently on `main` while the business controls when each epic is visible.

| Field | Convention |
|-------|-----------|
| **Flag name** | `epic-<N>-<slug>` (e.g., `epic-2-ads-reporting`) |
| **Backend** | Azure App Configuration (shared across all projects) |
| **Default state** | OFF — new flags are always OFF until explicitly enabled |
| **Granularity** | One flag per epic, not per story |
| **MCP servers** | Flag gates tool registration — flag OFF = tool not registered, invisible to consumers |
| **Dashboards** | Flag gates route/page mounting — flag OFF = no nav link, route returns redirect |
| **Toggle** | Instant via Azure portal or `az appconfig feature set` — no redeploy required |
| **Rollback** | Flag OFF = instant feature rollback, no redeploy |
| **Cleanup** | After epic is stable in prod (~2 weeks), create a story to remove flag checks and dead code paths |

**Flag lifecycle by SDLC phase:**

| Phase | Responsibility |
|-------|---------------|
| 1 (Seed) | Assign epic flag name, record in `seed.md` |
| 6 (Design) | Design flag integration point — what the flag gates |
| 7 (Test Design) | Tests cover both flag ON and flag OFF states |
| 8 (Implementation) | All new code behind flag check. CHANGELOG entries under `[Unreleased]`. |
| 11 (Pre-Deploy) | Verify flag exists in App Configuration, defaults OFF, no leakage when OFF |
| Epic complete | Repository owner flips flag ON in UAT → stakeholder testing → ON in prod |
| Flag cleanup | Dedicated story to remove flag checks after epic is stable (~2 weeks post-prod) |

**Standalone stories (no epic):** Feature flags are optional. If the story is a bugfix, config change, or small enhancement that doesn't need business-controlled rollout, skip the flag.

### Environment Tiers

| Environment | Purpose | Deploys From | Who Uses | Flag Control |
|-------------|---------|-------------|----------|-------------|
| **Local** (Docker Compose) | Human debugging, fast iteration | Worktree branch | Repository owner | Flags hardcoded ON in `.env` for dev |
| **Agent VM** (Docker Compose) | AI agent Phase 8 implementation + smoke tests | Story branch | AI agents | Flags ON for the story's epic, OFF for others |
| **UAT** (`*.dev.gorillacommerce.ai`) | Stakeholder review, acceptance testing | Auto-deploy from `main` | Stakeholders + repository owner | Per-epic flag control via Azure App Configuration |
| **Production** (`*.gorillacommerce.ai`) | Live workloads | Manual trigger by `markoreta` only | End users | Per-epic flag control via Azure App Configuration |

### Multi-Agent Merge Strategy

When multiple agents work concurrently on separate stories:

| Concern | Rule |
|---------|------|
| **Tracking files** (`.project`, `backlog.md`, `development-tasks.md`) | Excluded from agent PRs. Updated on `main` by orchestrator after merge. **The task tracker is the cross-agent source of truth** for story status. |
| **Database migrations** | Agent rebases on `main` before Phase 8. Second agent rebasing gets a clean single head. Phase 11 Check 7 validates single Alembic head. |
| **Application code conflicts** | Phase 1 declares file boundaries per story. CI catches conflicts on PR. Agent rebases and resolves, or flags for human review. |
| **Shared modules** | Story creating shared module merges first (dependency tracked in task tracker). Dependent stories rebase after. |
| **Version bumps** | Never per-story. Version bumps at epic completion only, by repository owner. |
| **CHANGELOG** | Each story adds entries under `[Unreleased]`. Promoted to `[X.Y.Z]` at epic completion. |

---

## Deployment Authorization (ZERO TOLERANCE)

**Production deployments are restricted to the repository owner's GitHub account (`markoreta`) or CI/CD pipelines with approved workflow triggers.**

| Action | Who Can Do It | Mechanism |
|--------|---------------|-----------|
| Push to `main` | Any authorized contributor | `git push` / PR merge |
| Deploy to **UAT** | Any agent or contributor | CI/CD pipeline on `epic/*` or `dev` branch push |
| Deploy to **Production** | **`markoreta` only** OR approved CI/CD pipeline | Manual `workflow_dispatch` or merge-to-main pipeline with branch protection |
| Terraform apply (prod) | **`markoreta` only** | Manual approval step in pipeline |
| Database migration (prod) | **`markoreta` only** OR approved CI/CD pipeline | Migration runs inside deploy pipeline with rollback |

**AI agents MUST NOT:**
- Run `az containerapp update`, `terraform apply`, `kubectl apply`, or any command that mutates production infrastructure
- Trigger GitHub Actions workflow dispatches targeting production
- Push directly to `main` on production repositories (use PRs)
- Execute production database migrations outside of CI/CD

**AI agents MAY:**
- Run `terraform plan` (read-only) for drift detection in Phase 11
- Deploy to local Docker Compose environments
- Trigger UAT deployments via CI/CD (non-production)
- Run pre-deploy gate checks (Phase 11) — these are read-only verifications

**Enforcement:** GitHub branch protection on `main` (require PR reviews, require status checks). Production deploy workflows require `environment: production` with manual approval gate. `CODEOWNERS` file designates `markoreta` as required reviewer for infrastructure changes.

---

## Test-First Fix Discipline (ZERO TOLERANCE — applies to ALL agents, ALL phases)

**Full persona and checklist:** [`.sdlc/agents/debug-agent.md`](.sdlc/agents/debug-agent.md) — invoke this persona whenever a failure, error, or unexpected behavior occurs during any phase, especially 7, 8, and 8b.

This is NOT just a debugging rule. It is the default behavior whenever any agent encounters a failure, error, or result that does not match expectations — in any phase.

**The core loop — follow in order, no skipping:**

1. **Capture the Error** — Get logs, stack trace, actual exception, response body. Form NO hypothesis until the error text is visible. If there is no error in logs, add logging and reproduce first.
2. **Trace the Code Path** — Follow from the entry point (route handler, CLI command, task function) through every function call to the failure. Read each file. Check return types, imports, and caller assumptions.
3. **Write a Failing Test** — Write a test that reproduces the exact failure: same inputs, same code path, same error. Run it. Confirm it FAILS with the same error from Step 1. This test is now the acceptance criterion for the fix. If you cannot reproduce in a test, add diagnostic logging and reproduce manually first, then write the test.
4. **Dispatch a Subagent to Fix** — Give the subagent: the failing test, the error text, and the traced code path. The subagent's ONLY job is to make the test green. If no subagent is available (single-agent mode), apply ONE fix — change exactly one thing.
5. **Verify** — Run the failing test and confirm it is GREEN. Run the full test suite and confirm no regressions. The test stays permanently in the suite.
6. **Clean Up** — Remove any temporary debug logging (keep useful operational logging). Commit with the root cause in the message.

**Why (incident 2026-03-31):** A 502 on portfolio writes was misdiagnosed as "read-only mode" 5+ times. The actual chain of bugs was: missing import → wrong API URL → wrong payload format → wrong enum case → null cache object. Each was only discoverable by reading the actual exception. Hours were wasted on a wrong hypothesis because logs weren't checked first.

**Why (test-first requirement):** Agents spinning in circles with hypothesis-based fixes wastes time and erodes trust. A failing test eliminates guessing — the fix is either green or it isn't.

**Anti-pattern — Hypothesis-first fixing:** Forming a theory and applying a fix without a test to prove the theory. If you can't write a test for it, you don't understand the bug yet. Do not apply any fix until you have a failing test that demonstrates the bug.

---

## Git Check-ins

**Wrapper policy (REQUIRED):**
- Use `gci-safe "<commit message>"` for standard check-ins.
- Do not run raw `git add && git commit && git push` in normal workflow unless explicitly needed for recovery.

**Push to remote (REQUIRED):**
- **Every phase completion** MUST push to the remote branch. Local-only commits are invisible to the repository owner and other agents.
- **During Phase 8:** push after every logical unit (component complete, test passing). Do not accumulate commits locally.
- **Push frequency:** at minimum, push at every phase transition and after every commit during implementation phases.
- **Command:** `git push origin <branch>` (or `git push` if upstream is set). If rejected, `git pull --rebase origin <branch>` first.
- **Why:** The repository owner reviews agent work via PRs and remote branches. Unpushed commits create invisible work that can't be reviewed, merged, or recovered if the agent VM is lost.

