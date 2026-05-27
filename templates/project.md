# Project State

## Phase Routing
| Field | Value |
|-------|-------|
| Scope Path | `<e.g., 1 → 7 → 8 → Done>` |
| Completed Phases | — |
| Current Phase | — |
| Current Status | pending |
| Next Phase | — |
| Context Strategy | grouped |
| Last Updated | <YYYY-MM-DD> |

### Parallel Group Status
> Only populated when a parallel group (e.g., `[6b, 6c, 6d]`) is active. Remove rows when group completes.

| Phase | Status | Agent | Result |
|-------|--------|-------|--------|

### Story Parallel Status (Phase 8)
> Only populated when Phase 8 runs in parallel mode (`orchestration.parallel_stories: true`, 3+ stories). Remove rows when merge completes.

| Story | Branch | Status | Tests Passing | Commits | Result |
|-------|--------|--------|---------------|---------|--------|

### Story Status (Multi-Worker)
> Only populated when `orchestration.multi_worker: true` in `config.yaml`. Tracks all active stories across workers.

| Story | Assignee | Scope | Current Phase | Status | Branch |
|-------|----------|-------|---------------|--------|--------|

> **Multi-worker mode:** Each row tracks one story being worked on by a specific worker. `Assignee` is the worker identity (human name, agent session, or AI model name). `Branch` is the worktree branch for this story. Only the orchestrator session updates this table — workers in worktrees do NOT write to `.project`.
>
> **Single-worker mode:** When `multi_worker: false` (default), the Phase Routing table above is the source of truth. This table is unused.

> **On phase completion:** Move current phase to Completed Phases, set Next Phase as Current Phase, set Current Status to `in_progress`. When user says "continue", "next step", or `/next` after `/clear`, read this section to determine what to do.
>
> **Parallel groups:** When Current Phase is a bracketed group (e.g., `[6b, 6c, 6d]`), set Current Status to `parallel_active` and track each phase in the Parallel Group Status table. The group is complete when all phases show `complete`. If any phase has critical/high findings, set Current Status to `blocked` until resolved.

## Project Overview
| Field | Value |
|-------|-------|
| Mode | <new_project\|feature_update> |
| Scope | <trivial\|small\|medium\|large> |
| Feature Name | <name if feature update> |
| Target Output | <what we're building/changing> |
| Target Audience | <who it's for> |
| Success Criteria | <how we measure success> |

## Codebase Context (Feature Updates)
| Aspect | Details |
|--------|---------|
| Affected files | <file paths> |
| Related components | <component names> |
| Current behavior | <summary of existing behavior> |
| Desired change | <what should change> |
| Test coverage | <coverage % on affected files> |
| Architecture constraints | <relevant constraints> |

## Version
current: 0.1.0
<!-- Bump rules: Minor (Y) for new features, Patch (Z) for fixes, Major (X) for breaking changes -->
<!-- Bump happens at Phase 8 completion. Sync with pyproject.toml/package.json and CHANGELOG.md -->

## Version History
| Version | Date | Phase | Change Type | Description | Reasoning |
|---------|------|-------|-------------|-------------|-----------|
| 0.1.0 | <start-date> | 1 | Initial | Project scaffolded | Starting point for development |

## Phase History
| Phase | Name | Start | End | Status | Summary |
|-------|------|-------|-----|--------|---------|

## Key Decisions
| Phase | Decision | Choice | Rationale | Date |
|-------|----------|--------|-----------|------|

## Council Deliberations
| Phase | Date | Conversation ID | Outcome |
|-------|------|-----------------|---------|

## Pending Actions
- [ ] <action item>

## Blockers
- <blocker if any>
