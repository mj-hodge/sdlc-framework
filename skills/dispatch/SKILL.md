---
name: dispatch
description: Send stories, story groups, or epics to agents (Dan/Derrick) with context, review, and optional detailed implementation prompts
---

# Dispatch Work to Agents

Build, review, refine, and send work assignments to your agent fleet.

**NEVER use RemoteTrigger, schedule, or cron to dispatch work.** Agents are reached via Teams messaging only — either through the `mcp__agent-ops__send_message` MCP tool or by printing the prompt for the user to copy-paste into Teams.

## Usage

```
/dispatch <agent> <stories> [context]
/dispatch dan STORY-018                                    # Detailed by default — implementation steps, tests, decision points
/dispatch derrick STORY-019,STORY-020                      # Multiple stories
/dispatch dan EPIC-2                                       # Full epic
/dispatch dan STORY-018 --brief                            # Brief mode — structured prompt without implementation steps
/dispatch dan STORY-018 "skip steps 1-2, VM at 137.x"     # Inline context
```

## Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `agent` | Yes | Agent name: `dan`, `derrick`, or `all` (broadcast) |
| `stories` | Yes | Comma-separated STORY-IDs, or EPIC-N for a full epic |
| `context` | No | Free-text context, constraints, or instructions |
| `--brief` | No | Skip implementation steps/tests — just SC table, constraints, and context |

## Mode Selection

| Story Scope | Default Mode | Override |
|-------------|-------------|---------|
| Small | **Brief** — SC table + constraints + context is enough | `--detailed` to force full prompt |
| Medium | **Detailed** — implementation steps + test specs + decision points | `--brief` to simplify |
| Large | **Detailed** — always | `--brief` to simplify |
| Epic | **Detailed** — always, with execution order and dependency graph | `--brief` to simplify |

## Workflow (3-phase: Build → Review → Send)

Every dispatch goes through three phases. The user reviews and refines before anything is sent.

```
/dispatch dan STORY-018
    │
    ▼
Phase A: GATHER — read seeds, check status, ask for context
    │
    ▼
Phase B: DRAFT — build the prompt (standard or detailed), present to user
    │
    ▼
    USER REVIEWS ← ── ── ── ── ── ── ── ── ──┐
    │                                          │
    ├── "looks good" / "send it" → Phase C     │
    ├── "change X" / "add Y" → revise ─────────┘
    └── "cancel" → abort
    │
    ▼
Phase C: SEND — dispatch via MCP or print for copy, update tracking
```

**CRITICAL: NEVER send without explicit user approval.** Always present the draft and wait.

---

## Phase A: Gather

### 1. Resolve stories

**Single story (STORY-XXX):**
- Read `features/story-XXX-*/seed.md` — full content
- Read `backlog.md` for status and scope
- If design docs exist (`feature-spec.md`, `architecture.md`, `test-design.md`), read them too
- Check `.project` for phase history on this story

**Multiple stories (STORY-XXX,STORY-YYY):**
- Read each seed.md
- Check for dependencies between them
- Determine execution order or parallelism

**Epic (EPIC-N):**
- Read `backlog.md` for all stories in the epic
- Read `implementation-plan.md` if it exists
- Only include Ready stories (skip Done/In Progress)

### 2. Check agent availability

- If agent-ops MCP tools are available: call `list_agents` or `get_agent_detail`
- Otherwise query Loki: `{agent="<name>"} |~ "(START|DONE|END)"` last 30 min
- If agent is active, warn user: "Dan is in a session (started X min ago). Dispatch anyway?"

### 3. Ask for context

If no context was provided inline, ask:

> **Context for this dispatch:**
> What should the agent know that isn't in the seed? Any constraints, decisions made, blockers resolved, files to read first, steps to skip, or instructions?
>
> (Press Enter to skip — the seed will be sent as-is)

---

## Phase B: Draft

### Brief mode (default for Small scope, or `--brief`)

Build a structured prompt with:

