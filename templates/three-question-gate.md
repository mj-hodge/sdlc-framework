# 3-Question Gate

Phase 9 cannot close until all three questions below are answered. Copy this
block into `refinement-report.md` under a `## 3-question gate` heading and fill
it in. "N/A" is allowed but **requires a one-line justification** — a bare "N/A"
is rejected.

These questions mirror the continuous-improvement checklist in
`gc-data-v2/pipeline-template/.github/pull_request_template.md`. The phase-9
skill (`.sdlc/skills/phase-9/SKILL.md`) auto-invokes `/canon-backport <STORY-ID>`
after all three are answered, unless `--no-backport` is passed.

## Questions

1. **Canon-doc impact** — does this work expose a gap in `gc-data-v2/platform/*.md`?
   > (Yes / No / N/A + justification)

2. **Scaffold backport** — should this work land in `gc-data-v2/pipeline-template/`?
   > (Yes / No / N/A + justification)
   >
   > For non-pipeline builds, auto-answered:
   > `N/A — build is not a pipeline; no pipeline-template to backport into`.

3. **Sibling sweep** — do other v2 pipelines need this same change?
   > (Yes — list affected pipelines / No / Unknown — flag for triage)

## Gate Rules

- All three questions MUST be answered. Missing answers →
  `Phase 9 cannot close: 3-question gate incomplete`.
- A bare "N/A" without justification is rejected →
  `N/A requires justification (e.g. 'N/A — pipeline-specific business logic')`.
- After the gate is complete, Phase 9 auto-invokes `/canon-backport <STORY-ID>`
  and writes `canon_backport_invoked: <pr-url|no_gap_found>` into `.project`.
- Pass `--no-backport` to skip the auto-invocation (still requires all three
  answers).
