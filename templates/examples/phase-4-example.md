```markdown
# Analysis

## Context
From seed.md: Auth for 500→5k users, minimal budget, 2-week timeline, FastAPI/PostgreSQL

From expansion.md: 6 approaches evaluated

## Evaluation Matrix

| Approach | Technical | Effort | Value | Future | Risk | Total |
|----------|-----------|--------|-------|--------|------|-------|
| Supabase Full | 4 | 5 | 4 | 2 | 4 | 19 |
| Supabase Hybrid | 4 | 4 | 4 | 3 | 4 | 19 |
| fastapi-users | 4 | 4 | 4 | 4 | 4 | 20 |
| Custom Minimal | 3 | 3 | 4 | 5 | 3 | 18 |
| Custom Future-Ready | 4 | 2 | 3 | 5 | 3 | 17 |
| Clerk | 5 | 5 | 5 | 2 | 4 | 21 |

---

## Detailed Assessments

### fastapi-users (Rank: #1)

**Strengths:**
- Native to our stack; no context switching
- Handles JWT, registration, password reset out of box
- No vendor dependency; full control
- Active maintenance; 4.2k GitHub stars

**Weaknesses:**
- 3-5 day implementation vs 1 day for managed services
- Must handle our own infrastructure (DB, email)
- Learning curve for library patterns

**Risks:**
- Library breaking changes: Low likelihood, Medium severity — pin versions, review changelogs
- Security gaps in implementation: Low likelihood if we follow docs — library handles hard parts

**Scores:**
| Dimension | Score | Justification |
|-----------|-------|---------------|
| Technical | 4/5 | Solid library, proven patterns, handles edge cases |
| Effort | 4/5 | 3-5 days; more than managed but reasonable |
| Value | 4/5 | Solves auth completely for our requirements |
| Future | 4/5 | No lock-in, extensible, we control the code |
| Risk | 4/5 | Established library, active community |

---

### Clerk (Rank: #2)

**Strengths:**
- Fastest to implement (1 day)
- Best-in-class UX out of box
- Handles all edge cases (password reset, email verification, etc.)

**Weaknesses:**
- $100/mo at 5k users — violates "minimal budget" constraint
- High vendor lock-in
- User data lives in their system

**Risks:**
- Cost growth: High likelihood, Medium severity — predictable but adds up
- Vendor lock-in: High likelihood, High severity if we want to migrate later

**Scores:**
| Dimension | Score | Justification |
|-----------|-------|---------------|
| Technical | 5/5 | Battle-tested, handles everything |
| Effort | 5/5 | 1 day implementation |
| Value | 5/5 | Solves auth completely with best UX |
| Future | 2/5 | High lock-in, data not ours |
| Risk | 4/5 | Low technical risk, high business risk (cost, lock-in) |

---

### Supabase Hybrid (Rank: #3)

**Strengths:**
- Free tier covers us
- Managed auth reliability
- Keep our own database for data

**Weaknesses:**
- Still pulls toward Supabase ecosystem
- User sync adds complexity
- Two systems to understand

**Risks:**
- Ecosystem pull: Medium likelihood, Low severity — can resist with discipline
- Sync complexity: Medium likelihood, Medium severity — adds moving parts

**Scores:**
| Dimension | Score | Justification |
|-----------|-------|---------------|
| Technical | 4/5 | Proven auth service |
| Effort | 4/5 | 3-4 days with sync logic |
| Value | 4/5 | Solves auth problem |
| Future | 3/5 | Medium lock-in, can migrate but effort required |
| Risk | 4/5 | Established service, some sync complexity |

---

## Recommendation

**#1: fastapi-users**

It's the sweet spot:
- **Technically sound:** Established library, proven patterns, handles security properly
- **Easiest viable path:** 3-5 days, reasonable for 2-week timeline
- **Delivers value:** Complete auth solution for our requirements
- **Doesn't sacrifice future:** No vendor lock-in, full control, extensible

**Trade-off acknowledged:** We spend 3-5 days instead of 1 day (Clerk). Worth it given budget constraint and future flexibility.

**If budget opens up:** Clerk becomes viable — faster with better UX.

**If timeline tightens:** Supabase Hybrid is fallback — slightly faster, some lock-in.

---

## Risks to Monitor

| Risk | Approach | Mitigation |
|------|----------|------------|
| fastapi-users breaking changes | #1 | Pin versions, review before updating |
| Scope creep in auth features | All | Stick to seed.md requirements |
| Timeline pressure | All | Supabase Hybrid as fallback |

Ready for Selection phase.
```
