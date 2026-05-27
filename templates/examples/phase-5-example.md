```markdown
# Selection

## Decision

**Selected: fastapi-users (Approach #1)**

## Rationale

1. **Gets us to market in budget:** No vendor costs, fits 2-week timeline
2. **Delivers the outcome:** Users can register, log in, maintain sessions — core problem solved
3. **Keeps options open:** No vendor lock-in; can evolve as we learn what users need

## Assumptions Validated

| Assumption | Validation |
|------------|------------|
| 3-5 day implementation | Based on library docs and similar past work — realistic |
| Team can learn library | FastAPI-native; team already knows the stack |
| Handles our requirements | Verified: JWT, registration, password reset all supported |

## MVP Scope

### In (Week 1-2)

| Feature | Rationale |
|---------|-----------|
| Email/password registration | Core requirement |
| Login with JWT | Core requirement |
| Session persistence | User expectation |
| Basic error messages | Usable experience |
| Logout | Complete the flow |

### Out (v1.1+)

| Feature | Rationale |
|---------|-----------|
| Password reset | Can handle manually for beta; add in v1.1 |
| Email verification | Not blocking for beta launch |
| Social login | Nice-to-have; not core need |
| Rate limiting | Add when we have traffic to limit |
| Refresh tokens | Session expiry acceptable for MVP |

### Quality Bar

- Login works reliably
- Errors don't crash the app
- UI is functional, not polished
- We can see logins in logs

## Risks Accepted

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Library breaking changes | Low | Medium | Pin version, update deliberately |
| Missing edge case in MVP | Medium | Low | Support users manually, fix in v1.1 |
| Password reset needed sooner | Medium | Low | Manual reset process as fallback |

## Fallback

If fastapi-users proves problematic (bad docs, missing features), we fall back to Supabase Hybrid. Adds 1-2 days but lower risk.

## Economic Summary

| Factor | Assessment |
|--------|------------|
| Build cost | 3-5 days engineering |
| Ongoing cost | $0 (no vendor) |
| Time to market | 2 weeks total |
| Rework risk | Low — standard patterns |

## Next Steps

1. Proceed to Design phase
2. Detailed specification for auth module
3. API design for auth endpoints
4. Test plan for core flows

Ready for Design.
```
