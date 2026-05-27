# CODEX.md

> **DIRECTIVE:** Follow [AGENTS.md](./AGENTS.md) as the primary SDLC policy.
> At session start and after context resets, re-read `AGENTS.md`, `config.yaml`, and `.project` when present.

---


## SDLC Process (Required)

- Treat prompts like "spec ..." as a Phase 1 start.
- Follow scope paths and phase gates defined in `AGENTS.md`.
- Read the phase persona from `agents/phase-X-*.md` before each phase.
- Produce required deliverables in `features/<story-folder>/`.
- Keep `.project`, `backlog.md`, `development-tasks.md`, and Asana synchronized at every transition.

## Codex Execution

- Codex does not depend on slash command support.
- Use the same workflows through plain-language directives (for example: `spec add dark mode`, `next STORY-016`).
- Codex MCP configuration lives in `~/.codex/config.toml`; use `codex mcp add ...` and `codex mcp list` to manage servers.
- Use `skills/*/SKILL.md` as the procedural source of truth.
- Use wrappers (required): `cai asana-api.sh ...` for Asana helper calls and `gci-safe "<commit message>"` for check-ins. For Asana commands, use the direct shape only (`cai asana-api.sh ...`) and avoid shell wrappers such as `/bin/zsh -lc`.
- For Asana operations, run one direct wrapper command at a time (`cai asana-api.sh <subcommand> ...`).
- Never shell-wrap Asana commands (`/bin/zsh -lc ...`) and never use pipes, redirects, command substitution (`$(...)`), or `&&`/`||` in the same Asana command.
- Keep Asana arguments inline and simple so the approved prefix remains stable across sessions.
- For epic completion, run the retrospective workflow: `retro <epic-name>`. This analyzes outcomes and applies SDLC improvements to `coding-ai-config`. See `skills/retro/SKILL.md`.
- For `/next` and `/spec` parity details, see:
  - [skills/next/codex.md](./skills/next/codex.md)
  - [skills/spec/codex.md](./skills/spec/codex.md)

## References

- [AGENTS.md](./AGENTS.md)
- [software-development-guidance.md](./software-development-guidance.md)
- [agents/README.md](./agents/README.md)
- [skills/](./skills/)
