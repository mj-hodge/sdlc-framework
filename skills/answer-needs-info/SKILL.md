---
name: answer-needs-info
description: >
  Answer a needs_info question on a dispatched story so the queue resumes.
  Trigger phrases: "answer needs info", "/answer-needs-info STORY-N",
  "unblock the question on STORY-N", "answer STORY-N's question". Use when
  a row in the dispatch queue is in needs_info and a human (Mark or Morris)
  can answer the QUESTION.md from seed + repo context. Pure-prompt skill —
  no external scripts. Claude executes curl + gh api directly.
category: dispatch
agent: morris
---

# answer-needs-info

A dispatched story has gone into `needs_info` because the agent wrote a
`QUESTION.md` and called `/api/dispatch/pause`. This skill walks Claude
through reading the question, drafting the answer, writing `ANSWER.md`
to the story's branch, and calling `/api/dispatch/resume` so the agent
can pick the work back up.

The skill has two modes:

| Mode | Output file | Resume API |
|------|-------------|-----------|
| normal (default) | `features/<story>/ANSWER.md` | `POST /api/dispatch/resume/<STORY-N>` |
| `--escalate` | `features/<story>/ESCALATE.md` | `POST /api/dispatch/pause/<STORY-N>` |

`--escalate` is the right call when the question is a real business
decision (recipient list, schedule, policy) that only Mark can answer.
The story stays paused; Mark gets a Teams ping; no resume happens.

## Prerequisites

- `OPS_CONSOLE_API_KEY` env var must be set on the agent VM. The skill
  reads it from the environment and passes it as `X-API-Key:` on every
  ops-console call. Never log or echo the value.
- `gh` CLI authenticated to read/write `hpi-gorillacommerce/<repo>`.
- The base URL `https://tech-dev-agents.gorillacommerce.ai`. Set as
  `BASE_URL` for brevity below.

## Arguments

```
/answer-needs-info STORY-N [--dry-run] [--escalate] [--reason "<why>"]
```

- `STORY-N` (required): canonical story id. Case-insensitive on input,
  but normalize to upper-case (`STORY-633`, not `story-633`) before any
  API call. If the user gave `story-633`, internally treat it as
  `STORY-633` in every URL and file path.
- `--dry-run`: print every action with the prefix `WOULD:` and exit.
  No HTTP writes, no file writes, no `/resume` call. Use this to walk
  Mark through the proposed answer before executing.
- `--escalate`: write `ESCALATE.md` instead of `ANSWER.md` and call
  `/pause` instead of `/resume`. Requires `--reason` so the escalation
  message tells Mark what's blocking.
- `--reason "<why>"`: free-text, surfaces in the ESCALATE.md body and
  in the Teams ping. Required with `--escalate`, optional otherwise.

## Recipe

### Step 1 — Look up the dispatch row

```
curl -s -H "X-API-Key: $OPS_CONSOLE_API_KEY" \
  "$BASE_URL/api/dispatch/v2/queue" | jq '.needs_info'
```

The v2 queue endpoint returns the adapter shape (`pending`,
`in_progress`, `in_review`, `paused`, `needs_info`). Find the row whose
`story_id` matches the requested STORY-N. Capture `job_id`, `repo`,
`needs_info_path`, and the head branch (typically `story-N/story-N`).
If no row matches, stop with a clear error — the story is not in
needs_info, there is nothing to answer.

### Step 2 — Fetch the QUESTION

The agent already wrote `QUESTION.md` to the story's branch. Read it
without cloning the repo:

```
gh api repos/hpi-gorillacommerce/<repo>/contents/<needs_info_path>?ref=<branch> \
  --jq '.content' | base64 -d
```

If the file does not exist on that branch, stop — the dispatch row is
inconsistent with the branch state and Mark needs to look at it.

### Step 3 — Draft the answer

Read the question carefully. The agent has typically presented two or
more options and asked for a directive. The answer must be:

1. A clear directive on the first line (`Option A`, `Option B`, or a
   third path you describe).
2. One paragraph of rationale, citing seed lines verbatim when the
   answer is in the seed.
3. A "what to do next" section telling the agent the concrete steps
   to take when it resumes.
4. Signed `— Mark (via Morris)` (or `— Morris` if Mark explicitly
   delegated).

Keep it short. Do not invent acceptance criteria or new requirements —
if the question is asking for a real product decision you do not have
authority to make, stop and rerun with `--escalate`.

### Step 4 — Confirm before writing

Show Mark the drafted ANSWER.md content and ask:

