---
name: schedule-cron
description: Schedule a recurring job in the agent's Linux crontab (subscription-billed Claude Code path). Use this for ANY recurring work — never use the hermes JSON cron system.
---

# Schedule a Cron Job

Add a recurring job to the agent's Linux crontab so it runs through the cheap Claude Code subscription path, NOT the expensive Foundry-billed hermes JSON cron.

## When to use this

Any time you need recurring work: monitoring a rollout, checking a queue, polling a metric, daily/weekly reviews, hourly heartbeats. If the cadence is "every N minutes/hours/days," this is the skill.

## Cost rationale (READ THIS FIRST — it's why the skill exists)

There are **two** cron paths on each agent VM and they hit different billing systems:

| Path | Where jobs live | Billing | Cost ratio |
|------|-----------------|---------|------------|
| **Linux crontab** (this skill) | `crontab -l` (per-user) | Anthropic subscription via local `claude` CLI | ~1× |
| **Hermes JSON cron** (do NOT use) | `~/.hermes/cron/jobs.json` | Azure Foundry → Claude API | ~5–10× |

The crontab wrapper (`/home/hermes/.hermes/scripts/run_cron.sh`) explicitly does:
```bash
unset ANTHROPIC_BASE_URL ANTHROPIC_TOKEN
```
That single line is the difference between subscription billing and Foundry billing. Hermes JSON cron has those vars set, so every fire bills Foundry. **Always use crontab.**

The hermes JSON cron system is **deprecated**. Morris's regular jobs were migrated off it on 2026-04-24. Don't add new entries there.

## Usage

```
/schedule-cron <job-name> <cadence> <script>
```

Examples:
```
/schedule-cron foundation-rollout-monitor every-30m sdk_state_sync.py
/schedule-cron pr-tracker-refresh "*/15 * * * *" heartbeat-collector.py
/schedule-cron daily-cost-summary "0 9 * * *" sdk_daily_cost.py
```

## Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `job-name` | Yes | Short identifier (kebab-case). Used as the `run_cron.sh` job label and log slug. |
| `cadence` | Yes | Either a 5-field cron expression (`"*/30 * * * *"`) OR a friendly form (`every-30m`, `every-1h`, `daily-9am`, `weekday-10am`). |
| `script` | Yes | Path to the script. Bare filename → resolves under `/home/hermes/.hermes/scripts/`. Absolute path → used as-is. |

## Steps

### 1. Resolve cadence to a 5-field cron expression

If the cadence is a 5-field cron expression already, use it verbatim. Otherwise convert:

| Friendly form | Cron expression |
|---------------|-----------------|
| `every-Nm` (N ≤ 59) | `*/N * * * *` |
| `every-Nh` (N ≤ 23) | `0 */N * * *` |
| `every-Nd` | `0 0 */N * *` |
| `daily-HHam` / `daily-HHpm` | `0 H * * *` (24-hour) |
| `weekday-HHam` / `weekday-HHpm` | `0 H * * 1-5` |
| `weekly-<dow>-HHam` (mon/tue/...) | `0 H * * <0-6>` |

If the input doesn't cleanly map, fall back to "give me the explicit 5-field expression."

### 2. Resolve script path

```python
if script.startswith('/'):
    script_path = script
else:
    script_path = f'/home/hermes/.hermes/scripts/{script}'
```

Verify the file exists and is executable. If not, fail with a clear error — don't add a broken cron entry.

### 3. Add to crontab

Run as the `hermes` user (this skill is invoked from a hermes-owned agent session, no sudo needed):

```bash
JOB_NAME="<job-name>"
CRON_EXPR="<5-field expression>"
SCRIPT_PATH="<resolved path>"
WRAPPER=/home/hermes/.hermes/scripts/run_cron.sh

# Snapshot current crontab
crontab -l > /tmp/cron-before.txt 2>/dev/null || touch /tmp/cron-before.txt

# Refuse to add a duplicate job-name
if grep -qF "\"${JOB_NAME}\"" /tmp/cron-before.txt; then
  echo "ERROR: a cron entry for ${JOB_NAME} already exists. Edit or remove the existing entry first." >&2
  exit 1
fi

# Append the new line and install
{
  cat /tmp/cron-before.txt
  echo ""
  echo "# Added $(date -u +%Y-%m-%dT%H:%M:%SZ) by /schedule-cron"
  echo "${CRON_EXPR} ${WRAPPER} \"${JOB_NAME}\" ${SCRIPT_PATH}"
} > /tmp/cron-after.txt

crontab /tmp/cron-after.txt
```

### 4. Verify

```bash
crontab -l | grep -F "\"${JOB_NAME}\""
```

If the line is there, report success with the cron expression and the next-fire time. If the line is missing, the install failed — surface the error and don't claim success.

### 5. Confirm to user

Report in this format:
```
Scheduled: <job-name>
Cadence:   <cron expression>  (next fire: <YYYY-MM-DD HH:MM UTC>)
Script:    <full path>
Billing:   Subscription (crontab path — NOT Foundry)
```

## Anti-patterns

- **Do NOT write to `~/.hermes/cron/jobs.json`.** That's the Foundry-billed system. Adding entries there can 5–10× the cost of the same recurring work. If you find yourself wanting to use it, stop and use this skill instead.
- **Do NOT `sudo systemctl` anything.** crontab edits don't need a service restart — `cron.service` re-reads the file automatically.
- **Do NOT skip `run_cron.sh`.** The wrapper is what unsets the Foundry env vars and writes structured logs. Calling the script directly from cron bypasses both protections.
- **Do NOT add a duplicate `job-name`.** If an entry exists, ask the user whether to replace, edit, or skip.

## Removing a cron entry

```bash
crontab -l | grep -vF "\"<job-name>\"" | crontab -
```

Verify with `crontab -l` afterward. Don't claim success without verifying.

## Listing current jobs

```bash
crontab -l | grep -E '^[^#]' | grep -v '^$'
```

This filters out comments and blank lines so you see only active entries.