```markdown
## Assignment: STORY-XXX: <title> (story-XXX/slug)

Scope: <Small/Medium/Large>
Phase path: <1 → 7 → 8 → Done>
Start from: <Phase N>
Seed: features/story-XXX-slug/seed.md
Branch: (story-XXX/slug)

### Success Criteria
<paste full SC table from seed.md>

### Key Constraints
<tech stack, out of scope, dependencies from seed.md>

### Context from Mark
<user's context — verbatim, not summarized>

### How to Execute
- Read the full seed at features/story-XXX-slug/seed.md before starting
- Use /next to advance through SDLC phases
- Use Claude Code SDK for ALL coding work (never code natively)
- Work on a feature branch (story-XXX/slug), NOT main
- Push to remote after EVERY commit — do not accumulate local commits
- When complete: create a PR with `gh pr create` and message Mark with the PR link
- Do NOT merge the PR — Mark reviews and merges
- Message Mark when complete or blocked
```

**Branch format note (REQUIRED):** The first line MUST include the branch name in parentheses — `(story-XXX/slug)`. The agent's poller (`dispatch_poller_v2._extract_story_branch`) uses regex `\((story-\d+/[A-Za-z0-9_./-]+)\)` to discover the branch. Without parens the rebase-prep gate fails fast with `branch_unresolved` and the job dies before Phase 7 even starts (observed 2026-05-04 on STORY-871). Always include the parens form on the title line AND in the explicit `Branch:` line.

### Detailed mode (default for Medium/Large/Epic scope)

Everything in standard mode PLUS:

**Read deeper** — analyze the seed's success criteria, proposed solution, and any existing design docs. Then add these sections to the prompt:

#### Implementation Steps
A numbered list of what the agent should do, in order. Keep each step to 1-2 sentences. Don't write code — describe the action and the expected outcome.

Example:
```
### Implementation Steps
1. Install Python 3.12 and uv on the VM. Done when `python3.12 --version` works.
2. Clone the repo to /opt/ops-console and install deps with uv. Done when `import tech_dev_agents` succeeds.
3. Create .env with the required vars (see config.py). Permissions 600.
4. Create systemd unit for uvicorn on port 8005. Enable and start.
5. Configure nginx reverse proxy. Reload.
6. Run certbot for TLS (may need to wait for DNS propagation).
7. Install and configure promtail for Loki.
8. Run the deploy smoke tests. All must pass.
```

#### Test Guidance
Tell the agent what to test, not how to write the tests. Reference success criteria by ID.

Example:
```
### What to Test
- SC-1: health endpoint returns 200 over HTTPS
- SC-2: console stays up when an agent VM is unreachable (partial results, not 500)
- SC-4: promtail logs appear in Loki under {job="ops-console"}
- Auth: unauthenticated requests return 401
Write tests FIRST (TDD). Confirm RED, then implement to GREEN.
```

#### Decision Points
Where the agent might get stuck or need Mark's input. Keep to 2-4 bullets.

#### Files to Read First
List 3-5 key files the agent should read before starting. Don't list obvious ones like the seed itself.

### Present draft to user

After building the prompt (standard or detailed), present it:

```
## Draft Dispatch to Dan

<full prompt content>

---
**Review this prompt.** Options:
- "send it" — dispatch as-is
- "change X to Y" — I'll revise and show you again
- "add: <instruction>" — I'll append to the Context section
- "more detail on step N" — I'll expand that step
- "cancel" — abort dispatch
```

### Handle revisions

When the user requests changes:
1. Apply the change to the draft
2. Show the updated section (not the entire prompt, unless they ask)
3. Ask again: "Ready to send, or more changes?"

Repeat until the user says "send it" or equivalent.

---

## Phase C: Send

### Push to remote FIRST (CRITICAL)

Before sending anything to an agent, ensure all story files (seed.md, design docs, etc.) are committed and pushed to remote. The agent pulls from git — if it's not on remote, they can't see it.

```bash
git add features/story-XXX-*/
git commit -m "feat(STORY-XXX): seed + dispatch"
git push origin main
```

