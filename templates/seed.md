# Seed

## Overview
| Field | Value |
|-------|-------|
| Mode | <new_project\|feature_update> |
| Scope | <trivial\|small\|medium\|large> |
| Criticality | <routine\|important\|critical> |
| Feature Name | <name if feature update> |

## Problem Statement
<1-2 sentences describing what problem we're solving>

## Target User / Use Case
<Who benefits and how they'll use it>

## Success Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>

## Constraints
| Constraint | Value |
|------------|-------|
| Budget | <$0 / minimal / funded> |
| Timeline | <days / weeks / flexible> |
| Scale | <users, requests/sec, data volume> |

## Performance Requirements (Medium+ Scope)
| Metric | Target |
|--------|--------|
| API response time (p95) | < ___ms |
| Page load time | < ___s |
| Database queries per request | < ___ |
| Bundle size budget | < ___KB |

_Leave blank if not applicable. Phase 6 design must validate against these._

## Security Constraints (Non-Negotiable)

_These are embedded in the spec so AI code generation is secure by construction. Remove any that don't apply, add project-specific ones._

- [ ] All database queries MUST use parameterized queries (no string concatenation)
- [ ] All user input MUST be validated and sanitized before use
- [ ] All API endpoints MUST require authentication (unless explicitly public)
- [ ] Sensitive data (passwords, tokens, PII) MUST NOT appear in logs
- [ ] All secrets MUST come from environment variables, never hardcoded
- [ ] All file uploads MUST be validated for type and size
- [ ] All API responses MUST NOT expose internal error details to clients

_Additional project-specific constraints:_
- [ ] <add as needed>

## Operational Lifecycle
- What configuration might change after deployment? (URLs, credentials, thresholds)
- How will operators make those changes? (env var + restart, DB config, UI settings page)
- What monitoring confirms the feature is working? (logs, health endpoint, dashboard)

## Codebase Context (Feature Updates Only)
| Aspect | Details |
|--------|---------|
| Affected files | <file paths> |
| Related components | <component names> |
| Current behavior | <summary of existing behavior> |
| Desired change | <what should change> |
| Test coverage | <coverage % on affected files> |
| Architecture constraints | <relevant constraints> |
