# Software Development Guidance

> Reference in `AGENTS.md` or `CLAUDE.md`:
> `See [software-development-guidance.md](./software-development-guidance.md)`

## Deliverables

| File | Phase | Scope |
|------|-------|-------|
| `.project` | All | All |
| `backlog.md` | All | All |
| `development-tasks.md` | All | All |
| `seed.md` | 1 | Small+ |
| `codebase-context.md` | 1 | Large |
| `research.md` | 2 | New/Large |
| `expansion.md` | 3 | New/Large |
| `analysis.md` | 4 | New/Large/Medium |
| `selection.md` | 5 | New/Large |
| `specification.md` | 6 | New/Large |
| `feature-spec.md` | 6 | Medium |
| `architecture.md` | 6 | New/Large |
| `api-design.md` | 6 | New/Large |
| `database-schema.md` | 6 | New/Large |
| `implementation-plan.md` | 6 | New/Large/Medium |
| `ux-review.md` | 6c | Medium+ |
| `ops-review.md` | 6d | Medium+ |
| `test-design.md` | 7 | Small+ |
| `tests/` (runnable, RED) | 7 | Small+ |
| `tests/` (GREEN) | 8-9 | Small+ |
| `predeploy-gate.md` | 11 | Medium+ |
| `site-reliability.md` | 10 | New/Large |
| `site-reliability.md` (project root refresh) | Epic close | Epic |
| `README.md` | 1 | All |

Templates: See `templates/` directory.

**Deliverable location:** `features/<story-folder>/` (all modes).

| Mode | Working directory | Example |
|------|------------------|---------|
| Single-worker | Project root | `features/story-021-user-auth/seed.md` |
| Multi-worker (worktree) | Worktree root | `features/story-021-user-auth/seed.md` (within worktree) |

**Rules:**
- Shared tracking files (`.project`, `backlog.md`, `development-tasks.md`) always live at project root — read-only in worktrees
- Story deliverables go in `features/<story-folder>/` — NEVER at project root
- Test files (`tests/`) follow the project's test directory structure, scoped to the story's worktree/branch

---

## SDLC Mandate

**Every request to spec, design, or build something MUST follow the SDLC phases — no exceptions.** This includes features, infrastructure, deployment, tooling, spikes, and refactors. The scope classification determines how many phases are required (trivial → small → medium → large), but the process is never skipped entirely.

**"spec" trigger:** Any prompt starting with "spec" MUST initiate the SDLC process starting at Phase 1 (Seed). Treat "spec ..." as equivalent to `/phase-1 ...`. When `multi_worker: true`, spec also auto-runs `/start-story` after Phase 1 completes — one command creates the seed, task tracker item, worktree, and Story Status row. Output: `Next: /next STORY-ID`.

If the user asks to "just do X" or "quickly set up Y", classify the scope and follow the appropriate phase path. A small scope is a shorter process (1 → 7 → 8), not no process.

---

## Parallel Backlog Processing (DEFAULT)

**When multiple stories exist in the backlog, parallelize by default.** Sequential processing is the fallback, not the norm. Each story runs its full SDLC phase path in an isolated worktree via a Task subagent.

### Why Parallel First

- Stories are independent units of work — their SDLC phases don't depend on each other
- Worktree isolation eliminates merge conflicts during development
- Throughput scales linearly with batch size
- Sequential processing wastes time when stories touch different files

### Batching Rules

1. **Group by conflict risk:** Stories touching different files/domains run in the same batch. Stories modifying the same files go in separate batches.
2. **Batch size:** 3-5 stories per batch (matches typical non-conflicting groups). Adjust based on codebase modularity.
3. **Priority order within batches:** Critical stories always in Batch 1. Within a priority level, trivial/small scope before medium (faster path = faster feedback).
4. **Dependency awareness:** If Story B depends on Story A's output (e.g., Story A creates an API that Story B consumes), they go in sequential batches.

### Execution Model

Each story in a batch runs as a **Task subagent with `isolation: "worktree"`**. The agent:

1. Gets the story's acceptance criteria, scope, and relevant codebase context
2. Follows the full SDLC phase path for that scope (1→7→8 for Small, →8 for Trivial, etc.)
3. Produces all phase deliverables (seed.md, test-design.md, implementation)
4. Commits with standard format: `phase <N>: [story-name] <description>`
5. Returns the worktree branch with all changes

### Merge Strategy

After a batch completes:

1. **Review each worktree branch** for quality and completeness
2. **Merge smallest changeset first** to minimize conflict snowball
3. **Run full test suite** after each merge to catch integration issues
4. **Update shared files** (.project, backlog.md, task tracker) in the main branch after merge — not in worktrees
5. **Resolve conflicts** if any — prefer the change that better matches the story's acceptance criteria

### Shared File Handling

These files are NOT modified in worktrees — they're updated in the main branch after merge:

| File | When Updated | By Whom |
|------|-------------|---------|
| `.project` | After each batch merge | Main session |
| `backlog.md` | After each batch merge | Main session |
| `development-tasks.md` | After each batch merge | Main session |
| Task tracker | After each story merge | Main session |

**Version field rule (CRITICAL):** The `.project` version and Version History table in a worktree are stale snapshots from worktree creation time. Worktree agents MUST NOT read, compare, or reason about version numbers — they will differ from the root `.project` and cause confusion. Version bumps happen exclusively at merge time in the main branch.

### Batch Status Tracking

Track batch progress in `.project`:

```markdown
### Batch Execution Status
| Batch | Stories | Status | Merged |
|-------|---------|--------|--------|
| 1 | Wire debate exec, SSE streaming, Council edit | in_progress | 0/3 |
| 2 | Council create, Council delete, YAML import, Clone | pending | 0/4 |
```

### When NOT to Parallelize

- **Single story:** No batching needed
- **Heavy file overlap:** Stories that all modify the same core files (e.g., all touching `main.py`)
- **Sequential dependency:** Story B cannot start until Story A's code exists
- **User requests sequential:** Explicit override

---

## Multi-Worker Protocol

When `orchestration.multi_worker: true` in `config.yaml`, multiple workers (humans, AI sessions, or both) can advance different stories through the SDLC simultaneously.

### Core Principle

**The task tracker is the source of truth for story state. `.project` is a local dashboard that may be stale in worktrees.**

- Before claiming or suggesting a story, **always check task tracker live state** (task assignee + section)
- A story showing "Ready" in `.project` may already be claimed by another worker in the task tracker
- **Never compare version numbers** between worktree and root `.project` — they will diverge and it's expected. Version bumps are a merge-time concern only.
- If `.project` and the task tracker disagree, trust the task tracker
- Never recommend a story that has a task tracker assignee — it's already claimed
- **Exclude "Do Not Do" tasks** — tasks in the "Do Not Do" section are invisible to all agent operations (claiming, suggesting, listing)

### Worktree-Per-Story Isolation

Each claimed story gets its own worktree for ALL phases (not just Phase 8):
- Worktree location: `.worktrees/STORY-ID`
- Branch naming: `phase-N/story-slug`
- **All story deliverables** (seed.md, test-design.md, feature-spec.md, architecture.md, etc.) are written to the **worktree root** — NEVER to the main project root. The worktree IS the story's working directory.
- Worker advances through phases in their worktree
- Merge happens at story completion (after final phase), not after each phase
- **Exception:** Shared deliverables that apply project-wide (e.g., `config.yaml` changes, migration files) follow the existing merge gate protocol
- **Anti-pattern:** Writing `test-design.md` or `seed.md` to the project root while in multi-worker mode — this overwrites other stories' deliverables

### Shared File Rules

| File | Access in Worktree | Updated By |
|------|-------------------|------------|
| `.project` | Read-only | Orchestrator / main session only |
| `backlog.md` | Read-only | Orchestrator / main session only |
| `development-tasks.md` | Read-only | Orchestrator / main session only |
| Story deliverables | Read-write | Worker in worktree |
| Task tracker | Read-write | Any worker (via API/MCP) |

### Claiming Protocol

Stories are claimed via task tracker assignee field:
1. Before starting, check task tracker assignee — if already assigned, warn user
2. Set assignee to current worker identity
3. Worker identity resolution: `config.yaml` → `orchestration.worker_id` > `git config user.name` > auto-generated
4. Move task to In Progress section
5. Create worktree and add Story Status row

### Merge Gate (Story Completion)

When a story reaches its final phase:
1. Run full test suite in worktree
2. Merge to main (smallest changeset first if multiple stories completing)
3. Run full test suite on main after merge
4. Post-merge integrity check (REQUIRED):
   - `python -c "import src.server"` (or equivalent) to verify no ImportError from removed functions
   - `grep -r '<<<<<<' src/` to check for merge conflict markers
   - Verify all function references resolve — merges that remove functions used by other stories are the #1 multi-worker failure mode
5. Remove worktree, delete branch
6. Update `.project` Story Status table, task tracker (Done + completed), `backlog.md`

### Worktree Merge Verification (REQUIRED before marking Done)

After merging a worktree to main and before marking story Done:

```bash
ls features/<story-folder>/
```

Required files by scope (must all be present on main):

| Scope | Required Files |
|-------|---------------|
| Small | seed.md, test-design.md |
| Medium | seed.md, analysis.md, feature-spec.md, security-review.md, ux-review.md, test-design.md, code-review.md, predeploy-gate.md |
| Large | all Medium + specification.md, architecture.md, api-design.md, database-schema.md, implementation-plan.md, predeploy-gate.md, refinement-report.md, site-reliability.md |

