```markdown
# Research

## Problem Context
From seed.md: User authentication with email/password
- Scale: 500 now, 5,000 potential
- Budget: Minimal
- Timeline: 2 weeks
- Stack: FastAPI, PostgreSQL, React

---

## Solutions Evaluated

### Managed Services

#### Clerk
| Aspect | Assessment |
|--------|------------|
| What | Auth service with React components |
| Cost | Free <10k MAU, $100/mo at 5k users |
| Business tradeoff | Saves 1-2 weeks dev time; vendor lock-in; cost grows with scale |
| Technical tradeoff | Drop-in React SDK; requires their user model; adds external dependency |
| Verdict | BUY if budget allows |

#### Supabase Auth
| Aspect | Assessment |
|--------|------------|
| What | Auth built on PostgreSQL |
| Cost | Free <50k MAU, $25/mo Pro |
| Business tradeoff | Free tier covers us for 2+ years; pulls toward Supabase ecosystem |
| Technical tradeoff | Native PostgreSQL fit; self-host option; learning curve 1-2 days |
| Verdict | STRONG BUY — stack and budget fit |

#### Auth0
| Aspect | Assessment |
|--------|------------|
| What | Enterprise auth platform |
| Cost | $23/mo at 1k users, scales quickly |
| Business tradeoff | Overkill for our scale; paying for features we won't use |
| Technical tradeoff | Complex setup for simple use case |
| Verdict | SKIP |

---

### Libraries

#### fastapi-users
| Aspect | Assessment |
|--------|------------|
| What | Auth library for FastAPI |
| Cost | Free (MIT) |
| Business tradeoff | No vendor cost; we own maintenance; 2-3 days to implement |
| Technical tradeoff | FastAPI-native; handles JWT, password reset; some config complexity |
| GitHub | 4.2k stars, active |
| Verdict | ADAPT |

#### Custom (PyJWT + pwdlib)
| Aspect | Assessment |
|--------|------------|
| What | Build from standard components |
| Cost | Free |
| Business tradeoff | Full control; security responsibility on us; 1-2 weeks to build properly |
| Technical tradeoff | No dependencies; must handle edge cases ourselves |
| Verdict | BUILD only if specific requirements |

---

## Recent Innovations

| Tool | Launched | Relevance |
|------|----------|-----------|
| Clerk React SDK | 6 months ago | Drop-in auth components |
| Supabase Auth Hooks | 3 months ago | Simplified server-side verification |
| Passkeys | Gaining adoption | Future consideration |

---

## Refactoring Opportunities

### R1: SQLAlchemy 2.0 Migration
| Aspect | Assessment |
|--------|------------|
| What exists | SQLAlchemy 1.4 with legacy query patterns |
| What's available | SQLAlchemy 2.0 with native async, improved typing |
| Why better | 30% performance improvement, cleaner async patterns |
| Migration effort | Medium — 2-3 days, mostly mechanical changes |
| Risk if ignored | 1.4 maintenance mode, missing performance gains |
| Recommendation | Plan for later — not blocking, schedule for next sprint |

### R2: Replace python-jose with PyJWT
| Aspect | Assessment |
|--------|------------|
| What exists | python-jose for JWT handling |
| What's available | PyJWT (actively maintained, 15k+ stars) |
| Why better | Active maintenance, smaller footprint, same functionality |
| Migration effort | Low — 1-2 hours, API nearly identical |
| Risk if ignored | python-jose abandoned 4+ years ago, has security vulnerabilities |
| Recommendation | Do now — low effort, improves security posture |

### R3: Pydantic V2 Upgrade
| Aspect | Assessment |
|--------|------------|
| What exists | Pydantic V1 models throughout |
| What's available | Pydantic V2 with 5-50x performance improvement |
| Why better | Faster validation, better error messages, rust core |
| Migration effort | Medium — requires model updates, ~1-2 days |
| Risk if ignored | V1 in maintenance mode |
| Recommendation | Plan for later — do alongside auth feature |

---

## Summary for Expansion

| Option | Type | Time to implement | Monthly cost | Risk |
|--------|------|-------------------|--------------|------|
| Supabase Auth | Buy | 1-2 days | $0 | Ecosystem lock-in |
| fastapi-users | Adapt | 2-3 days | $0 | Library breaking changes |
| Custom | Build | 1-2 weeks | $0 | Security responsibility |

**Context drives recommendation:**
- Budget minimal → rules out expensive services
- Timeline 2 weeks → favors buy/adapt
- Stack PostgreSQL → Supabase natural fit

---

## Red Flags
- Custom auth: security vulnerabilities if done wrong
- fastapi-users: breaking changes between major versions

## Dependency Health Audit

| Dependency | Status | Last Release | Issue | Action |
|------------|--------|--------------|-------|--------|
| python-jose | Abandoned | 4+ years | No maintainer activity, has security vulns | Migrate to PyJWT |
| SQLAlchemy | Healthy | 2 weeks | None | Continue |
| Pydantic | Aging | 3 months (V1) | V1 maintenance mode | Plan V2 migration |
| FastAPI | Healthy | 1 month | None | Continue |
| passlib | Abandoned | 4+ years | No activity, incompatible with bcrypt 5.x | Migrate to pwdlib |

**Urgent:** python-jose replacement (see R2 above), passlib replacement (use pwdlib[argon2])
**Planned:** Pydantic V2 migration (see R3 above)

## Open Questions
- [ ] Preference on Supabase ecosystem adoption?
- [ ] Compliance requirements affecting vendor choice?
```
