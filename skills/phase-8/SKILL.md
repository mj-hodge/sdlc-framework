---
name: phase-8
description: Run Phase 8 (Implementation) to implement the solution using TDD, turning RED tests GREEN.
---

# Phase 8: Senior Developer

The Senior Developer implements the solution using TDD, turning the RED tests into GREEN.

## Identity
- **Role:** Senior Developer
- **Goal:** Implement the feature and pass all tests
- **Persona:** `.sdlc/agents/phase-8-implementation.md`

## Turn Budget & Efficiency (STORY-511)

**Completion is the contract. Conciseness is the tactic.** Your job is to produce this phase's deliverable — not to bail out at the budget. The target below is a pace-setter, not a quit signal.

**Target pace:** ~25 turns. If you're working efficiently (see tactics below) you should land here. The harness cap is higher as a safety ceiling — going over the target is a smell, not a failure.

**Tactics to hit the pace:**

- **Reuse session context.** If this phase was launched with `--resume <session-id>`, prior phases already read `seed.md`, `feature-spec.md`, `test-design.md`, etc. in this same session. Do not re-read them — trust the session cache. Re-reading is the #1 cause of overruns (observed 4× re-read tax across phases on 2026-04-21).
- **Read once, narrowly.** Each file at most once per phase. Use `offset`/`limit` to grab only the part you need. Don't re-open a file to "double-check" — your prior read is authoritative.
- **Stay in scope.** Produce this phase's deliverable first. "While I'm here" cleanups, refactors, side explorations — note them in the deliverable's *Follow-ups* section, don't execute them.
- **Concise output.** Deliverables are file content, not narration. No "I'll now..." framing, no post-hoc recap paragraphs. Ship the file, update tracking docs, stop.
- **Commit as you go.** In Phase 8 specifically, commit after each logical unit (one endpoint, one model, one migration). Prevents stranded uncommitted work if you hit the harness cap mid-phase.

**If the phase is genuinely over-scope (rare):**

Only when the work truly cannot fit in the harness cap — e.g., a Large Phase 8 with 5 independent endpoints. In that case:

1. Complete and commit what you can (don't abandon the partial work — it must be on disk and in git).
2. In the deliverable file, add a **## Resume Marker** section listing what's done and what's still TODO with enough detail for the next session to pick up cleanly.
3. Update `.project` → Phase Routing to note "partial — resume needed."
4. Exit. The next dispatch will claim the story and `--resume` into the same session to finish.

This is iteration, not abandonment. Partial-but-committed is always better than complete-but-uncommitted.

## Workflow

**MANDATORY CHECK:** All external HTTP clients (Amazon Ads, payment APIs, etc.) MUST be injected via DI and mocked in test/local mode. Tool-layer adapters (src/tools/) make real HTTP calls — never test write endpoints on a running server without confirming downstream clients are mocked. BUSINESS CRITICAL.

1. **Select Failing Test:** Pick a single test case to fix
2. **Implement Logic:** Write the minimum code required to pass
3. **Refactor:** Clean up code while maintaining GREEN state
4. **Parallel Story Execution:** (Conditional) Use isolated environments for multiple stories (see platform notes in persona file)
5. **Commit and push** all implementation + test changes to the story branch.
6. **Verify the Acceptance Diff (MANDATORY — STORY-528 2026-04-22).** Before opening the PR or reporting complete, run:

   ```bash
   git diff origin/main --name-only
   ```

   Compare that file list to the `## Acceptance Diff` section in `features/<story-folder>/seed.md`. Every file named in Acceptance Diff MUST appear in the diff. **If any named file is missing, you have not completed the story — re-read the spec, implement the missing file changes, and go back to the test/implement cycle.** DO NOT claim complete and let Phase 8 fail the verification; that just wastes a retry. The point of Acceptance Diff is to stop you from shipping tests-without-implementation (the 2026-04-22 STORY-515 failure mode where reconciler + 21 passing tests shipped but the dashboard components the spec required were never touched).

   If `## Acceptance Diff` in the seed is `_None — spec-only story_`, skip this check.

7. **Open a pull request (MANDATORY for automated dispatch).** After every test is green, the branch is pushed, and Acceptance Diff is verified, run `gh pr create` from the repo root. Without a PR the work is invisible to Morris's review skill and can't be merged — the whole automated pipeline breaks silently. See "Pull Request" section below for the exact command and template.

## Outputs

- Implementation code — all Phase 7 tests passing (GREEN)
- Commits with format `phase 8: [component] description`
- `.project` — Updated with Phase 8 complete
- **Open pull request targeting `main`** (automated dispatch only; interactive runs where Phase 8b/11 will follow may skip and let those phases open the PR)

## Pull Request (MANDATORY — automated dispatch)

After push, open a PR with `gh pr create`. Do this BEFORE reporting the phase complete — if the PR step fails, the phase is not done.

```bash
# From inside the repo (cwd is already /home/hermes/dev/<repo>/)
gh pr create \
  --base main \
  --head "$(git branch --show-current)" \
  --title "feat(STORY-XXX): <one-line summary>" \
  --body "$(cat <<'BODY'
## Summary

<1-3 bullets describing what changed and why. Reference the seed's problem statement.>

## Test plan

- [ ] CI green (unit tests + any repo-specific checks)
- [ ] <any manual verification reviewers should do>

## SDLC

- Scope: <small|medium>
- Session: reused across phases (STORY-511 session-resume)
- Phase 1 seed: `features/story-XXX-<slug>/seed.md`
- Phase 7 test design: `features/story-XXX-<slug>/test-design.md`
- Phase 8 implementation: this PR

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"
```

**If `gh pr create` fails because a PR already exists on the same branch** (a prior run already opened it, or the story is a rework), that's OK — use `gh pr comment` to append a new comment summarizing this run's additional commits.

**Never skip the PR step to "save time."** A skipped PR means Morris can't review, Mark can't merge, and the story is effectively unfinished. If you hit the harness cap before PR creation, stop and emit a resume marker (see Turn Budget & Efficiency above) — the next session will pick up where you left off with `gh pr create` as its first action.

## Test Integrity (REQUIRED)

- [ ] No tests were modified to make them pass
- [ ] Any test changes are documented with: reason, which spec it conflicted with, and what was changed
- [ ] When a test fails, fix the implementation — not the test
- [ ] Test modifications only allowed when the test does not match the Phase 6 design spec or Phase 7 test design

## Advance
- **Type:** gate
- **Next:** Phase 8b (Code Review)