If any file is missing:
1. Check the worktree — the file may exist there but not have been merged
2. Cherry-pick to main if found in worktree
3. Produce the file if it was never created (document gap in code-review.md)

Story is NOT marked Done until all scope-required deliverables exist on main.

### Limits and Risks

- **Max workers:** 5 concurrent per project (configurable via `max_workers`)
- **File conflicts:** If two stories need the same file, they must be sequenced (not parallel) — enforced by File Ownership Matrix at Phase 6
- **Merge conflicts:** Resolved by sequential merge gate (smallest changeset first)
- **State drift:** `.project` ↔ task tracker → `/sync-backlog` resolves drift
- **Resource contention:** 5+ agents on one machine → memory/port exhaustion (use Docker/VM isolation for scale)
- **Context fragmentation:** Workers don't see each other's design decisions → mitigated by reading shared design docs before implementation

### UX Requirements

**Phase completion — minimize user effort:**
- **Same context group:** Apply advance category directly (auto/confirm/gate) — don't make the user retype commands
- **Context clear needed:** `"Please /clear, then /next"` — agent auto-resolves the story after clear
- **Story done:** `"Story STORY-016 complete. Run /next to auto-claim the next story."`
- The user should NEVER need to type a story ID — `/next` auto-resolves

**Model switching — never manual:**
- If the phase requires a different tier, delegate to a sub-agent at the correct tier
- Both directions: tier-1 → tier-2 and tier-2 → tier-1
- The user should NEVER be asked to switch models

---

## Context Management (CRITICAL)

Context pollution is the **#1 cause of degraded LLM output quality**. Performance drops as the context window fills with irrelevant information. Follow these rules:

**Between phases:**
- `/clear` between context groups (see Orchestration section), not necessarily every phase
- Within a context group, phases can advance without clearing
- Each group starts fresh — read the relevant phase docs and previous deliverables
- Use `/next` to auto-determine whether a `/clear` is needed

**During research (Phases 2-3):**
- Use subagents (Task tool) for all exploration. They run in separate context windows and return summaries
- Never read more than 3 files in the main context for research purposes
- Time-box: stop after 3 viable approaches or when no new information emerges

**During implementation (Phase 8):**
- `/clear` between unrelated functions/endpoints
- After 2 failed correction attempts on the same issue, `/clear` and restart with a better prompt
- Use `/compact Focus on [current task]` when context grows but you're mid-task
- Commit after each logical unit to create rollback save points

**Anti-patterns (never do these):**
- Kitchen sink sessions: mixing research, implementation, and debugging in one long conversation
- Correction spirals: repeatedly fixing the same error without starting fresh
- Infinite exploration: reading hundreds of files without a clear stopping criterion
- Carrying stale context: continuing after compaction without re-reading CLAUDE.md and .project

---

## Scope Classification

See AGENTS.md § Feature Development Process for phase paths by scope.

**Code gates:**
- Trivial: No gate
- Small: Tests first (Phase 7)
- Medium: Design + tests
- Large/New: No code until Phase 8
- Epic: Per-story gates + E2E integration gate between epic phases

### Story Sizing Guardrails (REQUIRED)

A single story should be implementable in one focused session. Stories that are too large cause subagent context overflow, partial implementations, and repeated failures.

**Hard limits per story:**
- **Max 30 tests** in Phase 7. If test design produces >30 tests, the story MUST be split.
- **Max 2 new DB models** (tables). If the design requires 3+ new tables, split into a models story + a service/API story.
- **Max 3 new API endpoints**. More endpoints = more stories.
- **Max 1 architectural layer per story.** A story should be: models OR service OR API/router — not all three stacked together. The exception is trivial/small scope where the full vertical slice is <15 tests.

**Splitting rules:**
When a story exceeds limits, split bottom-up:
1. **Models story** (Small scope): DB models, migrations, constants, basic CRUD. Tests: model constraints, relationships. Typically 8-15 tests.
2. **Service story** (Small/Medium scope): Business logic, state machines, validation. Depends on models story. Tests: service methods. Typically 10-20 tests.
3. **API story** (Small/Medium scope): Router, auth, request/response schemas, endpoint wiring. Depends on service story. Tests: HTTP-level integration. Typically 10-20 tests.

**When to split — triggers:**
- Phase 1 seed describes models + service + API → split during Phase 1
- Phase 6 design produces >3 endpoints or >2 tables → split before Phase 7
- Phase 7 test design produces >30 tests → STOP, split, re-seed the sub-stories
- Phase 8 subagent fails twice on the same story → likely too large, split and retry

**Subagent prompt quality (Phase 8):**
When dispatching implementation to a subagent, the orchestrator MUST provide:
1. **Exact file paths** to create/modify (not "look at the codebase")
2. **Exact imports and patterns** copied from existing code (auth deps, router registration, model base class)
3. **Exact constants and enums** as used in the test file (not the feature spec — tests define the contract)
4. **Method signatures** with parameter names and return types matching test expectations
5. **One chunk at a time** — dispatch models, verify GREEN, then service, verify, then router. Never all-at-once for >15 tests.
- Epic close gate: E2E gate story MUST include operational readiness verification. All ops requirements from Phase 6 designs must be implemented (not just documented). Project-level `site-reliability.md` MUST be updated with full-product release protections. Epic is NOT Done until ops tickets are closed.

### Regression Test Backfill (valid story type)

A **regression test backfill** story adds automated test coverage for bugs that were already fixed but not covered by tests at the time of the fix. These are first-class backlog items, not technical debt footnotes.

**Use when:**
- A bug was fixed as a hotfix without writing a test first
- A category of recurring bugs exists and you want regression guards
- Phase 8b fix loops repeatedly surface the same category of issue

**Phase path:** `1 → 7 → 8 → Done` (Small scope, no design phase needed)

**AC format:**
```
SC-1: [Scenario that reproduces the bug] → [Expected outcome]
      Guards against: [git commit hash or story ID of original fix]
```

**Rules:**
- Backfill stories do NOT modify production code — only test files
- All ACs must reference the specific bug they guard (traceability)
- If a backfill test FAILS against the current codebase, stop: the original fix was incomplete — file a bug story instead

**Sizing:** Up to 10 new tests = Small; 10–40 tests = Medium (prefer splitting into 2–3 Small).

---

### Scope Reassessment Protocol

If any phase reveals the scope classification is wrong, **STOP and reassess**. Do not proceed forward with known-bad assumptions.

**Triggers for reassessment:**
- Phase 2 research reveals the problem is bigger/smaller than expected
- Phase 4 analysis shows more components are affected than originally scoped
- Phase 6 design reveals database changes, new APIs, or cross-cutting concerns not in seed.md
- Phase 7 test design reveals too many or too few test cases for the scope
- Phase 8 implementation hits unexpected complexity

**Reassessment process:**
1. Document the trigger and rationale in `.project`
2. Propose the new scope classification to the user
3. Get user approval for the scope change
4. Restart from the **first required phase** for the new scope that hasn't been completed
5. Update the story's tracker ticket with the new scope

**Direction matters:**
- **Scope up** (Small → Medium): Add missing phases (e.g., add Phase 4 + 6 if going Small → Medium)
- **Scope down** (Large → Medium): Skip remaining unnecessary phases, but keep completed work

### Epic Scope

**When to classify as Epic:** Work that decomposes into 5+ stories, typically spanning multiple sprints or delivery phases. Examples: a new product module (accounting, maintenance), a platform migration, a multi-system integration.

**Epic Phase 1 (Seed) produces:**
1. `seed.md` — Problem statement, high-level goals, user personas
2. `implementation-plan.md` in `features/<epic-folder>/` — The execution tracker containing:
   - **Progress tracker table** — Story # | Name | Scope | Sprint | Phase | Tests | Status | Notes
   - **Pre-requisites table** — Actions needed before specific stories can start Phase 8
   - **Parallelism strategy** — Which stories can run concurrently, dependency graph
   - **Delivery phases** — How stories group into sprints/batches (e.g., P2-1: Foundation, P2-2: Core, P2-3: UI)
   - **Transition gates** — Mandatory checkpoints between delivery phases (commit, deploy, UAT, sign-off)
3. **Task tracker epic structure:**
   - Create epic parent task: `EPIC: <name>` in the project board
   - Create story subtasks under the epic: `[P1] STORY-XXX: <name>`, `[P2] STORY-XXX: <name>`, etc.
   - Create E2E gate subtasks: `[E2E] STORY-XXX: <name>` between delivery phases
   - All subtasks added to the project board so they appear in sections
   - Move subtasks to Backlog section initially; orchestrator advances them through Ready → In Progress → E2E Gate → Done

**Epic execution flow:**
```
Phase 1 (Epic Seed)
  → Decompose into stories (each gets its own scope: S/M/L)
  → Group stories into delivery phases (sprints)
  → Per-sprint:
      → Run stories through their individual SDLC paths (in parallel where possible)
      → Design phases can run ahead of implementation for non-blocking stories
      → E2E + Ops Integration Gate at sprint boundary
  → Repeat until all delivery phases complete
  → Phase 10 (project-level ops gate — all ops tickets resolved)
  → Retrospective (/retro) — analyze outcomes, apply SDLC improvements
  → Epic marked Done
```

