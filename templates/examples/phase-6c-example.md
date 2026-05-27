```markdown
# UX Review

## User Profile

| Attribute | Value |
|-----------|-------|
| Primary user | Property manager, 10-50 units |
| Technical level | Moderate — comfortable with web apps, not technical |
| Usage frequency | Daily, 30-60 min sessions |
| Context | Multitasking, often on phone or tablet |
| Top tasks | 1. Review maintenance requests, 2. Message tenants, 3. Check occupancy |

---

## Flow Analysis

### Flow: Review and respond to maintenance request

| Step | Action | Friction | Notes |
|------|--------|----------|-------|
| 1 | Click "Maintenance" in nav | 1 | Clear navigation |
| 2 | Scan list for new requests | 2 | List needs sort-by-priority default |
| 3 | Click request to view | 1 | Good — opens detail view |
| 4 | Read request details | 2 | Photos inline, but missing tenant history |
| 5 | Click "Respond" button | 1 | Clear CTA |
| 6 | Type response | 1 | Good |
| 7 | Select status change | 2 | Dropdown with 8 options — too many for common use |
| 8 | Click "Send" | 1 | Good |

**Total friction:** 11/8 = 1.4 avg — **PASS**

**Improvements:**
- Step 2: Default sort by priority + date, not alphabetical
- Step 4: Add tenant history sidebar (previous requests, lease info)
- Step 7: Show top 3 statuses as buttons, "More..." for the rest

### Flow: Create new property listing

| Step | Action | Friction | Notes |
|------|--------|----------|-------|
| 1 | Click "Properties" in nav | 1 | Clear |
| 2 | Click "Add Property" | 1 | Clear |
| 3 | Fill address fields (5 fields) | 3 | Could auto-complete from address lookup |
| 4 | Fill property details (12 fields) | 4 | Too many required fields for initial creation |
| 5 | Upload photos (separate page) | 3 | Should be same page, drag-and-drop |
| 6 | Set pricing (separate page) | 2 | Could be on main form |
| 7 | Review and publish | 2 | Good summary |
| 8 | Click "Publish" | 1 | Clear |

**Total friction:** 17/8 = 2.1 avg — **NEEDS WORK**

**Improvements:**
- Step 3: Address autocomplete (Google Places API) — reduce to 1 field + confirm
- Step 4: Only require address + type + bedrooms for initial creation. Rest optional
- Step 5-6: Merge into single page with sections
- Estimated improvement: 17 → 10 friction (1.25 avg)

---

## Consistency Findings

### High: Inconsistent Primary Action Placement

| Aspect | Detail |
|--------|--------|
| Severity | High |
| Pattern | Primary action button position |
| Deviation | "Save" is bottom-right on property form, bottom-left on tenant form, top-right on maintenance |
| Impact | Users hunt for the action button on every screen |
| Fix | Primary action always bottom-right of form, aligned with form fields |

### Medium: Mixed Terminology

| Aspect | Detail |
|--------|--------|
| Severity | Medium |
| Pattern | Referring to tenants |
| Deviation | "Tenant" on dashboard, "Renter" on lease page, "Resident" on messaging |
| Impact | Users unsure if these mean the same thing |
| Fix | Use "Tenant" everywhere — it's the most common term in the industry |

### Medium: Inconsistent Empty States

| Aspect | Detail |
|--------|--------|
| Severity | Medium |
| Pattern | What users see when there's no data |
| Deviation | Properties shows helpful "Add your first property" CTA. Maintenance shows blank white page. Messages shows "No data" |
| Impact | Blank pages confuse new users and feel broken |
| Fix | Every empty state: illustration + explanation + CTA to create first item |

---

## Design System Gaps

| Token | Status | Recommendation |
|-------|--------|----------------|
| Color palette | Defined | OK — primary, secondary, success, error present |
| Typography scale | Partially defined | Missing caption and overline sizes |
| Spacing scale | Not defined | Define 4px base: 4, 8, 12, 16, 24, 32, 48 |
| Border radius | Inconsistent | Standardize: 4px (inputs), 8px (cards), 16px (modals) |
| Shadow scale | Not defined | Define: sm (cards), md (dropdowns), lg (modals) |

---

## Verdict

**CHANGES REQUIRED**

**Critical/High issues (fix before Phase 7):**
1. Standardize primary action placement (bottom-right, all forms)
2. Simplify property creation flow (single page, fewer required fields)

**Medium issues (add to implementation plan):**
- Consistent terminology ("Tenant" everywhere)
- Empty states for all list views
- Address autocomplete for property creation

**Low issues (polish later):**
- Define spacing and shadow design tokens
- Add hover previews for tenant/property links

Once primary action placement and property flow are updated, proceed to Test Design.
```
