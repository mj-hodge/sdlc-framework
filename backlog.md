# Backlog

Synced from Asana: 2026-04-25

## In Progress

### [STORY-591] Critical-Feature SDLC Pattern
**As a** engineering team using the SDLC framework **I want** a generic critical-feature pattern with output contracts, hardened tests, deploy gates, and monitoring templates **so that** features with material business impact are systematically protected across all Gorilla Commerce projects.

| Field | Value |
|-------|-------|
| Scope | Large |
| Criticality | Critical |
| Phase | 1 - Seed (complete) |
| Branch | story-591/story-591 |

**Acceptance Criteria:**
- [ ] SC-1: Seed template includes `criticality: routine|important|critical` field
- [ ] SC-2: `output-contracts.md` template exists for critical stories
- [ ] SC-3: Phase 10c (Output Contract Hardening) fires for all scopes when critical
- [ ] SC-4: Phase 7 requires `tests/critical_features/` directory for critical features
- [ ] SC-5: Phase 10 requires business-level output contracts with violation events
- [ ] SC-6: Phase 11 includes deploy-blocking `Critical Feature Contracts` CI step
- [ ] SC-7: Generic `/api/status` JSON + `/status` HTML pattern documented
- [ ] SC-8: Grafana dashboard template documented
- [ ] SC-9: `docs/critical-features.md` single index requirement documented
- [ ] SC-10: Pattern doc + AGENTS.md section + persona updates
- [ ] SC-11: Zero behavior change in advertising-amazon
- [ ] SC-12: Missing contract infrastructure fails deploy closed

---

## Ready

---

## Backlog

---

*0 tasks parked in Do Not Do*