**Key rules:**
- Each story follows its own scope path (Small/Medium/Large) — the epic scope only governs decomposition and orchestration
- Stories within a sprint can advance through design phases independently
- Implementation (Phase 8) respects dependency order within and across sprints
- The `implementation-plan.md` is updated after every phase completion (same cadence as `.project`)
- Transition gates between delivery phases require: commit, push, deploy, user acceptance testing, sign-off

### E2E Integration Gate

**Purpose:** Verify that a batch of completed stories work together correctly before starting the next delivery phase. This catches integration issues that per-story tests miss.

**When required:**
- Between delivery phases of an Epic (e.g., Phase 2 Accounting → Phase 3 Maintenance)
- After completing a foundation story that other stories depend on
- Before deploying a batch of stories to production

**E2E gate story structure:**
- Scope: Large (follows full 1→2→...→8b→[9,10] path)
- **Phase 1 seed defines:** refactoring ACs (cross-story cleanup) + E2E integration ACs (cross-module flows)
- **Phase 7 tests cover:** multi-module flows, data consistency across stories, API contract verification, UI integration
- **Phase 8 implements:** both the refactoring fixes and the E2E test infrastructure
- **Gate rule:** E2E story must be Done before any story in the NEXT delivery phase enters Phase 8

#### E2E Gate Ordering
E2E gate stories (e.g., `[E2E] STORY-XXX`) MUST validate real API contracts before dependent frontend stories can be marked Done. If frontend stories complete Phase 8b before the E2E gate runs:
- Each frontend story must include at least one non-mocked integration test that hits the real backend.
- Alternatively, hold frontend stories in "E2E Gate" section until the gate story validates all contracts.

**Example (from AppFolio project):**
```
STORY-062: Phase 2 E2E Integration Tests
  - 17 ACs: module refactoring & cleanup (import consistency, shared fixtures, dead code)
  - 65 ACs: E2E integration tests (ingestion→extraction→submission→verification flow)
  - Must be Done before Phase 3 stories enter Phase 8
  - Phase 3 design work may proceed in parallel
```

**Implementation plan updates:** E2E gate stories appear in the progress tracker between delivery phases, marked with a `[GATE]` indicator.

### E2E Gate Story Standard Scope (REQUIRED for every epic)

Every epic must include an E2E gate story with the following standard scope:
1. **Module refinement:** naming consistency, dead code removal, import cleanup, API envelope standardization
2. **Migration chain audit:** `alembic heads` check + merge migration if needed + rehearsal from clean DB
3. **E2E integration tests:** cross-story integration paths that individual story suites cannot validate
4. **Full-product smoke:** authenticated Playwright suite across all deployed surfaces
5. **Regression baseline:** document test counts (backend + frontend e2e) as the Phase N+1 entry baseline
6. **Operational readiness verification:** Audit every story's Phase 6 design for ops requirements (health checks, metrics, logging, alerting, runbooks). Verify each requirement was implemented. Any unimplemented ops requirement becomes a blocking ticket — the E2E gate does NOT pass until all ops tickets are resolved.
7. **Ops ticket reconciliation:** If Phase 10 identifies NEW ops concerns not caught in Phase 6 design, these are tracked as stories in the backlog and must be Done before epic close. Document any gap between Phase 6 ops requirements and Phase 10 findings in `site-reliability.md` under a "Gap Analysis" section.

This story is the epic's CLOSING story. Its SDLC path is: Large scope (`1→2→3→4→5→6→[6b,6c,6d]→7→8→8b→[9,10]`)

Epic may NOT be marked Done until this story is Done.

### Migration Chain Audit (REQUIRED as part of E2E gate story)

1. Run `cd backend && poetry run alembic heads`
2. If single head: proceed.
3. If multiple heads: create merge migration as part of E2E gate story:
   ```bash
   poetry run alembic merge heads -m "merge_multiple_heads_epic_N"
   ```
4. Run full migration rehearsal from clean DB: `alembic downgrade base && alembic upgrade head`
5. E2E gate story is NOT complete until single head is confirmed and migration rehearsal passes.

### Full-Product Authenticated Smoke (REQUIRED for epic close)

Run Playwright headless against the deployed build (staging or demo):
```bash
npm -C frontend run test:e2e
```
Minimum authenticated routes to verify:
- `/admin` (dashboard, all tabs render, no console errors)
- `/host` (dashboard, history tab, filters)
- Any new epic-specific routes (e.g., `/admin/appfolio` for Phase 2)

If any authenticated route fails: epic is NOT Done. Story-local passes are necessary but not sufficient.

### Cross-Story Integration Verification (Required at E2E Gate)

Before the E2E gate can be marked PASS, perform the following cross-story verification steps in addition to running all story test suites:

#### Shared Infrastructure Checklist
- [ ] **Auth flow end-to-end:** Log in with a test user whose JWT includes all claims required by stories in this epic. Verify the JWT is correctly read and all account-scoped API calls include the required headers.
- [ ] **Navigation consistency:** Visit every page added by stories in this epic. Verify navigation links render, active states are correct, and no routes 404.
- [ ] **Layout wrapper consistency:** Verify all new pages use the shared layout wrapper. No page should render without the nav sidebar/header that other pages use.
- [ ] **Account context propagation:** For account-scoped features, verify the same account ID is used consistently across all pages in the epic (no story uses a different account than others).
- [ ] **Empty state coverage:** Verify all new pages handle the case where the API returns empty data (no JavaScript errors, no blank screens).
- [ ] **Health check endpoints:** All services expose `/health` and `/health/ready`. Readiness probe checks all critical dependencies. Response format is consistent across services.
- [ ] **Metrics endpoint:** `/metrics` returns Prometheus-compatible output with request rate, error rate, latency histograms, and dependency health counters for all stories in this epic.
- [ ] **Structured logging:** All endpoints emit structured JSON logs with `trace_id`, `level`, `service`, `endpoint`, and `duration_ms` fields. No unstructured log output on critical paths.
- [ ] **Alerting rules:** Alert definitions exist for error rate breach, latency SLO breach, health check failure, and dependency degradation. Every alert links to a runbook.
- [ ] **Runbook coverage:** A runbook exists for every alertable condition. Runbooks include specific diagnosis steps and resolution commands (not just "investigate").
- [ ] **Post-deploy smoke tests:** Smoke test suite covers health endpoints, core API flows, and authenticated routes. Smoke test failure blocks deployment completion.

#### Cross-Story Test Verification
- [ ] **Mock URL audit:** For every `page.route()` call across all story test files, confirm the mock pattern matches the actual registered endpoint (account-scoped routes must include `accounts/*` segment).
- [ ] **JWT fixture audit:** For every story test that requires account context, confirm the test fixture JWT includes the required claims.

**Gate:** The E2E gate does NOT pass until all checklist items above are verified, in addition to all story test suites passing GREEN.

### Retrospective Feedback Loop (REQUIRED — every phase)

Every phase participates in the retrospective feedback loop. **Upstream**, each phase produces artifacts and metrics the retrospective analyzes. **Downstream**, each phase checks for pending retro proposals from prior epics before starting work.

**Universal gate:** Before starting any phase on a new epic, check for retro proposals from prior epics targeting that phase. Critical proposals MUST be applied before Phase 8; High proposals before Phase 7. See the retro agent persona for proposal status lifecycle.

| Phase | Upstream: What Retro Analyzes | Downstream: What to Check |
|-------|-------------------------------|---------------------------|
| 1 (Seed) | AC quality, scope classification accuracy | Proposals improving requirement gathering, AC templates |
| 2 (Research) | Technology/pattern research thoroughness | Proposals about research scope or missed technology areas |
| 3 (Expansion) | Approach generation completeness | Proposals about approach categories or evaluation criteria |
| 4 (Analysis) | Risk identification completeness | Proposals about risk dimensions or scoring models |
| 5 (Selection) | MVP scope sizing accuracy | Proposals about scope classification or tradeoff criteria |
| 6 (Design) | Architecture/design quality — Phase 10 design gaps feed retro | Proposals about design patterns, checklists, shared utilities |
| 6b (Security) | Threat model completeness | Proposals about threat categories or security gates |
| 6c (UX) | UX review coverage | Proposals about UX checklists or friction detection |
| 6d (Ops) | Operational readiness coverage | Proposals about ops review scope or health check patterns |
| 7 (Test Design) | Test adequacy (fix loops + defect types measure this) | Proposals about test categories, gates, or coverage rules |
| 8 (Implementation) | Error patterns, implementation quality | **HARD GATE:** All Critical proposals MUST be APPLIED before any story enters Phase 8 |
| 8b (Code Review) | Finding categories, fix loops, recurrence — primary retro data source | Proposals about review checklists or finding categories |
| 9 (Refinement) | Gap analysis, deferred findings, edge cases found late | Proposals about refinement scope or gap categories |
| 10 (Operations) | Design Gap Analysis in site-reliability.md → retro flags as Phase 6 gaps | Proposals about SLI/SLO patterns, runbook templates, dashboards |
| 11 (Pre-Deploy) | Gate effectiveness metrics | Proposals about gate criteria or scan coverage |

### Epic Retrospective (REQUIRED)

**Purpose:** After all delivery phases and E2E gates are complete, run a retrospective to analyze outcomes and propose improvements to the SDLC framework. This is a required step before marking the epic as Done.

**When to run:** After the final E2E gate is Done and all stories in the epic are complete.

