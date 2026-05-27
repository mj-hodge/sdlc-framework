---
name: review-context-bundler
description: Build the review-context.md knowledge bundle that powers Morris's PR review citations.
agent: morris
---

# review-context-bundler

Generates `~/state/morris/review-context.md` — the knowledge bundle Morris's `review-prs` skill loads via `--append-system-prompt-file`. The bundle gives Morris innate company knowledge during reviews so it can cite KB articles, SDLC standards, runbook procedures, and recurring gaps.

## When to use

- **Scheduled:** Runs daily at 06:00 UTC via cron — overwrites the bundle automatically.
- **On-demand:** Run `/review-context-bundler` after merging wiki PRs, updating runbooks, or adding new KB pages. This refreshes Morris's knowledge immediately.

## What the bundle contains

| Section | Source | Content |
|---------|--------|---------|
| KB Digest: Systems | `wiki/systems/*.md` | Title + summary + section headers with one-line summaries |
| KB Digest: Processes | `wiki/processes/*.md` | Title + summary + section headers with one-line summaries |
| SDLC Standards Matrix | `.sdlc/AGENTS.md` | Deliverable matrix table + scope paths (verbatim) |
| Runbook Excerpts | `runbooks/`, `docs/runbooks/`, `monitoring/runbooks/` in active repos | Titles + summaries |
| Recent Fleet Incidents | `~/state/morris/action-log-*.md` (last 7 days) | One bullet per incident (PR, repo, verdict) |
| Knowledge Gaps Roll-Up | `~/state/morris/knowledge-gaps.jsonl` | Top 10 most-frequent gaps with counts |

## Output

- **File:** `~/state/morris/review-context.md` (also git-tracked at `~/workspace/tech-dev-agents/state/morris/review-context.md`)
- **Format:** Markdown with header line: `<!-- review-context bundle: built=ISO8601 / wiki_pages=N / runbooks=N / incidents=N / gaps=N -->`
- **Budget:** ≤120K chars (~30K tokens). If exceeded, drops wiki pages by least-recently-modified; logs dropped pages to `/tmp/bundle-dropped.txt`.

## Steps

### Step 1 — Run the generator

Execute the bundle generator script:

```bash
python3 /home/hermes/workspace/tech-dev-agents/.sdlc/skills/review-context-bundler/generate-bundle.py
```

The script is fully self-contained. It:
1. Reads wiki pages from `/home/hermes/dev/hpi-gorillacommerce/tech-gc-knowledgebase/wiki/` (read-only — never writes to KB repo)
2. Extracts SDLC matrix from `.sdlc/AGENTS.md`
3. Scans active repos for runbooks
4. Summarizes last 7 days of action-log files
5. Reads `knowledge-gaps.jsonl` (if exists)
6. Enforces the 120K char budget — trims oldest wiki pages if over
7. Writes identical output for identical inputs (idempotent)

### Step 2 — Verify output

After the script completes, verify:

```bash
# Check file exists and has the header
head -1 ~/state/morris/review-context.md

# Check size is under budget
wc -c ~/state/morris/review-context.md

# Check for dropped pages
cat /tmp/bundle-dropped.txt 2>/dev/null || echo "No pages dropped"
```

### Step 3 — Report

Print a summary:
```
Bundle refreshed:
- Wiki pages: N (systems) + N (processes)
- Runbook excerpts: N
- Recent incidents: N (last 7 days)
- Knowledge gaps: N
- Size: N chars (budget: 120,000)
- Dropped pages: N (see /tmp/bundle-dropped.txt)
```

## Cron schedule

Registered via `/schedule-cron`:
```
Job:      review-context-bundler
Cadence:  0 6 * * *  (daily at 06:00 UTC)
Script:   python3 /home/hermes/workspace/tech-dev-agents/.sdlc/skills/review-context-bundler/generate-bundle.py
```

## Constraints

- **Read-only on KB repo** — never write to `tech-gc-knowledgebase`
- **No full wiki bodies** — only titles, section headers, and one-line summaries
- **Budget in code** — the 120K char limit is enforced in `generate-bundle.py`, not a comment
- **Idempotent** — identical inputs produce identical output bytes (timestamps use UTC, sorts are deterministic)
- **Git-tracked** — bundle is committed at `~/workspace/tech-dev-agents/state/morris/review-context.md`

## How review-prs uses the bundle

The `review-prs` skill references this bundle when launching sub-agent review sessions. The header line lets Step 0 detect staleness (if `built=` timestamp is >24h old, trigger a refresh before reviewing). Section `[KB: ...]` citations in findings-ledger.jsonl trace back to entries in this bundle.

## Anti-patterns

- Do NOT include full page bodies — the bundle will blow the token budget
- Do NOT run this from inside the KB repo — always run from Morris's state context
- Do NOT manually edit `review-context.md` — it is machine-generated and will be overwritten
