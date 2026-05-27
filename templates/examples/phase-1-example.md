```markdown
# Seed

## Overview
| Field | Value |
|-------|-------|
| Mode | feature_update |
| Scope | medium |
| Feature Name | user-authentication |

## Problem Statement
Users cannot save their preferences or maintain identity across sessions. Every visit starts fresh, causing repeated setup and preventing personalized experiences.

## Desired Outcome (This Iteration)
Users can register and log in with email/password. Session persists across refreshes. Basic auth working end-to-end.

## Target User
Primary: Regular users who return multiple times per week
Secondary: Occasional users who expect their data to persist between visits

## Business Constraints
| Constraint | Value |
|------------|-------|
| Scale (now) | ~500 users initially |
| Cost | Minimal - avoid paid auth services |
| Timeline | 2 weeks for beta launch |
| Resources | Single developer |
| Tech | Must use existing PostgreSQL |

## Acceptance Criteria (This Iteration)
- [ ] New user can register with email and password
- [ ] Existing user can log in and see their previously saved data
- [ ] User remains logged in across browser refreshes
- [ ] Invalid credentials show clear error message
- [ ] User can log out and session is cleared

## Out of Scope (This Iteration)
- Social login (Google, GitHub, etc.)
- Password reset flow
- Email verification
- Multi-factor authentication
- Admin user management UI

## Assumptions
- Email addresses are unique identifiers
- Users have valid email addresses
- HTTPS will be configured

---

## Long-Term Context (For Expansion Agent)

> This section captures vision and future direction. NOT requirements for this iteration.

| Aspect | Future Consideration |
|--------|---------------------|
| Scale trajectory | Could grow to 5,000+ users if product succeeds |
| Future auth needs | Social login, SSO likely requested by enterprise users |
| Security evolution | MFA will be needed if handling sensitive data |
| Integration points | May need API tokens for third-party integrations |

This context informs architectural decisions but does NOT expand current scope.
```