**How to run:** Use `/retro` or `/retro <epic-name>`. The retrospective agent reads all code reviews, refinements, blockers, and metrics, then proposes changes to any SDLC phase or agent persona.

**Required steps (in order):**
1. Run `/retro` to initiate the Retrospective process
2. Analyze all stories (code reviews, fix loops, test counts, timeline)
3. Identify recurring patterns — any finding in 3+ stories is systemic
4. Produce `retrospective.md` and `retro-proposal.yaml` in `features/<epic>/`
5. Submit `retro-proposal.yaml` to framework owner via `/retro-apply --import`
6. Only after retrospective is complete → mark epic Done in task tracker/backlog

**What it produces:**
- `features/<epic-folder>/retrospective.md` in the **project repo** — includes full project context, metrics, findings, and a status tracker with proposed SDLC changes
- The report includes exact proposed text changes for each finding

**What it does NOT do:**
- The retrospective does NOT modify `.sdlc/` or `coding-ai-config`
- The `.sdlc` submodule is **read-only** for consuming projects
- Only the framework owner reviews retros across projects and applies changes to `coding-ai-config`

**Status tracker:** Every proposed change is tracked from `PENDING` → `REVIEWED` (framework owner approved) → `IMPLEMENTED` (committed to coding-ai-config) → `VERIFIED`. The status tracker lives in the project repo's retrospective report.

**Key rule:** The retrospective can propose changes to ANY phase (1-10), ANY agent persona, guidance docs, or templates. No phase is exempt from improvement. But proposals are just that — proposals. They are not applied automatically.

**Epic lifecycle:**
```
stories all Done → E2E + Ops gate → Phase 10 (project-level) → Stakeholder Review → Retrospective → Epic Done
```

### Epic Stakeholder Review (REQUIRED)

**Purpose:** Before the retrospective, conduct a three-way review session to validate the epic delivers on its promises. This catches UX gaps, missing requirements, and persona doc drift that automated tests can't find.

**When to run:** After E2E gate passes and Phase 10 (if applicable) is complete, but BEFORE the retrospective.

**Participants:**
1. **User (stakeholder)** — validates workflows match real operations, confirms the product solves their problem
2. **UX Strategist (`/ux persona <name>`)** — audits friction on the live product, updates persona PR/FAQ in `docs/personas/`, scores key flows
3. **Product Manager (`/pm epic`)** — verifies all ACs met, no scope gaps, success metrics are achievable

