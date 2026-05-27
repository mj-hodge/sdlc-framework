---
name: retro-apply
description: Import and apply retrospective proposals from project teams into the SDLC framework. Framework owner only.
---

# Retro Apply (Framework Owner Only)

Import retrospective proposal files from project teams, review findings, and apply approved changes to the SDLC framework (coding-ai-config).

**This skill is run from within coding-ai-config, not from a project repo.**

## Usage

```
/retro-apply --import <file>                       # Import a single proposal file
/retro-apply --import <file1> <file2> ...          # Import multiple proposal files
/retro-apply <path-to-project>                     # Direct scan (local projects you own)
/retro-apply --all ~/projects/*/                    # Scan all local projects for retros
```

## How Proposals Arrive

Project teams run `/retro` after completing an epic. This generates:
1. `retrospective.md` — full report (stays in their project repo, private)
2. `retro-proposal.yaml` — portable proposal file (shared with framework owner)

The proposal file contains only SDLC improvement suggestions — no proprietary code, business logic, or sensitive project data. Teams share it via email, Slack, shared drive, or any secure channel.

**No cross-repo access needed.** The framework owner doesn't need GitHub access to consumer repos, and consumers don't need write access to coding-ai-config.

## Steps

1. **Load proposals**
   - `--import`: Read the provided YAML proposal file(s)
   - Direct path: Scan `features/*/retro-proposal.yaml` in the project path
   - Validate YAML structure matches expected schema

2. **Present findings summary**
   - Group by category (Phase 1, Phase 7, Phase 8b, etc.)
   - Highlight cross-project patterns (same finding from 2+ proposal files)
   - Show severity distribution

3. **Review with user**
   - Present each proposal with its evidence
   - User marks items as REVIEWED (approve) or REJECTED
   - Cross-project patterns get priority — same issue from multiple projects is a strong signal

4. **Apply REVIEWED items**
   - Edit agent personas, guidance docs, templates in this repo
   - **Anonymized commit messages (REQUIRED):** Never include project names, company names, or epic names in commit messages
     - Public commit: `retro: [F-XXX] <description>`
     - Example: `retro: [F-007] add tenant isolation gate to Phase 7`
     - NOT: `retro: [F-007] add tenant isolation gate (from acme-corp/billing-epic)`
   - **Private source log:** Append to `retrospectives/source-log.yaml` (gitignored) to preserve traceability
     ```yaml
     - id: F-007
       source_project: acme-corp
       source_epic: billing-epic
       commit: abc1234
       date: 2026-03-08
     ```

5. **Generate receipt**
   - Create a receipt file listing applied changes with commit hashes
   - Framework owner can send receipt back to the project team
   - Project team updates their status tracker: PENDING → IMPLEMENTED

6. **Push**
   - Push coding-ai-config to remote
   - Projects update their .sdlc submodule ref on next pull

## Cross-Project Pattern Detection

When the same finding appears in 2+ proposal files:
- Flag it as a **systemic gap** (not just project-specific)
- Higher priority for framework changes
- Example: "Missing tenant isolation tests" in Project A AND Project B = must-fix in Phase 7 agent

## Privacy Model

| What | Who sees it | Where it lives |
|------|-------------|----------------|
| Retrospective report | Project team only | Project repo (`features/<epic>/retrospective.md`) |
| Proposal file | Project team + framework owner | Shared via secure channel |
| Applied changes (commits) | Everyone (via submodule) | coding-ai-config (anonymized — no project/company names) |
| Source log | Framework owner only | `retrospectives/source-log.yaml` (gitignored) |
| Receipt | Framework owner + originating team | Sent back to team |

**Anonymization rules:**
- Commit messages NEVER contain project names, company names, or epic names
- The git history reveals only what SDLC improvements were made, not who requested them
- The private source log (`retrospectives/source-log.yaml`) preserves full traceability for the framework owner only
- This file is in `.gitignore` — it never leaves your machine

## Receipt Format

After applying proposals, generate a receipt for the submitting team:

```yaml
# retro-receipt-<project>-<date>.yaml
version: 1
project: <project-name>
epic: <epic-name>
applied_date: YYYY-MM-DD
applied:
  - id: F-001
    status: IMPLEMENTED
    commit: abc1234
    file: agents/phase-7-test-design.md
  - id: F-003
    status: IMPLEMENTED
    commit: def5678
    file: agents/phase-8-implementation.md
rejected:
  - id: F-002
    reason: "Already covered by existing Gate 3"
```

## Output

```
## Retro Apply Summary

### Proposals Imported
| Source | Project | Epic | Date | Items |
|--------|---------|------|------|-------|
| retro-proposal.yaml | vpm | AppFolio Phase 2 | 2026-03-08 | 15 |
| retro-proposal.yaml | project-b | Feature X | 2026-03-15 | 8 |

### Cross-Project Patterns
| Pattern | Projects | Category | Action |
|---------|----------|----------|--------|
| Missing tenant isolation | vpm, project-b | Phase 7 | Add Gate 6 |

### Applied Changes (commits are anonymized — no project names in git history)
| ID | File | Commit |
|----|------|--------|
| F-007 | agents/phase-7-test-design.md | abc1234 |

### Source Log (private, gitignored)
- Updated: retrospectives/source-log.yaml
- Maps F-IDs back to source projects (only on your machine)

### Receipt
- Saved to: retro-receipt-<project>-2026-03-08.yaml
- Send back to the project team so they can update their status tracker
```