> Confirm? [y/N]

Use the AskUserQuestion tool, or print the draft and explicitly wait
for confirmation. Do NOT proceed without an affirmative reply.

If `--dry-run` is set, skip the confirmation prompt — instead print the
draft prefixed with `WOULD: write features/<story>/ANSWER.md` (or
`WOULD: write features/<story>/ESCALATE.md` in escalate mode), then
print `WOULD: POST /api/dispatch/resume/<STORY-N>` (or `/pause/`) and
exit. The dry-run preview must be sufficient for Mark to greenlight a
real run by re-issuing the command without `--dry-run`.

### Step 5 — Commit the answer file

The target path is the same folder as the QUESTION.md, with a
different filename. Build it from `needs_info_path` by replacing the
basename:

- normal: `features/<story-folder>/ANSWER.md`
- escalate: `features/<story-folder>/ESCALATE.md`

Encode the answer body and PUT it via the contents API:

```
B64=$(printf '%s' "$ANSWER_BODY" | base64 -w0)
EXIST=$(gh api repos/hpi-gorillacommerce/<repo>/contents/<answer-path>?ref=<branch> \
  --jq '.sha' 2>/dev/null || true)

if [ -z "$EXIST" ] || echo "$EXIST" | grep -q "Not Found"; then
  gh api -X PUT repos/hpi-gorillacommerce/<repo>/contents/<answer-path> \
    -f message="STORY-N: ANSWER.md — <one-line summary>" \
    -f content="$B64" \
    -f branch="<branch>"
else
  gh api -X PUT repos/hpi-gorillacommerce/<repo>/contents/<answer-path> \
    -f message="STORY-N: ANSWER.md — <one-line summary>" \
    -f content="$B64" \
    -f branch="<branch>" \
    -f sha="$EXIST"
fi
```

Verify the response contains a `commit.sha` before continuing.

### Step 6 — Resume (or pause-with-escalation)

Normal mode (v2 operator-resume — emits `requeued` event, story moves
back to work_queue lane for next polling cycle):

```
curl -s -X POST -H "X-API-Key: $OPS_CONSOLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo":"<repo>","story_id":"STORY-N","reason":"answered"}' \
  "$BASE_URL/api/dispatch/v2/operator/resume"
```

Expect HTTP 200 and a body like `{"job_id":"...","prior_state":"needs_info"}`.
If the response is 409 ("not in needs_info") or 404, surface the body
to Mark — the dispatch state has drifted from what the skill expected.

Note: this endpoint is MANAGER-role gated. The skill must run with an
API key that authenticates as a manager (Morris's API key works;
Mark's developer keys may not).

Escalate mode (no resume — instead, log the escalation and notify Mark
without changing dispatch state). v2 doesn't have a separate /pause
endpoint because the story is already in `needs_info`/`human_queue`.
Just commit ESCALATE.md, ping Mark in Teams, and skip the resume call:

```
# (no v2 dispatch call — story stays in needs_info lane)
# Send Mark a Teams summary listing the story id, the question
# verbatim, and the reason. He resumes in his own time via the
# operator/resume endpoint above.
```

### Step 7 — Report

Output one short line back to the user:

- normal: `STORY-N answered — branch <branch> · resumed (status: pending)`
- escalate: `STORY-N escalated to Mark — ESCALATE.md committed · paused`
- dry-run: `STORY-N — dry-run preview only, no writes`

## Hard rules

- Never invoke an interpreter or any helper script. terminal_guard
  blocks interpreter invocations on the agent VMs (that is exactly
  why the prior STORY-770 implementation failed). The whole flow is
  curl + gh api in Bash, nothing else.
- Never leave `OPS_CONSOLE_API_KEY` in command output. Pass it as a
  header via `-H "X-API-Key: $OPS_CONSOLE_API_KEY"` and never echo
  the variable.
- If the QUESTION.md is asking for a real product decision (price
  thresholds, recipient lists, schedule windows, policy choices) and
  you do not have a direct answer from the seed, escalate. Do not
  guess.
- One ANSWER.md per QUESTION.md. If the row is back in needs_info
  with a fresh QUESTION.md, treat it as a new question — write a new
  ANSWER.md (replacing the old contents via the `sha` field shown
  above) and resume again.

## Worked example

Reference: `features/story-760-no-hardcoded-default-branch-contract/ANSWER.md`
on branch `story-760/story-760` in `tech-dev-agents`. That answer
selected Option A, cited the seed, and told the agent the three
concrete next steps. Match that shape.