If the push fails (merge conflict), resolve it before dispatching. **NEVER dispatch a story whose seed only exists locally.**

### Dispatch to agent

**IMPORTANT: Use ONLY these methods. NEVER use RemoteTrigger, schedule, cron, or any other dispatch mechanism.**

**Method 1 (preferred for follow-up work): Enqueue via Dispatch Queue API (v2)**

For queuing stories that agents auto-claim, use the v2 ops console dispatch API:

```bash
curl -X POST "https://tech-dev-agents.gorillacommerce.ai/api/dispatch/v2/enqueue" \
  -H "X-API-Key: $OPS_CONSOLE_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Worker-Version: 2.0" \
  -d '{"story_id":"STORY-XXX","repo":"<repo-name>","scope":"small","prompt":"<full prompt with branch, deps, spec location>","title":"<short title>","enqueued_by":"mark","target_role":"developer"}'
```

- `story_id` must match `^STORY-\d+$`
- `X-Worker-Version: 2.0` header is required (the v2 router enforces it via `_check_worker_version`)
- Response: 200 with `{job_id, repo, story_id, scope, enqueued_at}`. If a job already exists for this `(repo, story_id)` pair in non-terminal state, the existing job is returned (idempotent).
- 409 if an active correlation conflict exists; 422 if the request body is invalid.
- **Verify by job_id, NOT by `/queue`.** Use `GET /api/dispatch/v2/lineage/{job_id}` — that endpoint reads `dispatch_jobs` directly and returns honest state. The `/queue` endpoint has a read-side bug (observed 2026-05-12) that returns 0 rows in every lane even when the row exists; do not trust it for write verification. See "Verify after enqueue" below.
- Agents poll v2 (`DISPATCH_PROTOCOL=v2`) and auto-claim from `work_queue` lane via `/claim-next` (not `/queue`) when idle — no Teams message needed. The `/queue` read bug does NOT block claims; agents still receive work.

**Failsafe: v1 mirror trigger.** If you accidentally hit the legacy `POST /api/dispatch` endpoint, a database trigger automatically mirrors the v1 row into v2 (`dispatch_jobs` + `enqueued` event), so the story still reaches v2 pollers. Prefer the v2 endpoint above for clarity and to get the job_id back.

### Stale State Heuristics (queue stall reasons)

`GET /api/dispatch/v2/stalls` returns rows where the dispatch state has aged past a threshold. This is the single source of truth for "why is STORY-N stuck?" — `/pm`, `/whats-next`, and the SLA Teams notifier all read it.

| Reason | Trigger | Where to look | Action |
|--------|---------|--------------|--------|
| `silent_stall` | lane=`in_progress` && `dispatch_leases.heartbeat_at` older than 15 min | Loki: `{agent="<name>", job="claude-code"} \|~ "STORY-N"` last 1h | Wrapper or Claude API hung. Investigate logs; force-release if dead. |
| `awaiting_human` | state=`needs_info` && `updated_at` older than 2h with no `ANSWER.md` on branch | Story branch `features/<story>/QUESTION.md` | Mark notified via Teams. Run `/answer-needs-info STORY-N`. |
| `awaiting_human_critical` | state=`needs_info` && `updated_at` older than 12h | Same as above | Manager line pinged. Decision overdue. |
| `stale_dispatch` | state=`pending` && `updated_at` older than 24h | Check `DISPATCH_PROTOCOL` on agent VMs; `/fleet` for poller activity | No agent claimed. Verify pollers running and worker_version current. |
| `review_stuck` | state=`in_review` && `updated_at` older than 24h && PR has unresolved review comment | PR comments | PR feedback webhook (see below) handles this — should auto-flip to `needs_info`. If not, webhook is failing: check Render service `pr-feedback-webhook` logs and verify the GitHub App's webhook delivery in repo settings. Escalate to Mark if webhook is healthy but flips aren't happening. |

