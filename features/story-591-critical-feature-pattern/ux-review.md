# UX Review — STORY-591: Critical-Feature SDLC Pattern

**Reviewer:** Phase 6c UX Review
**Date:** 2026-04-25
**Story:** STORY-591
**Surfaces reviewed:** `/status` HTML page, `docs/critical-features.md` index, output-contracts template, criticality classification field

---

## 1. User Journey Analysis

### On-Call Operator (Primary — Incident Response)

**Goal:** Determine which critical features are unhealthy and find the runbook within 30 seconds of receiving a page.

**Journey:**
1. Receive alert → navigate to `/status` URL (likely bookmarked or in runbook header)
2. Scan table for red/yellow rows — unhealthy features are sorted first (correct)
3. Read `Last Success` timestamp to gauge severity and duration
4. Click `Runbook` link and begin remediation

**Assessment:** Journey is well-supported. The sort-unhealthy-first rule eliminates scanning time in multi-feature tables. The 30s auto-refresh prevents stale reads during active incidents. No auth wall removes friction on the critical path.

**Gap:** If the operator reaches `/status` and the endpoint itself has errored (503 → degraded fallback), there is no visual cue distinguishing "degraded because status check failed" from "degraded because a feature is degraded." The operator may open the wrong runbook.

### CTO / Mark (Secondary — Coverage Confidence)

**Goal:** Grep or scan `docs/critical-features.md` to confirm coverage before a board-level review or post-incident.

**Journey:**
1. Open `docs/critical-features.md` in GitHub or terminal
2. Scan the table for any blank `Last Verified` cells or missing runbook links
3. Confirm every row has a `Tests` directory link

**Assessment:** The table structure is appropriate for grep and terminal reading. `Last Verified` is the most important column for Mark's purpose — a date that is >30 days old is an immediate red flag.

**Gap:** There is no explicit staleness threshold defined. Without a convention (e.g., "> 30 days = stale"), Mark cannot tell whether a 45-day-old entry is acceptable or concerning.

### AI Agent / SDLC Persona (Consumer — Phase 1 Classification)

**Goal:** Set `criticality` field correctly during Phase 1 seed; know when to trigger enhanced path.

**Journey:**
1. Read BA persona instructions in `agents/phase-1-seed.md`
2. Evaluate feature against the three-tier classification table
3. Set field value; if `critical`, write justification for any deviation from the must-classify list
4. Follow enhanced phase path (Phase 10c injection)

**Assessment:** Classification criteria table is clear and unambiguous. The must-classify list (external APIs, time-window ops, financial data, healthz, integrity ops) covers all known failure categories. The one-line justification rule is a good forcing function.

**Gap:** AI agents consume templates by pattern-matching. The `criticality` field in `templates/seed.md` needs the valid values (`routine|important|critical`) inline — an agent that reads only the template file (not the spec) may omit the field or misspell a value.

### Engineering Team (Producer — Writing Output Contracts)

**Goal:** Fill in `output-contracts.md` for a new critical feature with accurate, testable contracts.

**Journey:**
1. Copy `templates/output-contracts.md` into `features/<story>/`
2. Read Overview table, fill in feature name/story/owner
3. Read Contracts table header, write C1 through Cn
4. Struggle with: what counts as a "good" assertion vs. "bad" one
5. Reference the worked examples (C1–C4) from the spec

**Assessment:** The template is functional but the worked examples live in `specification.md`, not in the template file itself. Engineers filling out the template for the first time will not see the good/bad examples unless they navigate to the spec.

**Gap:** The template file needs at least one inline worked example (commented or in a `<!-- EXAMPLE -->` block) so the pattern is self-contained for engineers who clone the template without reading the full spec.

---

## 2. `/status` HTML Page Review

### Layout and Readability

- Monospace font (`font-family: monospace`) is appropriate for a data-dense operations dashboard. Consistent character widths make columns easy to read.
- Table width is 100% — correct for varying screen widths.
- Five columns (Feature, Health, Last Success, Violations 24h, Runbook) is the right density: enough signal, not overcrowded.
- `Last updated` timestamp and auto-refresh notice below the heading gives operators situational awareness immediately.

**Issue:** Health column shows raw enum values (`healthy`, `degraded`, `unhealthy`). Under stress, color alone conveys status, but the text value provides no additional scannable signal compared to a symbol prefix (e.g., `✓ healthy`, `⚠ degraded`, `✗ unhealthy`). Symbols would survive color-blind and grayscale contexts better.

### Accessibility

