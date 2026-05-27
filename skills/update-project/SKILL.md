---
name: update-project
description: Sync an existing project with the latest SDLC scaffolding from coding-ai-config — updates submodule, ensures symlinks, and verifies config.
---

# Update Project

Ensure an existing project has the latest SDLC scaffolding from coding-ai-config. Run this when starting work on a project that may be out of date.

## Usage

```
/update-project
```

No arguments needed — operates on the current working directory.

## Steps

### 1. Verify .sdlc submodule exists and is up to date
```bash
git submodule update --init --remote .sdlc
```
If `.sdlc/` does not exist, abort with: "This project has no .sdlc submodule. Use /new-project instead."

### 2. Ensure AGENTS.md symlink
Check if `./AGENTS.md` exists and points to `.sdlc/AGENTS.md`. If not:
```bash
ln -sf .sdlc/AGENTS.md ./AGENTS.md
```

### 3. Ensure .claude/agents/ symlinks
```bash
mkdir -p .claude/agents
```
For each agent file in `.sdlc/.claude/agents/*.md`:
- If a symlink already exists and points to the right target → skip
- If a regular file exists (old copy) → replace with symlink
- If missing → create symlink
```bash
ln -sf ../../.sdlc/.claude/agents/sonnet-worker.md .claude/agents/sonnet-worker.md
ln -sf ../../.sdlc/.claude/agents/opus-worker.md .claude/agents/opus-worker.md
```

### 4. Ensure .claude/skills symlink
```bash
ln -sf ../.sdlc/skills .claude/skills
```

### 5. Ensure .gemini/skills and .codex/skills symlinks (if dirs exist)
Only create if the parent directory (`.gemini/` or `.codex/`) already exists:
```bash
[ -d .gemini ] && ln -sf ../.sdlc/skills .gemini/skills
[ -d .codex ] && ln -sf ../.sdlc/skills .codex/skills
```

### 6. Check for stale files
Warn if any of these exist as regular files instead of symlinks (they should be managed by the submodule):
- `AGENTS.md` (should be symlink)
- `software-development-guidance.md` (should be in `.sdlc/`)
- `.claude/agents/sonnet-worker.md` (should be symlink)
- `.claude/agents/opus-worker.md` (should be symlink)

### 7. Report results
Output a summary table:

```
SDLC Update Summary
─────────────────────────────────
.sdlc submodule    ✓ updated to <commit>
AGENTS.md          ✓ symlinked
.claude/agents/    ✓ 2 agents symlinked
.claude/skills/    ✓ symlinked
.gemini/skills/    ✓ symlinked (or ○ skipped)
.codex/skills/     ✓ symlinked (or ○ skipped)
Stale files        ✓ none (or ⚠ list)
```

## What this does NOT do
- Does not create config.yaml, .project, backlog.md, or other project-specific files — those are /new-project responsibilities
- Does not modify CLAUDE.md — that's project-specific
- Does not touch Asana
- Does not run any phases or advance stories
- Read-only except for symlinks and submodule update
