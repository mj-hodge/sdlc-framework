# Epic Retrospectives

This directory is for the **framework owner** to track SDLC improvements applied from project retrospectives.

## How It Works

1. Project teams run `/retro` after an epic completes
2. This produces two files in their project repo:
   - `features/<epic>/retrospective.md` — full report (private, stays in project)
   - `features/<epic>/retro-proposal.yaml` — portable proposal file (shared with framework owner)
3. Team sends the proposal file to the framework owner via any secure channel
4. Framework owner imports proposals with `/retro-apply --import <file>`

**No cross-repo access needed.** The framework owner doesn't need access to consumer repos. Consumers don't need write access to coding-ai-config. Projects never see each other's proposals.

## Framework Owner Workflow

```
1. Receive proposal files from project teams
   - Proposals arrive via email, Slack, shared drive, etc.
   - Each file is a self-contained YAML with SDLC improvement suggestions
   - No proprietary code or sensitive project data included

2. Import and review
   - /retro-apply --import proposal1.yaml proposal2.yaml
   - Cross-project patterns are auto-detected (same finding from 2+ projects)
   - Mark items as REVIEWED (approve) or REJECTED

3. Apply approved changes
   - Edit agent personas, guidance docs, templates in this repo
   - Commit with ANONYMIZED messages: "retro: [F-XXX] <description>" (no project/company names)
   - Update private source log: retrospectives/source-log.yaml (gitignored)

4. Send receipt back to project team
   - Receipt lists applied/rejected items with commit hashes
   - Team updates their status tracker: PENDING → IMPLEMENTED

5. Release
   - Push to remote
   - Consuming projects update their .sdlc submodule ref
```

## Tracking Applied Changes

Use git log to see all retro-driven changes:
```bash
git log --oneline --grep="retro:"
```

## Privacy Model

| Component | Location | Who sees it |
|-----------|----------|-------------|
| Retrospective report | Project repo (`features/<epic>/retrospective.md`) | Project team only |
| Proposal file | Shared via secure channel | Project team + framework owner |
| Commit messages | This repo (git history) | Everyone — **anonymized, no project/company names** |
| Applied changes | This repo (agent personas, guidance, templates) | Everyone via submodule |
| Source log | `retrospectives/source-log.yaml` (gitignored) | Framework owner only |
| Receipt | Sent back to originating team | Framework owner + originating team |

**Anonymization:** Git history never contains project names, company names, or epic names. Consumers see only generic SDLC improvements (e.g., "add tenant isolation gate to Phase 7"). The private source log maps finding IDs back to their origin — it stays on the framework owner's machine only.
