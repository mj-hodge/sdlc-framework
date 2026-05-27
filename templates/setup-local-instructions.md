# Local Setup Instructions

> **AGENT DIRECTIVE:** Run ALL steps in this file before starting any SDLC work on this project. Do not skip any step. If a step fails, fix it before proceeding.

## 1. SDLC Framework (run once, update each session)

```bash
# First time: clone SDLC framework if not present
if [ ! -d /opt/sdlc-framework ]; then
  git clone https://github.com/hpi-gorillacommerce/sdlc-framework.git /opt/sdlc-framework
fi

# Update to latest
cd /opt/sdlc-framework && git pull origin main

# Copy skills into Claude Code (real copies, not symlinks)
rm -rf ~/.claude/skills
cp -r /opt/sdlc-framework/skills ~/.claude/skills

# Copy into this project
rm -rf .claude/skills
cp -r /opt/sdlc-framework/skills .claude/skills
cp -r /opt/sdlc-framework/agents .sdlc/agents 2>/dev/null || true
```

## 2. Python Virtual Environment (MANDATORY)

```bash
# Create venv if it doesn't exist
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Install project dependencies
pip install -e ".[dev]" 2>/dev/null || pip install -e . 2>/dev/null || echo "No pip installable package"

# Install test dependencies if requirements-dev.txt exists
if [ -f requirements-dev.txt ]; then
  pip install -r requirements-dev.txt
fi
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
```

**NEVER use `--break-system-packages`**. Always use a project-level `.venv`.

## 3. Node Dependencies (if applicable)

```bash
if [ -f package.json ]; then
  npm install
fi
```

## 4. Verify Setup

```bash
# Run tests to confirm environment works
source .venv/bin/activate
python -m pytest tests/ -x -q --timeout=60 2>&1 | tail -5
```

If tests fail due to missing dependencies, fix the setup. Do NOT proceed to SDLC work with a broken environment.

## 5. Git Identity

```bash
git config user.name "$(git config --global user.name)"
git config user.email "$(git config --global user.email)"
```

## Notes

- Each project gets its own `.venv` — never share between projects
- Always activate the venv before running tests or code: `source .venv/bin/activate`
- The SDLC framework is at `/opt/sdlc-framework` — update it at the start of each session
- Skills must be real copies in `.claude/skills/`, not symlinks (SDK can't follow symlinks)