- **Color contrast — healthy:** Background `#d4edda` (light green) with black text. Contrast ratio ~8:1. Passes WCAG AA.
- **Color contrast — degraded:** Background `#fff3cd` (light yellow) with black text. Contrast ratio ~1.4:1 against the yellow. **FAILS WCAG AA** (requires 4.5:1 for normal text). The yellow background is visually distinct but technically low-contrast.
- **Color contrast — unhealthy:** Background `#f8d7da` (light red) with black text. Contrast ratio ~4.6:1. Borderline WCAG AA.
- **Color-blind (red-green deficiency):** Red and green rows are visually indistinguishable for users with deuteranopia/protanopia. Status text (`healthy`/`unhealthy`) partially compensates, but a symbol or shape cue is needed.
- **Screen readers:** No `aria-label` on the table, no `scope` attributes on `<th>` elements. These are missing for full screen reader support.
- **Keyboard navigation:** Runbook links are keyboard-reachable as standard `<a>` tags. No issues.

### Mobile

- `width: 100%; border-collapse: collapse` renders acceptably on mobile.
- `padding: 8px` is adequate touch target spacing for cells, though the `Runbook` link target area is small.
- No viewport meta tag in the spec HTML. Without `<meta name="viewport" content="width=device-width, initial-scale=1">`, the page will render at desktop scale on mobile Safari/Chrome.
- Long feature names or runbook URLs may cause horizontal scroll on narrow screens. Feature names should be tested at 320px width.

### No-JS / No-CDN

- `<meta http-equiv="refresh">` for auto-refresh is correct — works without JavaScript.
- Inline CSS only. No CDN dependencies. Correct and intentional.
- Works in Lynx and other text-mode browsers. Appropriate for ops contexts.

---

## 3. Index Document Review (`docs/critical-features.md`)

### Discoverability

- File lives at `docs/critical-features.md` — a conventional location that Mark can find without guidance.
- Phase 11 CI gate verifies the file exists — prevents accidental deletion.
- Requirement that `README.md` links to it ensures it appears in GitHub's rendered landing page.

### Column Completeness

| Column | Assessment |
|--------|------------|
| Feature | Clear |
| Status | URL to `/api/status#<slug>` — fragment links require anchor IDs in the HTML page. The spec does not define anchor IDs on table rows. This link may not work. |
| Contracts count | Useful signal; easy to compute |
| Tests | Directory path — grepable and linkable |
| Dashboard | Grafana link — may be internal/VPN-only; not useful during external incidents |
| Runbook | Must be a public or VPN-accessible URL; same concern |
| Last Verified | Most important column for staleness detection; no staleness threshold defined |

### Staleness Indicators

No policy exists for when `Last Verified` becomes a warning. Recommendation: define 30 days as the staleness threshold and add a note to the template header. Without this, the column is informational but not actionable.

### Grepability

The table structure is grep-friendly. `grep "unhealthy\|degraded" docs/critical-features.md` would not return status because the Status column contains a URL, not a health value. This is a deliberate choice (live status comes from the endpoint), but Mark should be told the column is a link, not a live value.

---

## 4. Template Usability Review (Output Contracts)

### Cognitive Load Assessment

| Task | Load | Notes |
|------|------|-------|
| Filling Overview table | Low | Four fields, all obvious |
| Writing Assertion column | High | Business-level language is unfamiliar to engineers used to writing test assertions |
| Writing Degraded Behavior | High | Requires reasoning about partial-failure modes, not just happy paths |
| Choosing Blocking: true/false | Medium | The default-false-during-adoption rule is buried in the spec, not in the template |
| Filling Test File | Low | Just a path |
| Filling Metric | Medium | Engineers may not know the naming convention without referencing the spec |

### Template Self-Containment Gaps

1. The template contains no inline examples — all examples are in `specification.md`.
2. The "GOOD/BAD" assertion examples are in the spec but not near the template fields where they are needed at write time.
3. The Blocking field default (`false` during adoption) is not stated in the template.
4. The metric naming convention (`<feature>_<contract>_violation_total`) is not stated in the template.

### Recommendation

Add a collapsible `<!-- EXAMPLE: remove before committing -->` section at the bottom of the template with one complete worked row. This cuts the engineering feedback loop from "read spec → understand → write" to "copy example → modify → validate."

---

## 5. Friction Points