**Heartbeat cadence (set by poller):**
- Wrapper layer: `dispatch_poller_v2.py` heartbeats every `DISPATCH_LEASE_RENEW_INTERVAL` seconds (default 300, 5 min). Three missed beats (15 min) → `silent_stall`.
- Semantic layer: agent personas write `last_action` to a sidecar file the poller reads on each heartbeat tick. Stale `last_action` doesn't trip a stall by itself, but `/pm STORY-N` surfaces it as context: "last commit abc123 47m ago in Phase 8."

**PR feedback → needs_info:** GitHub `pull_request_review` and `issue_comment` webhooks POST to `/api/dispatch/v2/pr-feedback`. When a reviewer requests changes, the webhook generates `features/<story>/PR_FEEDBACK_<pr_num>.md` on the story branch and flips the queue row to `needs_info`. The agent picks up the feedback on its next poll cycle — no manual `/dispatch` needed for rework.

**Verify after enqueue (REQUIRED — use lineage, NOT queue):**

The `/api/dispatch/v2/queue` endpoint has a read-side bug (since at least 2026-05-12) where it returns 0 rows in every lane even when the row exists in `dispatch_jobs`. Multiple remote agents have hit this and falsely concluded their enqueue was orphaned. **Do not use `/queue` for write verification.** Use the lineage endpoint instead — it reads `dispatch_jobs` directly and is honest:

```bash
curl -sS -H "X-API-Key: $OPS_CONSOLE_API_KEY" \
  "https://tech-dev-agents.gorillacommerce.ai/api/dispatch/v2/lineage/$JOB_ID"
```

Returns `{"chain":[{"job_id":"<uuid>","attempt":1,"state":"pending|leased|in_progress|in_review|needs_info|completed|...","parent_job_id":null,"redispatched_at":"..."}]}`. Any non-error response means the row exists. The `state` field tells you whether it's still pending or already claimed.

**Only escalate to Mark if `lineage/{job_id}` returns 404.** That's the only true-orphaned signal. A 0-row `/queue` response is a known bug, not orphanage — do NOT re-enqueue and do NOT fall back to v1 `/api/dispatch` based on `/queue` alone.

**`/queue` only shows ACTIVE lanes — not terminal outcomes.** The lanes are `pending`, `in_progress`, `in_review`, `paused`, `needs_info`, `claimed`. There is no `completed`/`cancelled`/`failed`/`dead_letter` lane. Stories that finish disappear from `/queue` **by design**, regardless of the read-side bug. So "my row isn't in `/queue`" has at least three innocent causes — already completed, cancelled, or failed-terminal. **`/lineage/{job_id}` is the only endpoint that surfaces terminal states.** Always use it.

Lineage states: `pending`, `leased`, `in_progress`, `in_review`, `needs_info`, `paused`, `completed`, `cancelled`, `failed`, `dead_letter`. The first six are active and would also appear in `/queue` (when `/queue` is honest). The last four are terminal and ONLY surface in `/lineage/{job_id}`.

Once STORY-918 (v1↔v2 sync) ships, the `/queue` endpoint's active-lane reads should be reliable again — but `/queue` will still never show terminal states; that's design, not bug.

**Do not use the v1 endpoint** (`POST /api/dispatch`) for fresh enqueue. It still exists for legacy callers but its v2 mirror is unreliable. Reading from it (e.g. `/api/dispatch/queue`, `/api/dispatch/history`) is fine where v2 doesn't yet have parity.

**When to use the queue vs Teams:**
- **Queue:** Follow-up stories, well-defined tasks where the seed.md has all context
- **Teams (Method 2):** Initial detailed dispatch with custom context, constraints, inline implementation steps

**Method 2 (for detailed initial dispatch): Send via Graph API (Bash tool)**

Send the message directly via Microsoft Graph API using the locally stored token. Use this Bash command pattern:

```bash
TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.agent-ops/graph-token.json'))['access_token'])")

# Resolve agent email to chat ID
CHAT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  'https://graph.microsoft.com/v1.0/me/chats?$top=50&$expand=members' | \
  python3 -c "
import sys,json
d=json.load(sys.stdin)
for c in d.get('value',[]):
    for m in c.get('members',[]):
        if m.get('email','').lower() == '<agent-email>':
            print(c['id']); sys.exit(0)
print('NOT_FOUND')")

# Send message (HTML format so Teams renders headers, lists, bold)
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body":{"contentType":"html","content":"<html-message-content>"}}' \
  "https://graph.microsoft.com/v1.0/chats/${CHAT_ID}/messages"
```

Agent email lookup (from agent-registry.json):
- dan → tech-agent-dan@gorillacommerce.co
- derrick → tech-agent-derrick@gorillacommerce.co

If the token is expired, refresh it first:
```bash
bash /mnt/c/Projects/tech-dev-agents/tools/agent-ops-mcp/auth/graph-token.sh
```

If the chat ID is NOT_FOUND, the user needs to start a 1:1 chat with that agent in Teams first.

**HTML conversion:** Before sending, convert the markdown prompt to HTML for Teams rendering:
- `## Heading` → `<h2>Heading</h2>`
- `### Heading` → `<h3>Heading</h3>`
- `**bold**` → `<b>bold</b>`
- `- item` → `<li>item</li>` wrapped in `<ul>`
- `1. item` → `<li>item</li>` wrapped in `<ol>`
- Newlines between sections → `<br>`
- Code blocks → `<pre>code</pre>`

Use Python to convert: write the markdown to a temp file, then convert with a script before sending.

Confirm delivery by checking for a message `id` in the response.

**Fallback (if Graph API fails):**
- Print the final prompt in a fenced code block
- Tell the user: "Graph API send failed. Copy this to the agent's Teams chat."
- Do NOT attempt RemoteTrigger, schedule, or any alternative

**If `all` (broadcast):**
- Split stories across agents (group by dependency, balance by effort)
- Send each agent their batch with awareness of the other's work
- Each agent gets: their stories + "Dan is working on X, do not touch those files"

### Update tracking

- `backlog.md` — set Assignee column for dispatched stories
- `.project` — update Story Status with assignee and current phase
- Monday.com — update task assignee if board exists

### Confirm

```
Dispatched to Dan:
- STORY-018: Ops Console Dedicated VM (Phase 7 → Done)
Context: "VM at 137.116.63.176, DNS live, skip steps 1-2"
Mode: detailed (implementation steps + test specs included)
Agent status: idle

Monitor via Loki: {agent="dan"} |~ "START|DONE"
```

---

## Agent Handoff (sharing this with a remote agent)

