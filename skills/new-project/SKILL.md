---
name: new-project
description: Set up a new project with full SDLC scaffolding — submodule, CLAUDE.md, GEMINI.md, CODEX.md, skills, config.yaml.
---

# New Project

Set up a new project with full SDLC scaffolding.

## Usage

```
/new-project [project-name]
```

## Steps

1. **Create project directory** (if not exists)
2. **Initialize git** (if not already a repo)
3. **Add SDLC submodule and link AGENTS.md:**
   ```bash
   git submodule add https://github.com/YOUR-ORG/coding-ai-config.git .sdlc
   ln -s .sdlc/AGENTS.md ./AGENTS.md
   mkdir -p .claude/agents
   ln -s ../../.sdlc/.claude/agents/sonnet-worker.md .claude/agents/sonnet-worker.md
   ln -s ../../.sdlc/.claude/agents/opus-worker.md .claude/agents/opus-worker.md
   ```
4. **Create config.yaml:**
   ```yaml
   project:
     name: <project-name>
     mode: new_project
     scope: <ask user>

   council:
     enabled: true
     tier: free
   ```
5. **Create .project file** with initial state
6. **Create Asana project:**
   - Name: `sdlc-<project-name>`
   - Sections: Backlog, Ready, In Progress, E2E Gate, Done, Do Not Do
   - Description: Link to repository
7. **Create initial files:**
   - `backlog.md` — Empty template
   - `development-tasks.md` — Empty template
   - `README.md` — From template (`templates/readme.md`) with project name, key links placeholders, setup stubs
8. **Run Phase 1** — Invoke /phase-1 to capture concept

## Outputs

```
project-name/
├── .sdlc/              (git submodule → coding-ai-config)
├── .claude/agents/sonnet-worker.md → ../../.sdlc/.claude/agents/sonnet-worker.md
│   └── opus-worker.md → ../../.sdlc/.claude/agents/opus-worker.md
├── .claude/skills → ../.sdlc/skills
├── .gemini/skills → ../.sdlc/skills
├── .codex/skills → ../.sdlc/skills
├── .github/
│   └── dependabot.yml  (auto-updates .sdlc submodule)
├── AGENTS.md → .sdlc/AGENTS.md
├── CLAUDE.md           (generated)
├── GEMINI.md           (generated)
├── CODEX.md            (generated)
├── config.yaml
├── .project
├── backlog.md
├── development-tasks.md
└── README.md
```

Plus Asana project: `sdlc-<project-name>`

## Next Steps

After setup, user should:
1. Complete Phase 1 (seed.md)
2. Follow phase workflow based on scope
