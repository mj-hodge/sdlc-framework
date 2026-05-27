---
name: whats-next
description: Show what Mark needs to do — agent handbacks, PRs to review, blockers, manual admin tasks across all projects
---

# What's Next for Mark

Surfaces all pending items that need your attention across projects and agents.

## Usage

```
/whats-next                    # Everything across all projects
/whats-next advertising        # Filter to one project
/whats-next blockers           # Only items blocking agents
```

## Steps

### 0. Read Morris's heartbeat-generated state files FIRST

Before querying GitHub, Loki, or Asana, read these files. They're refreshed every 30 min by `heartbeat-collector.py` and together cover ~80% of "what needs Mark" without any network calls:

```bash
for f in current-focus escalation-needed parked-seeds uncommitted-work; do
  path="/home/hermes/state/morris/${f}.md"
  if [ -f "$path" ]; then
    echo "=== ${f} ==="
    cat "$path"
    echo
  fi
done
```

- **`current-focus.md`** — live snapshot: active branch, open PR counts, alerts (CI failing, fleet WARN, parked seeds, uncommitted work).
- **`escalation-needed.md`** — state-sync's human-readable escalation list (hourly refresh). Surfaces CONFLICTING PRs, Mark's own PRs with failing CI, SSH/ops-console issues, review-required PRs that have sat too long.
- **`parked-seeds.md`** — `features/story-NNN-*/seed.md` directories that have no dispatch queue row. These are Phase-1 seeds written ahead of time or during incidents; they're "ready to dispatch or delete."
- **`uncommitted-work.md`** — Morris's own uncommitted seed folders and action logs. If this lists anything, Morris has incident-time work sitting on an unrelated branch and needs to split-commit before merging.

Roll these into the priority summary (Step 6) before falling back to the heavier GitHub/Loki queries.

### 0a. Fetch live dispatch stalls

Morris's heartbeat-collector covers Mark's manual TODO list, but it does NOT
see what's stuck on the agent fleet's dispatch queue. Pull the queue stall
view directly:

```bash
BASE_URL="https://tech-dev-agents.gorillacommerce.ai"
STALLS=$(curl -fsS -H "X-API-Key: $OPS_CONSOLE_API_KEY" \
  "$BASE_URL/api/dispatch/v2/stalls") || STALLS='{"items":[]}'
echo "$STALLS" | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('items', [])
if not items:
    print('(no stalled jobs)')
else:
    for r in items:
        print(f\"  {r.get('story_id')} [{r.get('repo')}] {r.get('stall_reason')} \"
              f\"since {r.get('stalled_since')} · last_action={r.get('last_action') or '—'}\")
"
```

Stall reasons (full taxonomy in `skills/dispatch/SKILL.md` § Stale State Heuristics):
`silent_stall`, `awaiting_human`, `awaiting_human_critical`, `stale_dispatch`, `review_stuck`.

If the curl returns non-2xx, surface a one-line warning ("dispatch queue
unreachable — stall list unavailable") and continue with steps 1–7. Do not
block the whole `/whats-next` on a queue outage.

### 1. Check agent handbacks (PRs with Mark TODO)

Search for open PRs with handback items across all repos the agents work on:

```bash
# Check each repo the agents work on
for repo in tech-dev-agents advertising-amazon; do
  echo "=== ${repo} ==="
  gh pr list --repo "hpi-gorillacommerce/${repo}" --state open --json number,title,body,author 2>/dev/null | \
    python3 -c "
import sys,json
prs = json.load(sys.stdin)
for pr in prs:
    body = pr.get('body','') or ''
    if 'Mark TODO' in body or '- [ ]' in body:
        print(f'  PR #{pr[\"number\"]}: {pr[\"title\"]}')
        # Extract unchecked items
        for line in body.split('\n'):
            if line.strip().startswith('- [ ]'):
                print(f'    {line.strip()}')
"
done
```

### 2. Check seed.md files for Manual Steps sections

```bash
# Search across all projects
for dir in /mnt/c/Projects/tech-dev-agents /mnt/c/Projects/advertising-amazon; do
  grep -rl "## Manual Steps" "${dir}/features/" 2>/dev/null | while read f; do
    echo "=== ${f} ==="
    sed -n '/## Manual Steps/,/^## /p' "$f" | head -20
  done
done
```

### 3. Check agent blockers (from Loki)

Query Loki for recent "Blocked:" messages that reference Mark:

```bash
bash tools/loki-query.sh all "Blocked:|Decision needed:|waiting.*Mark|approval" 24
```

Parse for unresolved blockers — items where no follow-up "Unblocked" or "Resolved" appears after the blocker.

### 4. Check Monday.com for items assigned to Mark

If Monday MCP tools are available, search for tasks assigned to Mark or tagged as needing manual action.

### 5. Check agent completion summaries

Look for recent "STORY-XXX complete" messages that include recommendations or follow-up items:

```bash
bash tools/loki-query.sh all "complete|Recommendations:|follow-up" 48
```

### 6. Present summary

Format as a prioritized list:

```
## What's Next for Mark

### 🚨 Escalations (from escalation-needed.md)
- PR #98 (tech-dev-agents): CONFLICTING for 18h — needs rebase before CI can run.
- PR #102 (tech-dev-agents, Mark's): CI failing, review required.
- Fleet: Daisy + Devon SSH timeout on :443.

### 🔴 Blocking Agents (do these first)
- [ ] **STORY-082** (Dan blocked): Create Azure AD app registration for UAT environment
      PR #14, filed 2h ago

### 🛑 Stalled jobs (live queue)
- **STORY-N** — `silent_stall`, no heartbeat 47m, last action: `committed abc123 (Phase 8)`
- **STORY-M** — `awaiting_human` 3h, run `/answer-needs-info STORY-M`

### 🟡 PRs to Review
- PR #12 (advertising-amazon): STORY-088 Scheduled Spend Refresh — Dan, 8/8 tests GREEN

### 🪵 Parked seeds (from parked-seeds.md)
- STORY-560, STORY-561 — incident-time seeds with no dispatch row. Dispatch or delete.

### 📦 Morris has uncommitted work (from uncommitted-work.md)
- `features/story-560-*/`, `features/story-561-*/` on `fix/phase-gate-retry-skip` — needs split-commit before the parent branch merges.

### 🟢 Follow-ups (non-blocking)
- STORY-088 recommends: add Grafana alert for spend refresh failures

### 📋 Agent Status
- Dan: idle, last completed STORY-088 (2h ago)
- Derrick: active on STORY-019 (Phase 7)
```

**Priority order:**
1. Live queue stalls (`silent_stall`, `awaiting_human_critical`) — agents are dead in the water
2. Items blocking agents (they're burning idle time or stuck)
3. PRs ready for review (agents are waiting on merge)
4. Manual admin tasks from handback TODOs
5. `awaiting_human` stalls — questions over 2h old that don't yet need escalation
6. Follow-up recommendations from completed stories
7. Agent status summary

### 7. Suggest next dispatch

After showing pending items, suggest what to dispatch next:

```
### Ready to Dispatch
These stories are specced and ready in the backlog:
- STORY-013: Agent Monday.com Integration (Medium) — no dependencies
- STORY-014: Agent Management Dashboard (Medium) — depends on STORY-013

Use /dispatch <agent> <story> to assign.
```

## Notes

- This skill works across ALL projects in /mnt/c/Projects/ — not just the current directory
- Agent handbacks use the `## Mark TODO` and `## Manual Steps (Mark)` conventions
- If no handbacks/blockers found, show agent status and ready-to-dispatch stories
- Keep output concise — this is a quick "what needs me" check, not a deep analysis