| ID | Surface | Friction | Severity |
|----|---------|----------|----------|
| F1 | `/status` HTML | No viewport meta tag — broken on mobile | Medium |
| F2 | `/status` HTML | Yellow (#fff3cd) fails WCAG AA contrast | Medium |
| F3 | `/status` HTML | Color-only health coding fails for red-green color blindness | High |
| F4 | `/status` HTML | No distinction between "status endpoint errored" and "feature degraded" | High |
| F5 | Index MD | Fragment link `#<slug>` requires HTML anchors not yet defined | Medium |
| F6 | Index MD | No staleness threshold for `Last Verified` column | Low |
| F7 | Template | No inline examples — engineers must cross-reference spec | High |
| F8 | Template | Blocking default and metric naming convention missing from template | Medium |
| F9 | `seed.md` template | Valid criticality values not visible inline | Medium |
| F10 | `/status` HTML | Runbook column shows only generic "Runbook" link text — not scannable by feature name | Low |

---

## 6. Required UX Tests (Phase 7)

1. **Color-blind simulation:** Render `/status` with a red-green color blindness filter (e.g., Coblis or browser DevTools). Verify unhealthy rows are distinguishable from healthy rows without color.
2. **WCAG contrast check:** Run the degraded row (`#fff3cd`) through a contrast checker. Verify remediated color meets 4.5:1 ratio.
3. **Mobile render at 320px:** Load `/status` in Chrome DevTools mobile simulation at 320px width. Verify no horizontal scroll and all five columns are readable.
4. **No-viewport render:** Load `/status` without the viewport meta tag on an iPhone. Verify the experience is still usable.
5. **Viewport meta tag addition:** Add the tag and re-test mobile render.
6. **Status endpoint error simulation:** Configure the status backend to return a read failure. Verify the HTML page shows a visually distinct "status check failed" state, not a standard "degraded" row.
7. **Grep test for Mark's workflow:** Run `grep` patterns against a populated `docs/critical-features.md`. Verify all critical columns are grep-findable.
8. **Template self-completion test:** Have an engineer unfamiliar with the spec fill out `output-contracts.md` using only the template file. Record where they get stuck. Threshold: zero lookups to the spec required for a first contract.
9. **Fragment link test:** Verify that `Status` column links in `docs/critical-features.md` resolve to the correct anchored position in the rendered HTML `/status` page.
10. **Auto-refresh under incident load:** Simulate 20 concurrent `/status` page loads at 30s refresh intervals. Verify response time stays under 2s (p95).

---

## 7. Recommendations Table

| ID | Priority | Finding | Recommendation |
|----|----------|---------|----------------|
| R1 | Critical | Red-green color blindness: status indistinguishable without color | Add a symbol prefix to the Health cell: `✓` (healthy), `⚠` (degraded), `✗` (unhealthy) alongside the text value |
| R2 | Critical | No visual distinction between "status endpoint errored" and "feature degraded" | Add a dedicated `status-error` CSS class with a distinct style (e.g., striped background or orange) and a note cell: "Status check failed — health unknown" |
| R3 | High | Yellow background (#fff3cd) fails WCAG AA contrast | Change degraded background to `#e6a817` text-on-white, or use `#ffc107` with black text — test to 4.5:1 minimum |
| R4 | High | Template has no inline examples — forces spec cross-reference | Add one worked row in a comment block at the bottom of `templates/output-contracts.md` |
| R5 | High | Blocking field default and metric naming convention missing from template | Add a "Field Reference" section inside the template with default values and naming convention |
| R6 | Medium | No viewport meta tag in HTML spec | Add `<meta name="viewport" content="width=device-width, initial-scale=1">` to the `<head>` block |
| R7 | Medium | Fragment links in index (`/api/status#<slug>`) require anchor IDs not yet defined | Define `id="<slug>"` on each `<tr>` in the HTML template, or use query-param links (`/status?feature=<slug>`) |
| R8 | Medium | `criticality` valid values not visible in `templates/seed.md` | Add inline comment: `<!-- values: routine | important | critical -->` next to the field |
| R9 | Low | No staleness threshold for `Last Verified` in index | Define 30-day staleness policy in the template header comment and in Phase 10c verification checklist |
| R10 | Low | Runbook link text is generic ("Runbook") across all rows | Use feature-name in link text: `<a href="{url}">{feature-name} Runbook</a>` for screen reader and tab-navigation clarity |

---

## 8. Sign-off

**Overall assessment:** The pattern is operationally sound. The `/status` page prioritizes the on-call use case correctly (sort unhealthy first, no auth, no JS, auto-refresh). The index document serves Mark's coverage-check use case. The output contracts template captures the right fields.

**Blockers before Phase 7:**
- R1 (color-blind status coding) — must be resolved in the HTML spec before test design
- R2 (status endpoint error vs. feature degraded) — must be resolved in the API design before implementation
- R4 (no inline template examples) — must be resolved in `templates/output-contracts.md` before Phase 7 test for template usability

**Non-blocking (can be addressed in Phase 9):** R3, R5, R6, R7, R8, R9, R10.

**Approved to proceed to Phase 7** contingent on resolution of R1, R2, R4.
