---
name: council
description: Invoke LLM Council for multi-model review of current work.
---

# Council

Invoke LLM Council for multi-model review of current work.

## Prerequisites

- LLM Council running locally (`~/projects/llm-council`)
- Start with: `cd ~/projects/llm-council && ./start.sh`

## Usage

```
/council                     # Review current phase artifact
/council [file]              # Review specific file
/council selection           # Review for Phase 4→5 decision
/council design              # Review for Phase 6→7 decision
```

## Steps

1. **Check council is running** — Verify http://localhost:8001 is accessible
2. **Determine review type:**
   - No args: Review current phase artifact based on .project
   - File specified: Review that file
   - "selection": Use Phase 4→5 prompt
   - "design": Use Phase 6→7 prompt
3. **Prepare prompt** based on review type
4. **Create council conversation** — POST to /api/conversations
5. **Submit for review** — POST artifact + prompt to /api/conversations/{id}/message
6. **Wait for 3-stage process:**
   - Stage 1: Individual opinions
   - Stage 2: Cross-review rankings
   - Stage 3: Chairman synthesis
7. **Present results** — Show final recommendation and key insights
8. **Update .project** — Record council deliberation ID and outcome

## Review Prompts

**Selection (Phase 4→5):**
```
Review the following analysis. Select the best approach and provide rationale.
Focus on: feasibility, risk, effort, impact.
```

**Design (Phase 6→7):**
```
Review this technical design before implementation.
Identify: missing edge cases, security concerns, performance risks, integration issues.
```

## Output

- Council recommendation with rationale
- Key concerns raised by council members
- Deliberation ID linked in .project