**Required steps:**
1. UX agent walks through the affected persona's daily journey on the **live product** (not mocks)
2. Key features are demoed end-to-end (specific demos listed in each epic's seed.md)
3. UX agent updates `docs/personas/<persona>.md` with any workflow changes from the implementation
4. PM identifies anything in the original seed that wasn't delivered, or new requirements discovered
5. All three participants sign off — documented in `features/<epic>/stakeholder-review.md`

**What it produces:**
- `features/<epic-folder>/stakeholder-review.md` — sign-off record with:
  - Friction scores for key flows (from UX)
  - AC verification summary (from PM)
  - User feedback and approval (from stakeholder)
  - List of persona doc updates made
  - Any follow-up items identified (become stories in the next epic or backlog)

**Invoke with:**
```
/ux persona <name>     — UX reviews the experience
/pm epic               — PM checks delivery status
/council               — full multi-perspective review if disagreement
```

**The epic is NOT Done until the stakeholder review is complete and all three participants sign off.**

**Ops gate rule:** If Phase 10 discovers ops requirements that were NOT identified during Phase 6 design, each unimplemented requirement becomes a blocking story. These stories follow the Small scope SDLC path (1 → 7 → 8) and must be Done before the epic can close. The retrospective MUST flag these as Phase 6 design gaps.

**Framework owner workflow:** See `retrospectives/README.md` in `coding-ai-config` for how to review and apply proposals from across projects.

### Retrospective Implementation Gate (REQUIRED)

After an epic retrospective is produced:

1. Triage proposals: Critical → must fix before next epic Phase 8; High → must fix before next epic Phase 7; Medium/Low → tracked in backlog
2. For each Critical/High proposal:
   - Update the target agent persona file (agents/phase-X-*.md) with the proposed_text
   - Update software-development-guidance.md if the target is process-level
   - Commit: `phase retro: [F-XXX] apply <finding> to <target>`
3. Mark the retro-proposal.yaml status for each implemented proposal: `APPLIED`

No new epic may have stories enter Phase 8 until all Critical retrospective
proposals from prior epics are APPLIED. This gate is enforced by the
orchestrating agent at epic start.

### Epic Lifecycle: Required Steps

Epic close sequence (in order, all required):

1. All stories complete Phase 8b
2. E2E gate story scope complete (migration chain audit + full regression suite)
3. Full-product authenticated smoke passes
4. **Retrospective** — produce `features/epic-<slug>/retrospective.md` and
   `features/epic-<slug>/retro-proposal.yaml`
   - Document what went well, what went wrong, recurring patterns
   - Produce proposals with IDs (F-001 through F-NNN) for each systemic issue
   - Apply Critical/High proposals to agent persona files before marking epic Done
5. Retrospective proposals status: all Critical proposals APPLIED
6. Epic marked Done in task tracker

Retrospective is NOT optional. Epic cannot be marked Done without it.

---

## Phases

| # | Name | Goal | Conditional |
|---|------|------|-------------|
| 1 | Concept & Seed | Capture idea, classify scope | Small+ |
| 2 | Research | Survey solutions | New/Large |
| 3 | Expansion | Generate options | New/Large |
| 4 | Analysis | Evaluate approaches | New/Large/Medium |
| 5 | Selection | Choose path | New/Large |
| 6 | Design | Architecture | New/Large, Medium-lite |
| 6c | UX Review | Friction, information, consistency | Medium+ |
| 7 | Test Design | Write tests first | Small+ |
| 8 | Implementation | Build solution | All |
| 8b | Code Review | Verify quality, security, spec compliance | Medium+ |
| 11 | Pre-Deploy Gate | Automated pre-deploy verification | Medium+ |
| 9 | Refinement | Polish, UAT | New/Large |
| 10 | Operational Resilience | Monitoring, dashboards, runbooks | New/Large |

### Phase 1: Concept & Seed
- Create `seed.md` (template: `templates/seed.md`)
- Create `README.md` (template: `templates/readme.md`) with project description, key links, setup instructions
- Classify scope
- For features: gather codebase context
- **Initialize `.project` Phase Routing:** Set `Scope Path` based on scope classification, set `Current Phase` to `1`, set `Current Status` to `in_progress`
- On completion: follow Phase Completion Protocol

### Phase 2-3: Research & Expansion (Conditional)
- **Phase 2:** Research Coordinator dispatches 3 parallel sub-agents: Market Scout (SaaS/vendors), Library Miner (OSS/packages), Field Reporter (community sentiment). Orchestrator deduplicates, corroborates cross-source findings, runs dependency health check.
- **Phase 3:** Expansion Coordinator dispatches 3 parallel sub-agents: Pragmatist (conservative/minimal), Futurist (scalable/innovative), Optimizer (cost/effort hybrid). Orchestrator deduplicates and verifies spectrum coverage (5-10 approaches).
- Skip if: Small, Medium, or clear approach exists

### Phase 4: Analysis (Conditional)
- Analysis Coordinator dispatches 3 parallel sub-agents: Technical (soundness + flexibility), Business (value + effort), Risk (risk profile + register). No dimension overlap. Orchestrator reconciles scores with context weights and ranks top 3.
- Medium: abbreviated (2-3 approaches)

### Phase 5: Selection (Conditional)
- Select approach with rationale
- Define MVP scope
- Skip if: Medium or smaller

### Phase 6: Design
- **Full (New/Large):** specification, architecture, API, database, implementation strategy
- **Lite (Medium):** `feature-spec.md` only
- Followed by Phase 6b: Security Review

### Phase 6b: Security Review
- Review design for security vulnerabilities
- Threat modeling, auth, authz, input validation, data protection
- Must address critical/high findings before Phase 7
- Runs in parallel with Phase 6c (both read Phase 6 design docs)

### Phase 6c: UX Review
- Review design for user experience before implementation
- Map core user flows with friction scores (target: 1-2 for core tasks)
- Audit information hierarchy — most important data most visible
- Audit consistency — terminology, actions, layout, colors, spacing
- Verify or define design system tokens
- Must address critical/high UX findings before Phase 7
- Runs in parallel with Phase 6b (both read Phase 6 design docs)
- Produce `ux-review.md`

### Phase 7: Test Design & Implementation
- Design tests in `test-design.md` (specifications)
- **Implement tests as runnable code** in `tests/` — this is not optional
- All tests must be importable and **failing (RED state)** before Phase 7 is complete
- Small: smoke tests only
- Medium+: comprehensive tests
- Coverage: 50-70%

**Phase 7 gate:** Phase 7 is NOT complete until:
1. `test-design.md` documents test specifications
2. `tests/` contains runnable test code
3. Running the tests produces failures (RED), not import errors or skips
4. Tests cover all user-facing endpoints/features relevant to the story
5. Every endpoint/method that transforms input has an output-variance test (two different inputs → two different outputs)

#### Frontend-Backend Contract Gate (required for all frontend stories)
Before Phase 7 exits, the test design MUST include:
1. **Route audit**: Extract all `/api/...` fetch paths from frontend code and verify each exists in backend router definitions. Document the mapping in `test-design.md`.
2. **Mock validation**: If Playwright tests use `page.route()` mocks, each mocked URL pattern must be verified against actual backend routes. No mock may use a URL path that doesn't exist in the backend.
3. **Response schema check**: Mock response shapes must match the actual backend response structure (envelope wrapping, field names, types).

Phase 7 is NOT complete for frontend stories until the route audit is documented and all mock URLs are validated against backend router definitions.

### Phase 8: Implementation
- **Entry gate:** All Phase 7 tests must be runnable and failing (RED). If tests only exist as markdown specs, go back to Phase 7
- **Definition of Done (REQUIRED — added 2026-05-01 retro):** A Phase 8 fix is NOT complete until the new code branch has been observed firing in production via a structured log, DB row, or HTTP response. "Tests pass" is necessary but not sufficient. If the agent cannot demonstrate the new branch executed against real prod data, the fix is unverified and a follow-on fix to the same area MUST NOT be shipped. Rationale: the 2026-05-01 cron outage shipped 3 PRs to `_get_credentials` while the actual broken function was upstream and never reached the credential code; each PR's tests passed, none of them ever ran in prod.
- **Test failure response (REQUIRED):** When a test fails, fix the implementation code to make it pass. NEVER modify a test to make it pass unless the test does not match the Phase 6 design spec or Phase 7 test design. If you believe a test is wrong, verify against `test-design.md` and the design docs before changing it. Document any test modification with: reason, which spec it conflicted with, and what was changed.
- **Hook gate:** Project must have `.claude/hooks/` configured before writing code. Copy from `templates/hooks.json` and `templates/format-on-save.sh` if not present. Required hooks:
  - `PostToolUse (Edit|Write)` — auto-format on save (ruff for Python, prettier/eslint for TS)
  - `Stop` — agent verifies tests still pass before Claude stops working
  - `SessionStart (compact)` — re-injects context after compaction
  - `Notification` — alerts user when Claude needs input
- TDD workflow: pick failing test → write code → green → refactor
- **Model:** tier-2 (default) — tier-1 requires explicit approval
- Commit after each logical unit
- **Chunk work:** Never implement more than one function/endpoint per prompt. Commit after each.
- **Stub detection gate (REQUIRED before Phase 8 complete):** Keyword scan clean, output-variance tests pass, semantic review complete (see `agents/phase-8-implementation.md`)

#### Frontend Integration Verification (required for all frontend stories)
Before a frontend story exits Phase 8:
1. Run Playwright E2E tests against the **real local backend** (not mocks) at least once.
2. Fix any URL mismatches, response format differences, or missing endpoints discovered.
3. Document any endpoints that require backend changes as cross-story dependencies.

This prevents the silent failure mode where mocked tests pass but real API calls fail due to URL or schema mismatches.

**Deployment gate (for infra/deployment stories):**
1. All smoke tests must pass against the live environment after deploy
2. **API:** `pytest -m smoke` — core endpoints, auth, health checks
3. **Frontend:** `npx playwright test --grep @smoke` — homepage load, login flow, core user journey (headless only)
4. Every user-facing endpoint must be verified — not just health checks
5. If any smoke test fails, the deployment is not complete

**Deployment authorization (HARD RULE):**
- **Production:** Only the repository owner (`markoreta`) or approved CI/CD pipelines may deploy. AI agents MUST NOT execute production deploy commands (`az containerapp update`, `terraform apply`, `kubectl apply`, or GitHub Actions `workflow_dispatch` targeting production). Agents produce the Phase 11 gate report; the human triggers the deploy.
- **UAT:** Agents and CI/CD may deploy to UAT environments (dev subscription) freely. UAT deploys are triggered by pushes to `epic/*` or `dev` branches.
- **Local:** Agents may run `docker compose up/down` for local dev/test environments without restriction.

**Parallel Story Execution (Large scope, 3+ stories):**

When `orchestration.parallel_stories: true` and the project has 3+ independent stories, Phase 8 runs stories in parallel using git worktree isolation. See `agents/phase-8-implementation.md` for full rules, prerequisites, ownership matrix, boundary enforcement, and merge gate steps.

**Phase 8 status values:**

| Status | Meaning |
|--------|---------|
| `pending` | Phase 8 not started |
| `in_progress` | Sequential execution (normal) |
| `parallel_active` | Worktree agents running stories in parallel |
| `merging` | All stories complete, merge step in progress |
| `merge_blocked` | Merge step failed (test failures, conflicts) |
| `complete` | All stories merged, full test suite passing |

### Phase 8b: Code Review (Medium+ Scope)
- Orchestrator launches sub-agents in 2 waves:
  - **Wave 1 (parallel):** Architect (tier-1), Skeptic (tier-2), Simplifier (tier-2), Rule Reviewer (tier-2), QA Preflight* (tier-2)
  - **Wave 2 (sequential, after auto-fix):** Browser Tester* (tier-2) — executes Playwright e2e flows
  - *\* Frontend projects only. Detection: `config.yaml` tech_stack.frontend set OR package.json + .tsx files exist.*
- Orchestrator deduplicates findings, triages, and runs auto-fix loop (max 2 iterations) for localized Critical/High bugs
- **Every finding requires a disposition** — fixed, deferred (backlog item created), or won't-fix (rationale documented)
- Deferred Medium/Low issues must be tracked as task tracker items or sub-tasks linking back to the review report by finding ID (e.g., "STORY-002 M-1")
- **Gate:** All critical/high issues resolved AND all findings have a recorded disposition AND frontend projects have browser tests passing before Phase 9 or Done
- **Browser Tester contract validation (frontend stories):** Run Playwright tests against both mocked AND real backend endpoints. Compare pass/fail results. Flag any test that passes with mocks but fails against real backend as a "contract violation" requiring immediate fix before Phase 8b exits.
- See `agents/phase-8b-code-review.md` for orchestrator workflow and sub-agent configuration

### Phase 10: Operational Resilience (Conditional)
- Produce `site-reliability.md` — single source of truth for ops
- Define SLIs/SLOs with error budgets
- Health check endpoints: `/health`, `/health/ready`, `/health/live`, `/health/detailed`
- Metrics instrumentation (Prometheus format): request, error, business, dependency, resource
- Dashboard specifications: executive, service overview, dependency, infrastructure
- Alerting strategy: severity levels, routing, runbook links
- Structured logging with correlation IDs
- Incident response runbooks for every alert type
- External uptime monitoring and synthetic checks
- Deployment safety: canary, rollback, post-deploy smoke tests
- **Post-deploy smoke tests (REQUIRED):** API smoke tests (`pytest -m smoke`) + Playwright e2e smoke tests (`npx playwright test --grep @smoke`) for frontend projects. Smoke tests reuse Phase 7 test code tagged `@smoke`. A deployment is not complete until all smoke tests pass.
- **CI/CD gate integration (REQUIRED):** Every operational requirement that can be automated MUST have a corresponding CI/CD pipeline gate (health probe, smoke test, migration chain check, alert rule validation). Document the gate mapping in `site-reliability.md`. If no pipeline exists, document gates as requirements for a future pipeline story.
- **Model:** tier-1 (always use most capable reasoning model)
- **Gate:** Every alert has a runbook. Every SLI has an SLO. Every dashboard panel has a purpose. Post-deploy smoke tests are defined and automated. CI/CD gates enforced for all automatable operational requirements.

### Infrastructure & Deployment as Stories

Infrastructure, deployment, and DevOps work MUST follow the same SDLC phases as feature work. These are not ad-hoc tasks — they are stories that get scoped, designed, tested, and tracked.

**Examples of infra stories:**
- Cloud deployment setup (Cloud Run, Kubernetes, etc.)
- CI/CD pipeline
- Database provisioning (Neon, RDS, etc.)
- Monitoring/observability
- Environment management (staging, production)

**Process:**
1. Create a story in the task tracker (tag: `tech-debt` or `story`)
2. Classify scope (deployment infra is typically Medium+)
3. Follow the phase path for that scope — seed, design, test, implement
4. Design phase should cover: architecture decisions, cost analysis, security, rollback strategy
5. Test phase (Phase 7) should cover: deploy scripts, health checks, migration verification, smoke tests — **as runnable code, not just markdown specs**. Tag smoke-suitable tests with `@smoke` (pytest marker) or `@smoke` (Playwright grep tag) so Phase 10 can reuse them for post-deploy verification.
6. Implementation phase (Phase 8) must run smoke tests against live environment after deploy — API (`pytest -m smoke`) and frontend (`npx playwright test --grep @smoke`, headless only)
7. Track in `development-tasks.md` and `.project` like any other story

**Do NOT:**
- Commit infra code without a tracked story
- Skip design for deployment architecture
- Treat infra as "just scripts" that don't need the SDLC process
- Deploy without runnable smoke tests — manual curl checks are not a substitute for automated tests
- Mark a deployment story as complete if any smoke test fails

---

## Model Policy

See `CLAUDE.md` for the authoritative model policy table (model + effort level per phase).

### Phase 11: Pre-Deploy Gate (Conditional — Medium+ scope)

- Automated verification that the build is safe to deploy before any code ships
- **Runs after Phase 8b (Code Review) and before Phase 9/10 or Done**
- Nine required checks (all must PASS — no exceptions):
  1. **Container image CVE scan** — `trivy image` or `grype`, fail on Critical/High
  2. **Dependency audit** — `pip-audit` / `npm audit`, fail on known vulnerabilities
  3. **Secrets scan** — `gitleaks` or `trufflehog`, fail on any detected secret
  4. **Infrastructure drift** — `terraform plan` / Bicep what-if, flag unexpected changes
  5. **Monitoring health** — `/health`, `/health/ready`, `/metrics` endpoints respond; alert rules configured
  6. **Adapter connections** — DB, cache, external APIs all reachable
  7. **Migration chain** — `alembic heads` shows exactly one head (no branched chain)
  8. **Smoke test dry-run** — `pytest -m smoke` + `npx playwright test --grep @smoke` pass
  9. **CI/CD gate verification** — pipeline config exists and all operational gates are active (health probe, smoke tests, migration check)
- **Deliverable:** `predeploy-gate.md` — gate report with evidence for each check
- **Automation:** `tests/predeploy/` directory with scripts for each check
- **Model:** tier-2 (automated checks, not deep reasoning)
- **Advance type:** gate — requires **explicit user approval** before deployment
- **Gate:** All 9 checks PASS + user has confirmed "Approved to deploy" on the gate report

### Phase 9: Refinement (Conditional)
- UAT automation
- Polish, edge cases
- Coverage target: 80%
- **Model:** tier-1 (always use most capable reasoning model)
- **8b deferred items:** Review `code-review-8b.md` for any deferred Medium/Low findings — resolve or explicitly carry forward with rationale

---

## Versioning

**Format:** `MAJOR.MINOR.PATCH` (semver)

### Version Bump Rules

| Bump | Trigger | Examples |
|------|---------|----------|
| **Major (X)** | Breaking changes, major architectural shifts, public API contract changes | 0.x→1.0.0 at first production release; 1.x→2.0.0 on breaking API change |
| **Minor (Y)** | New features, new endpoints, new capabilities — any user-visible addition | New story implemented, new integration added, new UI feature |
| **Patch (Z)** | Bug fixes, doc updates, dependency patches, config changes, refactors with no user-visible change | Hotfix, typo correction, dependency security patch |

### When to Bump

| Event | Bump Type | Who | Where |
|-------|-----------|-----|-------|
| **Epic completes** (all stories merged to main) | **Minor** (Y) | Repository owner or orchestrator script | `.project`, `pyproject.toml` / `package.json`, `CHANGELOG.md` |
| Standalone bugfix merged | **Patch** (Z) | Repository owner or CI/CD | `.project`, `pyproject.toml` / `package.json` |
| Standalone hotfix (no epic) | **Patch** (Z) | Repository owner | `.project`, `pyproject.toml` / `package.json` |
| First production release | **Major** to 1.0.0 | Repository owner | `.project`, `pyproject.toml` / `package.json` |
| Breaking API/schema change | **Major** (X) | Repository owner | `.project`, `pyproject.toml` / `package.json` |

**Version bumps happen at epic completion, not per-story.** Individual stories add entries to `## [Unreleased]` in CHANGELOG.md during Phase 8. When all stories in an epic are merged, tested, and approved, the repository owner bumps the version, promotes `[Unreleased]` to `[X.Y.Z]`, and creates a git tag. This gives clean rollback points per epic and business-readable release history.

### Version Sync (REQUIRED)

All version references MUST be updated atomically in a single commit:
- `.project` → `Version` field and new row in `Version History` table
- `pyproject.toml` → `version` field (Python projects)
- `package.json` → `version` field (Node.js projects)
- `CHANGELOG.md` → new entry under `## [X.Y.Z]` header (see Changelog section)

### Git Tags

After a **minor (Y) version bump**, create a git tag:
```bash
git tag -a vX.Y.Z -m "Release X.Y.Z — <one-line summary>"
```
Patch (Z) bumps do NOT require a git tag unless they are standalone hotfix releases.

### Changelog

Every project MUST maintain a `CHANGELOG.md` at the project root, following [Keep a Changelog](https://keepachangelog.com/) format.

**When to create a new entry:**
- **Minor (Y) bump** → create a new `## [X.Y.Z] - YYYY-MM-DD` section with all changes since last minor release
- **Patch (Z) bump** → add changes under the existing `## [Unreleased]` section (they roll into the next minor release entry)
- **Major (X) bump** → create a new entry, highlight breaking changes prominently

**Changelog categories:** Added, Changed, Deprecated, Removed, Fixed, Security

**Phase responsibilities:**
- **Phase 8** — append entries to `## [Unreleased]` as features/fixes are implemented (no version bump)
- **Phase 11** — verify CHANGELOG.md has entries for all merged stories, flag defaults OFF, no UI leakage
- **Phase 9** — review changelog for completeness, clarity, and user-facing accuracy
- **Epic completion** — repository owner promotes `[Unreleased]` to `[X.Y.Z]`, bumps version, creates git tag

### Multi-Worker Versioning

Version field in worktree `.project` files is a stale snapshot from worktree creation time. Worktree agents MUST NOT read, compare, or reason about version numbers — they will differ from the root `.project`. **Version bumps happen exclusively at merge time in the main branch.** The merge agent reads the root `.project` version, increments it, and commits the bump.

Include reasoning in version history — every row in the Version History table must explain WHY the version changed, not just what changed.

---

## Phase Transitions

**Requirements:** Outputs complete, user approval, no blockers.

**Gates by scope:** See phase paths in `CLAUDE.md`.

### Phase Completion Protocol

When a phase is completed, update **all tracking documents**. This applies to **every scope, including Trivial** — no exceptions.

**Documentation sync checklist (EVERY phase completion — no exceptions, including Trivial):**
- [ ] **Git push to remote** — all commits pushed to the remote branch. Local-only commits are not acceptable.
- [ ] `.project` — Phase Routing updated (see below)
- [ ] `.project` — Version: do NOT bump per-story. Add CHANGELOG entries under `[Unreleased]` only. Version bumps happen at epic completion.
- [ ] `backlog.md` — Story status reflects current phase
- [ ] `development-tasks.md` — Task statuses current
- [ ] `CHANGELOG.md` — Entries added (Phase 8), reviewed (Phase 9), verified (Phase 11)
- [ ] **Task tracker — status updated** and **summary comment posted** (see `trackers/` for platform-specific commands)

**Task tracker is NOT optional.** Every agent persona includes this as a workflow step. The `/next` skill verifies the task tracker is current before advancing. If the task tracker is stale, update it before proceeding.

### Ticket Comment Policy (REQUIRED)

Every phase completion MUST post a summary comment to the story's tracker ticket. This ensures tickets are useful standalone — anyone reading the ticket understands the story without checking local files.

**Required comments by phase:**
| Phase | Comment Content |
|-------|----------------|
| 1 (Seed) | Problem statement, scope, key ACs, key decisions |
| 5 (Selection) | Selected approach, rationale, MVP scope, timeline, key risks |
| 7 (Test Design) | Test count, RED/GREEN breakdown, coverage areas |
| 8 (Implementation) | Tests passing, key components built, regressions |
| 8b (Code Review) | Finding counts by severity, auto-fixes applied |

Other phases (2, 3, 4, 6, 6b, 6c, 9, 10): Post a 2-3 sentence summary if the phase produced significant decisions or findings.

**Format:** Use Markdown formatting. Include section headers and bullet lists for scannability.

1. **Update Phase Routing section:**
   - Add current phase number to `Completed Phases` (comma-separated, e.g., `1, 7`)
   - Set `Current Phase` to the next step in the Scope Path (may be a single phase or a parallel group)
   - Set `Current Status` to `pending` (or `parallel_active` if next is a bracketed group)
   - Set `Next Phase` to the step after that (or `Done`)
   - Update `Last Updated` to today's date
2. **Add row to Phase History table** with phase name, start/end dates, status, and summary
3. **Commit** the `.project` update: `phase <N>: update .project — phase <N> complete, next: <N+1>`
4. **Determine advance behavior** based on the completed phase's `advance` category:
   - **auto** (6b, 6c, 8b): Proceed to next phase immediately, no user input needed
   - **confirm** (2, 3, 4, 5, 6, 7, 9, 10): Show summary of outputs, ask "Proceed to Phase X?"
   - **gate** (1, 8): Show deliverables, require explicit user review and approval
5. **Check context group boundary** — if the next phase is in a different context group, tell the user to `/clear` (or use `/next` to handle automatically)
6. **Guide the user to the next step (REQUIRED — minimize user effort):**
   - **Same context group (no /clear needed):** Apply the advance category directly —
     - **auto:** proceed immediately, no user input
     - **confirm:** ask `"Continue to Phase X for STORY-016?"` — user confirms yes/no
     - **gate:** show deliverables, wait for approval, then continue
   - **Different context group (/clear needed):** tell the user `"Please /clear, then /next"` (agent auto-resolves the story after clear)
   - **Story done:** `"Story STORY-016 complete. Run /next to auto-claim the next story."`
   - The user should NEVER need to type a story ID — `/next` auto-resolves

**Example after completing Phase 1 (Medium scope):**

```markdown
## Phase Routing
| Field | Value |
|-------|-------|
| Scope Path | `1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done` |
| Completed Phases | 1 |
| Current Phase | 4 |
| Current Status | pending |
| Next Phase | 6 |
| Context Strategy | grouped |
| Last Updated | 2026-02-14 |
```

**Example during a parallel group (Large scope, [6b, 6c, 6d] active):**

```markdown
## Phase Routing
| Field | Value |
|-------|-------|
| Scope Path | `1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → [9, 10] → Done` |
| Completed Phases | 1, 2, 3, 4, 5, 6 |
| Current Phase | [6b, 6c, 6d] |
| Current Status | parallel_active |
| Next Phase | 7 |
| Context Strategy | grouped |
| Last Updated | 2026-02-14 |

### Parallel Group Status
| Phase | Status | Agent | Result |
|-------|--------|-------|--------|
| 6b | complete | Security Reviewer | 0 critical, 1 medium |
| 6c | in_progress | UX Strategist | — |
```

**Example during Phase 8 parallel story execution:**

```markdown
## Phase Routing
| Field | Value |
|-------|-------|
| Scope Path | `1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → [9, 10] → Done` |
| Completed Phases | 1, 2, 3, 4, 5, 6, 6b, 6c, 6d, 7 |
| Current Phase | 8 |
| Current Status | parallel_active |
| Next Phase | 8b |
| Context Strategy | grouped |
| Last Updated | 2026-02-14 |

### Story Parallel Status (Phase 8)
| Story | Branch | Status | Tests Passing | Commits | Result |
|-------|--------|--------|---------------|---------|--------|
| Auth | phase-8/auth | complete | 8/8 | 4 | success |
| Users | phase-8/users | in_progress | 3/5 | 2 | — |
| Items | phase-8/items | complete | 6/6 | 3 | success |
```

### Story Completion Protocol

When a story reaches its **final phase** (the last phase before "Done" in the scope path), perform ALL of the following before telling the user the story is complete:

1. **Update task tracker** — move story to Done section and mark as completed (see `trackers/` for platform-specific commands).

   Asana example:
   ```bash
   # Move to Done section
   cai asana-api.sh move "<task_gid>" "<done_section_gid>"
   # Mark task as completed (REQUIRED — section move alone is NOT sufficient)
   cai asana-api.sh complete "<task_gid>"
   ```

2. **Update `backlog.md`:**
   - Move story from In Progress to Done section
   - Add `Completed` date field to the story metadata table
   - Mark all acceptance criteria as `[x]`
   - Remove stale notes (e.g., "8b review pending", "in progress")

3. **Update `.project`:**
   - Set Current Phase Status to `complete`
   - Add version history entry with summary
   - Update Pending Actions (mark story tasks as checked)

**Final phases by scope:**

| Scope | Final Phase |
|-------|-------------|
| Trivial | 8 |
| Small | 8 |
| Medium | 8b |
| Large/New | [9, 10] (both must complete) |

**Anti-pattern (CRITICAL — applies to ALL scopes, including Trivial):**
Updating some docs but forgetting others. **Every phase transition and story completion** must update ALL of the following — no exceptions regardless of project size:
- `.project` — phase routing, version history
- `backlog.md` — story status, acceptance criteria
- `development-tasks.md` — task status
- Task tracker — status, section move, completion flag

Missing even one creates drift that compounds across phases. Treat these four as an atomic unit.

---

### Continue Protocol

When the user says **"continue"**, **"next step"**, **"start next phase"**, or uses **`/next`**:

1. Read `.project` → Phase Routing section
2. Confirm `Current Phase` and `Current Status`
3. **Single phase** (`Current Phase` is a number like `4`):
   - If status is `pending`: begin the phase
   - If status is `in_progress`: resume the phase (check deliverables for partial work)
   - Read the agent persona from `agents/phase-X-*.md` for the current phase
   - Adopt that persona and produce the phase deliverables
4. **Parallel group** (`Current Phase` is bracketed like `[6b, 6c, 6d]`):
   - If status is `pending` or `parallel_active`: check Parallel Group Status table
   - Launch incomplete phases as Task subagents (each reads its agent persona + input docs)
   - Collect results, update Parallel Group Status
   - If any phase has critical/high findings: pause for resolution
   - When all phases complete: advance past the group
5. When done, follow the Phase Completion Protocol above
6. **Check if `/clear` is needed** — compare the context group of the completed phase vs the next phase. If different, tell the user to `/clear`. If same, proceed directly.

This eliminates the need to re-explain context after clearing — `.project` carries the full routing state. Use `/next` to automate the advance logic.

---

## LLM Council

**Service:** `~/projects/llm-council` — Start with `./start.sh`

**Endpoints:** Backend `:8001`, Frontend `:5173`

**Tiers:** premium, economical, free (set in `config.yaml`)

**When to use:**
| Transition | Value |
|------------|-------|
| 4→5 | High |
| 6→7 | High |
| 5→6, 8→9 | Optional |

**Pattern:** Stage 1 (opinions) → Stage 2 (cross-review) → Stage 3 (synthesis)

Use `/council` skill to invoke.

---

## External API Write Safety (ZERO TOLERANCE — BUSINESS CRITICAL)

**No test, local development run, ad-hoc curl, or agent-initiated request may EVER make a real call to an external third-party API in any environment other than production with explicit user authorization.**

This is a universal rule that applies to ALL projects, ALL models, ALL agents, and ALL phases. It is not project-specific — it applies everywhere external write APIs exist.

### Why this exists

External API calls (e.g., Amazon Ads `PUT /v2/portfolios`) modify live production data with no rollback. A test that accidentally passes through authorization layers and reaches the real HTTP client can cause irreversible damage: modified budgets, paused campaigns, corrupted state.

Tool-layer abstractions (MCP adapters, service modules) are NOT safe boundaries — they make real HTTP calls. REST-layer guards (auth, write guards, permission checks) protect against *unauthorized* writes, not against *authorized test writes that reach the real client*.

### Mandatory phase gates for write-path stories

| Phase | Gate |
|-------|------|
| **6b (Security Review)** | MUST include "External API Isolation" section confirming how tests are blocked from external APIs |
| **7 (Test Design)** | MUST include at least one test asserting zero outbound HTTP calls to external API domains |
| **8 (Implementation)** | External HTTP clients MUST be injected via DI; test/local mode MUST use mock adapters |
| **8b (Code Review)** | Reviewer MUST verify no code path allows test traffic to reach external APIs |
| **11 (Pre-Deploy Gate)** | MUST verify: (a) test isolation flags are OFF in production, (b) test environments cannot reach production APIs |

### Rules for local testing

1. **Never `curl` a running local server's write endpoints** without confirming downstream HTTP clients are mocked or blocked.
2. When testing write endpoints locally, use one of:
   - `TESTING=1` env var with mock adapters injected
   - Network-level block on external API domains (e.g., `/etc/hosts`, firewall rule)
   - A dedicated test harness with stubbed HTTP clients (e.g., `respx`, `httpx` mocks)
3. **If unsure whether a code path reaches an external API, assume it does.** Trace the call chain to the HTTP client before testing.

---

## Hooks (Quality Gates)

Every project MUST configure quality gates before Phase 8 begins. In Claude Code, use hooks; in other CLIs (Gemini/Codex), use equivalent automation (for example pre-commit, CI checks, or local scripts) to enforce the same gates deterministically.

**Claude setup:** Copy `templates/hooks.json` into `.claude/settings.json` (merge with existing settings). Copy `templates/format-on-save.sh` to `.claude/hooks/` and `chmod +x`.

**Required hooks:**

| Hook | Event | Purpose |
|------|-------|---------|
| Auto-format | `PostToolUse (Edit\|Write)` | Run formatter after every file edit |
| Test verification | `Stop` | Agent verifies tests pass before session ends |
| Context recovery | `SessionStart (compact)` | Re-read CLAUDE.md and .project after compaction |
| Notification | `Notification` | macOS alert when the agent needs attention |

**Optional hooks (recommended for Large scope):**

| Hook | Event | Purpose |
|------|-------|---------|
| Security scan | `PostToolUse (Edit\|Write)` | Run bandit/semgrep on edited Python files |
| Protected files | `PreToolUse (Edit\|Write)` | Block edits to migration files, .env, etc. |

**Tool dependencies by stack:**
- Python: `ruff` (lint + format), `bandit` (security)
- TypeScript: `prettier` (format), `eslint` (lint)
- Both: `semgrep` (pattern-based security scanning)

Install required tools in Phase 8 setup before writing code.

---

## Config

Each project: `config.yaml` (template: `templates/config.yaml`)

Key settings:
- `project.scope` — determines phase path
- `council.enabled` — LLM council on/off
- `council.tier` — model tier
- `skills.auto_sync_backlog` — sync on session start
- `orchestration.context_strategy` — `strict`, `grouped`, or `minimal`
- `orchestration.auto_advance` — enable auto/confirm/gate categories
- `orchestration.parallel_execution` — enable parallel groups
- `orchestration.parallel_stories` — enable parallel story execution in Phase 8 (worktree isolation)
- `orchestration.parallel_stories_min` — minimum story count for parallel execution (default: 3)
- `orchestration.advance_overrides` — per-phase category overrides
- `orchestration.multi_worker` — enable multi-worker story processing (multiple humans/agents)
- `orchestration.max_workers` — maximum concurrent workers per project (default: 5)
- `orchestration.claiming` — story claiming mechanism: `assignee` (task tracker) or `branch` (git)
- `orchestration.worker_id` — override auto-detected worker identity

---

## Orchestration

### Advance Categories

See AGENTS.md § Hard Stop Rules for advance category definitions (auto/confirm/gate). Configurable per-project via `config.yaml` `advance_overrides`.

### Context Strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `strict` | `/clear` between every phase | Legacy behavior, maximum isolation |
| `grouped` | `/clear` between context groups only | Default — balances isolation and flow |
| `minimal` | `/clear` only before and after Phase 8 | Fast iteration, experienced users |

Set in `config.yaml` under `orchestration.context_strategy`. Missing config defaults to `strict` (backwards compatible).

### Parallel Execution

Bracket notation `[A, B]` in scope paths means phases run concurrently:

**`[6b, 6c, 6d]` — Security + UX + Ops Review:**
- All three run as Task subagents reading Phase 6 design docs
- Each produces its review file independently (`security-review.md`, `ux-review.md`, `ops-review.md`)
- If any finds critical/high issues, pause for resolution before Phase 7

**`[9, 10]` — Refinement + Operations:**
- Phase 9 runs in main session (modifies code)
- Phase 10 runs as Task subagent (produces `site-reliability.md` only)
- Both must complete before Done

**Phase 8 parallel stories** — See `agents/phase-8-implementation.md` for full rules (worktree isolation, ownership matrix, merge gate).

### `/next` Skill

The `/next` skill automates phase advancement:
1. Read `.project` Phase Routing
2. **Verify task tracker is current** — check task section matches `.project` status; update if stale
3. If current phase complete → determine next step from scope path
4. If next is sequential: apply advance category (auto/confirm/gate)
5. If next is parallel group: launch subagents for each phase
6. If `/clear` needed (group boundary): tell user, update `.project`
7. If no `/clear` needed: proceed directly
8. **Update all four tracking docs** — .project, backlog.md, development-tasks.md, task tracker (atomic)

See `skills/next/SKILL.md` for full implementation.

---

## API Design Standards

**Error response standard:** All API errors MUST use RFC 7807 Problem Details format (`application/problem+json`). See `templates/backend/core-exceptions.py` and `templates/backend/main.py` for the reference implementation.

---

## Lessons Learned

Accumulated from project implementations. Review before starting new projects.

### Debugging Discipline (2026-03-31 incident)

- **Write a failing test before fixing.** If you can't reproduce the error in a test, you don't understand the bug. The test is the acceptance criterion — not a manual check.
- **Never guess error causes.** Always get the actual exception from logs/traces before forming a hypothesis.
- **Never repeat a disproven hypothesis.** If a fix didn't work, that theory was wrong — move on.
- **Add debug logging before fixing.** So the next failure is instantly diagnosable.
- **Verify code changes are loaded.** Docker volume mounts don't auto-reload Python without `--reload`. The `./src:/app/src` and `./static/dashboard:/app/static/dashboard` mounts in docker-compose.yml mean: frontend changes need `npx vite build`, backend changes need `docker restart`.
- **One bug per cycle.** Fix → restart → test → read logs → fix next. Don't stack guesses.
- **Incident:** 502 on portfolio writes was misdiagnosed as "read-only mode" repeatedly. Actual bugs: missing import, wrong API URL format, wrong payload structure, wrong enum case, null cache. Each only discoverable from the actual traceback.

### Python / FastAPI

- **passlib is abandoned:** passlib has had no releases in 4+ years and is incompatible with bcrypt 5.x — use `pwdlib[argon2]` for password hashing (argon2 is the OWASP-recommended algorithm; pwdlib is actively maintained)
- **Poetry package-mode:** Set `package-mode = false` in `pyproject.toml` when project has no README.md. **Prefer `uv`** over Poetry for new projects — faster dependency resolution, built-in lockfile, simpler config
- **pydantic-settings extra vars:** Add `extra="ignore"` to `SettingsConfigDict` when `.env` has variables not defined in Settings class
- **Pydantic Decimal serialization:** `Decimal("450000.00")` serializes as `"450000.0"` — use `float()` in test assertions
- **`.env` localhost vs Docker:** Use `localhost` in `.env` for local dev/testing; override with Docker service names in `compose.yaml` `environment:` block (Docker Compose v2 uses `compose.yaml`; the `version:` field is deprecated and should be omitted)

### SQLAlchemy / Alembic

- **Async test event loops:** Use `NullPool` + function-scoped `db_session` fixture (create engine per test) to avoid event loop conflicts with pytest-asyncio
- **Module-level engines:** Module-level `create_async_engine()` causes event loop issues in async tests — test fixtures must create their own engine
- **TSVECTOR triggers:** `Base.metadata.create_all` does NOT create DB triggers — create triggers in Alembic migrations, or set search_vector in service layer via raw SQL UPDATE
- **JSONB `@>` operator:** Needs explicit PostgreSQL cast — use `sa_text(f"'[...]'::jsonb")`, not `cast()` which produces VARCHAR and errors
- **Identity map caching:** SQLAlchemy identity map caches stale objects — call `refresh()` + `expire()` before re-querying with `selectinload` after mutations
- **conftest model imports:** conftest.py must import all models for `Base.metadata.create_all` to discover and create all tables

### Docker / Infrastructure

- **Alembic in Docker:** `alembic/env.py` needs `sys.path.insert(0, ...)` to find the app module when running inside Docker containers
- **celerybeat-schedule:** Runtime file generated by Celery Beat — add to `.gitignore`
- **Docker Compose v2:** The `version:` field in compose files is deprecated and ignored — omit it. Use `compose.yaml` (not `docker-compose.yml`). The `docker-compose` CLI is replaced by `docker compose` subcommand
- **uv for Python packaging:** `uv` is the recommended Python package manager for new projects — 10-100x faster than pip/Poetry, built-in lockfile (`uv.lock`), replaces pip, pip-tools, virtualenv, and Poetry in one tool

### Auth / Security

- **PyJWT over python-jose:** python-jose is abandoned (4+ years, no releases). Use `PyJWT[crypto]` — actively maintained, same JWT functionality, API nearly identical
- **pwdlib over passlib:** passlib is abandoned (4+ years). Use `pwdlib[argon2]` — OWASP recommends argon2 over bcrypt for new projects


### MCP Server Patterns

**Starter template:** `templates/mcp-server/` — includes server.py (with identity middleware), auth helpers, API client (with auto-pagination), Docker Compose, token refresh script. Copy and customize for new projects.

**Key rules (implementation in template):**
- No MCP SDK auth — ASGI identity middleware, never returns 401
- Module-level `_last_user_id`, not contextvars (SDK tool tasks don't inherit context)
- `.mcp.json` type `"http"`. Middleware falls back to `.mcp.json` for stale client tokens
- Token refresh: `*/45 * * * *` cron. Auto-refresh in `get_credentials()` DB path
- Direct httpx, not SDK wrappers. Auto-pagination. Graceful degradation
- `async with db() as session:` everywhere
- Middleware wraps app LAST. Health check no auth. `.mcp.json` Docker volume mount
- Tool docstrings: business purpose, when to use vs alternatives, params with examples, response shape
- Usage dashboard: React SPA (audit logs, stats, config, health)
- Phase 6.5 Auth Spike: verify auth end-to-end before writing tools

## Test Isolation with Module-Level Dependency Injection

When a server module injects dependencies into tool modules at import time (e.g., `sp_tools.rate_limiter = _rate_limiter`), this can break test isolation if `src.server` is imported during test collection.

**Required pattern:** Use `_inject_if_none()` — only set the module attribute if it is currently None. This prevents overwriting test-patched values.

```python
def _inject_if_none(mod, attr, val):
    if getattr(mod, attr, None) is None:
        setattr(mod, attr, val)
```

**Test conftest pattern:** Save and restore module globals around each test using a fixture.

---


### Testing

- **pytest-asyncio strict mode:** As of v1.0, default mode is `strict` — use `@pytest_asyncio.fixture` for async fixtures. Set `asyncio_mode = "strict"` explicitly in `pyproject.toml`
- **pytest-asyncio loop scope:** Set `asyncio_default_fixture_loop_scope = "function"` in pytest config to avoid deprecation warnings about event loop scope
- **Test fixture date stability:** Test fixtures MUST NOT use `datetime.now()` combined with hardcoded comparison dates — hardcoded dates become stale as time advances, causing test failures unrelated to code changes. Use relative dates (`datetime.now() - timedelta(days=30)`) consistently, or a single fixed anchor constant (`BASE_DATE = datetime(2026, 1, 1)`) used throughout the fixture suite — never mix `datetime.now()` with hardcoded dates

### Frontend

- **Tailwind v4 CSS-first config:** Tailwind v4 uses CSS-based configuration (`@theme` in CSS) instead of `tailwind.config.js`. Do not create a JS config file for new v4 projects
- **ESLint flat config (mandatory):** ESLint v10 removed legacy `.eslintrc.*` format. All projects must use flat config (`eslint.config.mjs`)
- **Zod v4:** Ground-up rewrite with 2-7x faster parsing and 57% smaller core. New projects should use Zod v4 directly
- **Frontend mock drift (2026-03-15):** UI Redesign stories (063-068) passed all phases with Playwright mocks using wrong API URLs (`/accounting/gl` vs real `/transactions/gl`). Root cause: SDLC allowed frontend-only stories to mock all backend APIs without validating mock URLs against actual backend routes. Fix: Added Frontend-Backend Contract Gate to Phase 7, real-backend integration run to Phase 8, and contract validation to Phase 8b Browser Tester role.
