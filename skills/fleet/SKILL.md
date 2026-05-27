---
name: fleet
description: Quick status check on all agents — what they're working on, cost, availability
---

# Fleet Status

Show what every agent is doing right now so you know who's available for dispatch.

## Usage

```
/fleet              # Full status for all agents
/fleet dan          # Single agent deep dive
```

## Steps

### 1. Query Loki for recent activity (all agents)

Run this **single** Bash command. It sources env, queries Loki, and parses results in one shot — no intermediate variables or subshells that trigger permission prompts:

```bash
python3 /mnt/c/Projects/tech-dev-agents/scripts/fleet_status.py
```

If `fleet_status.py` does not exist, run the queries inline per step 1b.

### 1b. Inline fallback (only if fleet_status.py missing)

Run all three queries in a single python3 command to avoid permission prompts:

```bash
python3 -c "
import subprocess, json, time, os, re
from datetime import datetime, timezone

# Load env
env = dict(os.environ)
with open('/mnt/c/Projects/tech-dev-agents/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v

key = env.get('OPS_LOKI_API_KEY', '')
base = 'https://grafana.gorillacommerce.ai/loki/api/v1/query_range'
now = int(time.time())
start_2h = now - 7200
start_today = int(datetime.now(timezone.utc).replace(hour=0,minute=0,second=0).timestamp())

def loki_query(query, start, end, limit=50):
    import urllib.request, urllib.parse
    params = urllib.parse.urlencode({'query': query, 'start': start, 'end': end, 'limit': limit, 'direction': 'backward'})
    req = urllib.request.Request(f'{base}?{params}', headers={'Authorization': f'Bearer {key}'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

# Query 1: Sessions (START/DONE/END are in claude-code job)
sessions = loki_query('{job=\"claude-code\"} |~ \"\\\\[START\\\\]|\\\\[DONE\\\\]|\\\\[END\\\\]\"', start_2h, now)

# Query 2: Blockers
blockers = loki_query('{job=\"hermes-gateway\"} |~ \"Blocked:|Decision needed:|DENIED\"', start_2h, now, 10)

# Query 3: Today cost
costs = loki_query('{job=\"claude-code\"} |~ \"DONE.*cost\"', start_today, now, 100)

# Parse sessions
agents = {}
for stream in sessions.get('data', {}).get('result', []):
    agent = stream.get('stream', {}).get('agent', '?')
    if agent not in agents:
        agents[agent] = {'starts': [], 'dones': [], 'ends': []}
    for ts, line in stream.get('values', []):
        dt = datetime.fromtimestamp(int(ts[:10]))
        if '[START]' in line:
            # Extract story from prompt
            story = ''
            m = re.search(r'(STORY-\d+)', line)
            if m: story = m.group(1)
            prompt_start = line.find('[START]') + 8
            agents[agent]['starts'].append({'time': dt, 'story': story, 'prompt': line[prompt_start:prompt_start+80]})
        elif '[DONE]' in line:
            cost_m = re.search(r'cost=\\\$([\d.]+)', line)
            turns_m = re.search(r'turns=(\d+)', line)
            dur_m = re.search(r'duration=(\d+)', line)
            agents[agent]['dones'].append({
                'time': dt,
                'cost': float(cost_m.group(1)) if cost_m else 0,
                'turns': int(turns_m.group(1)) if turns_m else 0,
                'duration': int(dur_m.group(1)) if dur_m else 0,
            })
        elif '[END]' in line:
            agents[agent]['ends'].append({'time': dt})

# Parse costs for today
agent_costs = {}
for stream in costs.get('data', {}).get('result', []):
    agent = stream.get('stream', {}).get('agent', '?')
    for ts, line in stream.get('values', []):
        cost_m = re.search(r'cost=\\\$([\d.]+)', line)
        if cost_m:
            agent_costs[agent] = agent_costs.get(agent, 0) + float(cost_m.group(1))

# Parse blockers
blocker_lines = []
for stream in blockers.get('data', {}).get('result', []):
    agent = stream.get('stream', {}).get('agent', '?')
    for ts, line in stream.get('values', []):
        dt = datetime.fromtimestamp(int(ts[:10]))
        blocker_lines.append(f'{agent} {dt.strftime(\"%H:%M\")} {line[:100]}')

# Determine status
now_dt = datetime.now()
print(f'## Fleet Status ({now_dt.strftime(\"%H:%M\")} UTC)')
print()
print('| Agent | Status | Working On | Last Session | Today Cost |')
print('|-------|--------|-----------|-------------|-----------|')

for agent in sorted(agents.keys()):
    a = agents[agent]
    last_start = a['starts'][0] if a['starts'] else None
    last_end = a['ends'][0] if a['ends'] else None
    last_done = a['dones'][0] if a['dones'] else None

    # Status
    if last_start and (not last_end or last_start['time'] > last_end['time']):
        mins = int((now_dt - last_start['time']).total_seconds() / 60)
        status = f'active ({mins}m)'
        working = last_start.get('story', '') or last_start.get('prompt', '')[:40]
    elif last_end:
        mins = int((now_dt - last_end['time']).total_seconds() / 60)
        status = f'idle ({mins}m)'
        working = '—'
    else:
        status = 'offline'
        working = '—'

    last_info = ''
    if last_done:
        last_info = f'{last_done[\"turns\"]}t {last_done[\"duration\"]}s \\\${last_done[\"cost\"]:.2f}'

    cost_today = f'\\\${agent_costs.get(agent, 0):.2f}'

    print(f'| {agent} | {status} | {working} | {last_info} | {cost_today} |')

print()
if blocker_lines:
    print('**Blockers:**')
    for b in blocker_lines[:5]:
        print(f'- {b}')
else:
    print('**Blockers:** none')

available = [a for a in agents if agents[a]['ends'] and (not agents[a]['starts'] or agents[a]['ends'][0]['time'] > agents[a]['starts'][0]['time'])]
if available:
    print(f'**Available for dispatch:** {\", \".join(available)}')
"
```

### 2. Present the output directly

The python script outputs the formatted table. Present it as-is to the user.

### 3. Single agent deep dive (if agent name provided)

When `/fleet dan` is called, also query:

```bash
python3 -c "
# Same pattern as above but filter to specific agent
# query: {job=\"claude-code\", agent=\"dan\"} |~ \"\\[START\\]|\\[DONE\\]\"
# Show last 5 sessions with cost/turns/duration
# Also query {job=\"hermes-gateway\", agent=\"dan\"} |~ \"teams-m365.*Sent\" for last Teams message
"
```

## Notes

- Session data ([START], [DONE], [END]) is in `job="claude-code"`, NOT `job="hermes-gateway"`
- Blocker/error data is in `job="hermes-gateway"`
- Agent label: `agent="dan"` or `agent="derrick"`
- Use a single python3 command to avoid permission prompts from shell variable expansion
- If Loki is unreachable, fall back to SSH: `ssh -p 443 azureagent@<ip> "sudo -u hermes bash -c 'pgrep -af claude_sdk_tool.py'"`
