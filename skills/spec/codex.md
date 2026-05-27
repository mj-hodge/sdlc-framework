# spec — Codex Execution

Platform-specific execution details for the `spec` workflow in Codex sessions.

## Invocation

- Codex does not require slash commands.
- Treat both of the following as equivalent:
  - `/spec <feature description>`
  - `spec <feature description>`

## Execution Rules

1. Read `.project`, `config.yaml`, and `backlog.md`.
2. Run the Phase 1 workflow from `skills/spec/SKILL.md`.
3. Read and apply `agents/phase-1-seed.md`.
4. Enforce Phase 1 gate behavior (stop and wait for explicit approval).
5. If `multi_worker: true`, follow `start-story` protocol after approval.

## Output Guidance

- Keep the same output contract as other CLIs:
  - Phase 1 summary
  - scope classification + phase path
  - explicit next-step command (`/next STORY-ID`)
