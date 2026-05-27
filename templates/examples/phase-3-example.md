```markdown
# Expansion

## Context
From seed.md: User authentication, 500→5k users, minimal budget, 2 weeks, FastAPI/PostgreSQL/React

From research.md: Supabase Auth (buy), fastapi-users (adapt), custom (build) identified as viable paths

---

## Approaches

### 1. Supabase Auth (Full Buy)
**Summary:** Use Supabase for auth and database, adopt their ecosystem
**Components:** Supabase Auth, Supabase PostgreSQL, Supabase JS client
**Optimizes for:** Speed to market, minimal code
**Sacrifices:** Database control, vendor independence
**Fit:** Greenfield project, okay with Supabase ecosystem, want to ship in days

| Dimension | Assessment |
|-----------|------------|
| Time | 1-2 days |
| Cost | $0 (free tier) |
| Risk | Low (proven service) |
| Lock-in | High |
| Flexibility | Low |

---

### 2. Supabase Auth + Own Database (Hybrid)
**Summary:** Use Supabase for auth only, keep our PostgreSQL for data
**Components:** Supabase Auth, existing PostgreSQL, custom user sync
**Optimizes for:** Auth simplicity while keeping data control
**Sacrifices:** Some integration complexity, need to sync user data
**Fit:** Want managed auth but own your data layer

| Dimension | Assessment |
|-----------|------------|
| Time | 3-4 days |
| Cost | $0 |
| Risk | Low-Medium |
| Lock-in | Medium (auth only) |
| Flexibility | Medium |

---

### 3. fastapi-users Library (Adapt)
**Summary:** Use established FastAPI auth library, customize as needed
**Components:** fastapi-users, existing PostgreSQL, custom frontend
**Optimizes for:** FastAPI-native solution, no external dependencies
**Sacrifices:** More implementation time, maintain library updates
**Fit:** Want to stay in Python ecosystem, avoid external services

| Dimension | Assessment |
|-----------|------------|
| Time | 3-5 days |
| Cost | $0 |
| Risk | Low (established library) |
| Lock-in | None |
| Flexibility | High |

---

### 4. Custom JWT Auth (Minimal Build)
**Summary:** Build minimal auth with PyJWT + pwdlib, just what we need
**Components:** PyJWT, pwdlib[argon2], custom endpoints, existing PostgreSQL
**Optimizes for:** Full control, minimal dependencies, only features we need
**Sacrifices:** Security responsibility, no built-in password reset/email verification
**Fit:** Simple requirements, team confident with auth security

| Dimension | Assessment |
|-----------|------------|
| Time | 5-7 days |
| Cost | $0 |
| Risk | Medium (security on us) |
| Lock-in | None |
| Flexibility | Maximum |

---

### 5. Custom Auth with Future-Ready Foundation (Build for Growth)
**Summary:** Build custom but structure for future OAuth, MFA, API tokens
**Components:** Custom auth module, role system, token infrastructure
**Optimizes for:** Foundation for future auth features
**Sacrifices:** More upfront time, building for needs we don't have yet
**Fit:** Clear roadmap toward enterprise features, have time to invest

| Dimension | Assessment |
|-----------|------------|
| Time | 1-2 weeks |
| Cost | $0 |
| Risk | Medium |
| Lock-in | None |
| Flexibility | Maximum |

---

### 6. Clerk (Premium Buy)
**Summary:** Use Clerk for complete auth with React components
**Components:** Clerk service, Clerk React SDK, webhook sync to our DB
**Optimizes for:** Best-in-class UX, zero auth code
**Sacrifices:** Monthly cost at scale, vendor dependency
**Fit:** Budget flexible, want polished auth UX immediately

| Dimension | Assessment |
|-----------|------------|
| Time | 1 day |
| Cost | $0 now, $100/mo at 5k users |
| Risk | Low |
| Lock-in | High |
| Flexibility | Low |

---

## Spectrum Summary

| Approach | Type | Time | Cost | Risk | Flexibility |
|----------|------|------|------|------|-------------|
| Supabase Full | Minimal/Buy | 1-2 days | $0 | Low | Low |
| Supabase Hybrid | Balanced/Buy | 3-4 days | $0 | Low-Med | Medium |
| fastapi-users | Balanced/Adapt | 3-5 days | $0 | Low | High |
| Custom Minimal | Conservative/Build | 5-7 days | $0 | Medium | Maximum |
| Custom Future-Ready | Forward-looking | 1-2 weeks | $0 | Medium | Maximum |
| Clerk | Premium/Buy | 1 day | $$ | Low | Low |

---

## Decision Axes for Analysis

1. **Build vs Buy:** Approaches 1-2, 6 buy; 3 adapts; 4-5 build
2. **Time vs Flexibility:** Fast options (1, 6) sacrifice flexibility
3. **Vendor dependency:** Approaches 4-5 have none; 1, 6 have high
4. **Future investment:** Approach 5 builds for growth; others solve for now

Ready for Analysis phase.
```
