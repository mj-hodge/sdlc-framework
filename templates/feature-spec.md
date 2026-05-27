# Feature Specification

## Overview
| Field | Value |
|-------|-------|
| Feature | <name> |
| Scope | Medium |
| Story | [STORY-XXX](https://app.asana.com/...) |
| Affected Components | <list> |

## Requirements
- <requirement 1>
- <requirement 2>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Codebase Context
| Aspect | Details |
|--------|---------|
| Affected files | <file paths> |
| Current behavior | <summary> |
| Test coverage | <% on affected files> |

## Component Boundaries (REQUIRED for Medium)

_Define which modules/components are involved and their responsibilities:_

| Component | Responsibility | Changes Required |
|-----------|---------------|-----------------|
| <component> | <what it does> | <what changes> |

## API Changes (if applicable)

| Endpoint | Method | Change Type | Request Shape | Response Shape |
|----------|--------|-------------|---------------|----------------|
| /api/... | POST | New | `{ field: type }` | `{ field: type }` |

_Include error responses:_

_All error responses follow [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) Problem Details format._

| Status | Condition | Response |
|--------|-----------|----------|
| 400 | Invalid input | `{ "type": "/problems/validation-error", "title": "Validation Error", "status": 400, "detail": "..." }` |
| 401 | Not authenticated | `{ "type": "/problems/authentication-error", "title": "Authentication Error", "status": 401, "detail": "..." }` |

## Database Changes (if applicable)

| Table | Change | Migration Required |
|-------|--------|-------------------|
| ... | ... | Yes/No |

_Include index changes and data migration needs._

## Error Handling Strategy (REQUIRED for Medium)

| Error Scenario | Handling | User-Facing Message |
|----------------|----------|---------------------|
| <scenario> | <how handled> | <what user sees> |

## Integration Points

| System | Direction | Protocol | Auth |
|--------|-----------|----------|------|
| <system> | inbound/outbound | REST/gRPC/etc | <method> |

## Security Constraints
_Carried forward from seed.md. Add feature-specific constraints:_
- [ ] <constraint from seed.md>
- [ ] <feature-specific constraint>

## Performance Considerations
_Carried forward from seed.md performance requirements:_
- Expected query patterns and counts
- Caching strategy (if applicable)
- Payload size expectations

## Constraints
- <constraint 1>

## Out of Scope
- <exclusion 1>

## Medium Scope Completeness Checklist

_All items must be checked before Phase 7:_
- [ ] Component boundaries defined
- [ ] API request/response shapes specified (if API changes)
- [ ] Database changes documented with migration needs (if DB changes)
- [ ] Error handling strategy for each failure scenario
- [ ] Security constraints from seed.md carried forward
- [ ] Integration points identified
- [ ] Out of scope clearly defined
