# Agent Personas Summary

This directory contains persona definitions for each phase of the software development lifecycle. Each agent has a distinct role, expertise, and approach optimized for their phase.

---

## Phase Overview

| Phase | Agent | Role | Advance | Context Group | Parallel Safe |
|-------|-------|------|---------|---------------|---------------|
| 1 | Business Analyst | Gather requirements | gate | seed | no |
| 2 | Research Coordinator | Orchestrate parallel research | confirm | research | no |
| 3 | Expansion Coordinator | Orchestrate parallel approach generation | confirm | research | no |
| 4 | Analysis Coordinator | Orchestrate parallel evaluation | confirm | evaluation | no |
| 5 | Pragmatic Executive | Select & scope MVP | confirm | evaluation | no |
| 6 | Systems Architect | Design system | confirm | design | no |
| 6b | Security Reviewer | Security review | auto | design | yes |
| 6c | UX Strategist | UX review | auto | design | yes |
| 7 | Principal Developer | Design tests | confirm | test | no |
| 8 | Senior Developer | Implement | gate | implementation | worktree* |
| 8b | Code Review Orchestrator | Orchestrate parallel specialized reviews | auto | implementation | no |
| 9 | Distinguished Engineer | Refine & polish | confirm | polish | no |
| 10 | Site Reliability Engineer | Operational resilience | confirm | polish | yes |
| 11 | Release Engineer | Pre-deploy verification | gate | deploy | no |

---

## Phase Flow by Scope

```
Trivial:    ──────────────────────────────────────────────────────> 8 ──> Done

Small:      1 ───────────────────────────────────────────> 7 ──> 8 ──> Done

                                              ┌─ 6b ─┐
Medium:     1 ────────> 4 ────> 6 ──>         │      ├──> 7 ──> 8 ──> 8b ──> 11 ──> Done
                                              └─ 6c ─┘

                                              ┌─ 6b ─┐                         ┌─ 9 ──┐
Large/New:  1 ─> 2 ─> 3 ─> 4 ─> 5 ─> 6 ──>  │      ├─> 7 ─> 8 ─> 8b ─> 11 ─> │      ├─> Done
                                              └─ 6c ─┘                         └─ 10 ─┘
```

**Bracket notation:** `[A, B]` = phases run concurrently as subagents. Both must complete before advancing.

---

## Orchestration

Each agent file includes orchestration metadata in its Identity block:

| Field | Values | Purpose |
|-------|--------|---------|
| `advance` | `auto`, `confirm`, `gate` | What happens after phase completes |
| `context_group` | `seed`, `research`, `evaluation`, `design`, `test`, `implementation`, `deploy`, `polish` | When to `/clear` |
| `parallel_safe` | `true`, `false`, `worktree` | Can run as sub-agent in parallel group |

**Advance categories:**
- **auto** — advances immediately (6b, 6c, 8b)
- **confirm** — shows summary, asks user to proceed (2, 3, 4, 5, 6, 7, 9, 10)
- **gate** — requires explicit user review (1, 8, 11)

*\* Phase 8 uses `worktree` isolation for parallel story execution. See `agents/phase-8-implementation.md` for full rules.*

---

## Model Tiers

Skills use abstract tiers. Map to concrete models via `config.yaml` → `model_tiers`:

| Tier | Purpose | Claude | Gemini | Codex |
|------|---------|--------|--------|-------|
| tier-1 | Reasoning (Phase 1, 6, 9, 10) | Opus | Pro | GPT-5 |
| tier-2 | Execution (Phase 2-5, 7, 8, 8b) | Sonnet | Flash | GPT-5-mini |

Both agent personas and skills use tier notation. The mapping table above resolves tiers to vendor-specific models.

---

## Agent by Deliverable

| Deliverable | Agent | Phase |
|-------------|-------|-------|
| `seed.md` | Business Analyst | 1 |
| `research.md` | Research Coordinator | 2 |
| `expansion.md` | Expansion Coordinator | 3 |
| `analysis.md` | Analysis Coordinator | 4 |
| `selection.md` | Pragmatic Executive | 5 |
| `architecture.md`, `api-design.md`, `database-schema.md` | Systems Architect | 6 |
| `security-review.md` | Security Reviewer | 6b |
| `ux-review.md` | UX Strategist | 6c |
| `test-plan.md` | Principal Developer | 7 |
| Working code | Senior Developer | 8 |
| Code review report | Code Reviewer | 8b |
| Refinement report | Distinguished Engineer | 9 |
| `predeploy-gate.md` | Release Engineer | 11 |
| `site-reliability.md` | Site Reliability Engineer | 10 |

---

## Orchestrated Phases

Phases 2, 3, 4, and 8b use an orchestrator + parallel sub-agent pattern. The orchestrator prepares context, dispatches sub-agents, and synthesizes results. Sub-agents run concurrently (dispatch mechanism is CLI-specific).

| Phase | Orchestrator | Sub-Agents |
|-------|-------------|------------|
| 2 (Research) | Research Coordinator | market-scout, library-miner, field-reporter |
| 3 (Expansion) | Expansion Coordinator | pragmatist, futurist, optimizer |
| 4 (Analysis) | Analysis Coordinator | technical, business, risk |
| 8b (Code Review) | Code Review Orchestrator | architect, skeptic, simplifier, rule-reviewer, qa*, browser-tester* |

*\* Frontend projects only.*

---

## Full Details

Each agent's complete persona, workflow, constraints, and prompts are in its individual file (`phase-X-*.md`). Read the specific agent file when entering that phase — not this summary.