When a remote agent in another project / repo / machine needs to dispatch
work into this fleet, **do not try to walk them through this whole skill**.
Paste the block below verbatim into their CLAUDE.md, system prompt, or
chat. It's self-contained — they will not need to read this skill to
follow it. (User trigger: "what do I tell the other agent so it can use
the dispatch queue.")

````markdown
# How to dispatch work to Gorilla Commerce tech-dev-agents

Use the v2 queue API. Do NOT use Microsoft Graph, Teams, or any
device-code auth flow — that path is for ad-hoc messages only.

## Setup

Set `OPS_CONSOLE_API_KEY` in your environment. Ask Mark for the value
if you don't have it.

## Enqueue a story

```bash
curl -X POST "https://tech-dev-agents.gorillacommerce.ai/api/dispatch/v2/enqueue" \
  -H "X-API-Key: $OPS_CONSOLE_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Worker-Version: 2.0" \
  -d '{
    "story_id": "STORY-XXX",
    "repo": "<repo-name>",
    "scope": "small",
    "prompt": "<full prompt including branch name in parens like (story-XXX/slug) and a pointer to features/story-XXX-slug/seed.md>",
    "title": "<short title>",
    "enqueued_by": "<your-name>",
    "target_role": "developer"
  }'
```

## Required fields

- `story_id` must match `^STORY-\d+$`
- `repo` is the GitHub repo name (no org prefix)
- `scope` is `small`, `medium`, or `large`
- `X-Worker-Version: 2.0` header is required — the v2 router rejects calls without it
- The seed file at `features/story-XXX-slug/seed.md` must already be pushed to
  remote `main` before you call enqueue. If it only exists locally, agents
  won't see it when they claim.

## What success looks like

HTTP 200 with a body like:
```json
{"job_id":"...","repo":"...","story_id":"STORY-XXX","scope":"...","enqueued_at":"..."}
```

## Common errors

- HTTP 422 → request body invalid. Check `story_id` regex and required fields.
- HTTP 409 → an active job with the same correlation already exists. Cancel
  or wait for it to terminate before retrying.
- HTTP 401 → missing or wrong `X-API-Key`.
- HTTP 426 / unexpected → `X-Worker-Version` header missing.

## Verification — use `/lineage/{job_id}`, NOT `/queue`

The `/api/dispatch/v2/queue` endpoint has a known read-side bug (since
at least 2026-05-12) that returns 0 rows in every lane even when the
row exists. Multiple remote agents have hit this and falsely concluded
their enqueue was orphaned. **Do not use `/queue` for write
verification.** Use the lineage endpoint — it reads `dispatch_jobs`
directly and is honest:

```bash
curl -sS -H "X-API-Key: $OPS_CONSOLE_API_KEY" \
  "https://tech-dev-agents.gorillacommerce.ai/api/dispatch/v2/lineage/$JOB_ID"
```

Returns `{"chain":[{"job_id":"<uuid>","state":"pending|leased|in_progress|in_review|needs_info|completed|...","attempt":...}]}`. Any non-error response means the row exists. The `state` field tells you whether it's still pending or already claimed.

**Only escalate to Mark if `/lineage/{job_id}` returns 404.** That's the
only true-orphaned signal. A 0-row `/queue` response is a known bug,
not orphanage — do NOT re-enqueue and do NOT fall back to v1
`/api/dispatch` or to Graph/Teams based on `/queue` alone.

`/queue` only shows ACTIVE lanes (`pending`, `in_progress`,
`in_review`, `paused`, `needs_info`, `claimed`). There is no
`completed`/`cancelled`/`failed` lane — terminal states are
intentionally absent. So "missing from `/queue`" can also mean the
job already finished. The `/lineage/{job_id}` state field is the
only honest signal for terminal outcomes.

## Do NOT

- Do not POST to `/api/dispatch` (v1). Its v1→v2 mirror silently drops rows.
- Do not use Microsoft Graph / Teams chat to dispatch. That's a fallback
  for ad-hoc messages, not for queueing work.
- Do not dispatch a story whose `seed.md` is only on a local branch —
  push to remote `main` first.
````

**Maintenance:** if the API key rotates, or the host/path changes, update
the block above so the next handoff is still copy-paste-correct.

---

## Examples

**Default (detailed for Medium+ scope) — asks for context, builds full prompt with steps/tests:**
```
/dispatch dan STORY-019
```

**Brief mode for a Small story:**
```
/dispatch dan STORY-021 --brief
```

**With inline context:**
```
/dispatch dan STORY-018 "VM provisioned at 137.116.63.176. DNS live. Skip steps 1-2."
```

**Review and refine flow:**
```
/dispatch derrick STORY-020
→ [gathers seed, asks for context]
User: "he needs to read the existing ops_console code first"
→ [builds detailed prompt with steps, tests, decision points — shows draft]
User: "add: make sure to test with both Python 3.11 and 3.12"
→ [revises, shows updated section]
User: "change step 3 to use uv not pip"
→ [revises, shows updated section]
User: "send it"
→ [dispatches via MCP, updates tracking]
```

**Epic split:**
```
/dispatch all EPIC-2 "Dan takes backend, Derrick takes frontend. Share the API contract before starting."
```

**Force detailed on a Small story:**
```
/dispatch dan STORY-021 --detailed "this is trickier than it looks, needs careful steps"
```

**Cancel:**
```
/dispatch dan STORY-019
→ [shows draft]
User: "cancel"
→ "Dispatch cancelled. No message sent."
```
