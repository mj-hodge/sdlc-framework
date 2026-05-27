# Phase 7 Agent: Frontend Testing Extension

> **Applies when the project has a frontend (React/TypeScript/Vite).** Skip this file for backend-only projects.
> This is an extension of `phase-7-test-design.md` — read that file first for the core testing philosophy and workflow.

---

## Frontend Testing Strategy: Playwright-First

**Playwright is the primary frontend test tool.** All tests that touch the DOM — components, forms, navigation, auth flows, error states — use Playwright against the running application. Vitest is reserved for pure logic only (utility functions, Zustand store state, Zod validators).

**Why:** Vitest + MSW + jsdom misses real browser bugs (rendering, interaction, navigation, network timing). Curl/HTTP-level tests miss UI-specific failures entirely. Playwright tests what the user actually experiences.

### When to Use What

| Tool | Use For | Examples |
|------|---------|---------|
| **Playwright** | Anything that renders UI or involves user interaction | Forms, auth flows, navigation, error states, loading states, protected routes, CRUD operations |
| **Vitest** | Pure logic with no DOM involvement | Utility functions, Zod schema validation, Zustand store state transitions, date formatters, math helpers |

**Rule of thumb:** If the test needs `screen`, `render`, `page`, or any DOM query — it's a Playwright test.

---

## Frontend Test Structure

```
e2e/
├── auth.spec.ts                    # Auth flows (login, register, logout)
├── dashboard.spec.ts               # Dashboard interactions
├── settings.spec.ts                # Settings/profile CRUD
├── navigation.spec.ts              # Route guards, redirects, deep links
└── fixtures/
    └── test-data.ts                # Shared test data factories
src/
├── lib/
│   ├── validators.ts
│   └── validators.test.ts          # Vitest — pure logic
├── stores/
│   ├── authStore.ts
│   └── authStore.test.ts           # Vitest — store state transitions
└── utils/
    ├── formatDate.ts
    └── formatDate.test.ts          # Vitest — pure function
```

**Key convention:** Playwright tests live in `e2e/` organized by feature. Vitest tests are co-located with source files, but only for pure logic.

---

## Playwright Infrastructure

### Config

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['html', { open: 'never' }]],  // Prevent auto-opening browser for report. Use `npx playwright show-report` manually.
  timeout: 15000,
  use: {
    headless: true,  // REQUIRED — always explicit, never rely on defaults. Never use --headed/--debug/--ui flags.
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

### Test Data Fixtures

```typescript
// e2e/fixtures/test-data.ts
export const testUser = {
  email: 'e2e-test@example.com',
  password: 'SecurePass123!',
  name: 'Test User',
}

export const invalidUser = {
  email: 'notanemail',
  password: 'short',
}
```

---

## Playwright Test Patterns

### Form Submission Tests

```typescript
import { test, expect } from '@playwright/test'
import { testUser } from './fixtures/test-data'

test.describe('Registration Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register')
  })

  test('submits form with valid data', async ({ page }) => {
    await page.getByLabel(/email/i).fill(testUser.email)
    await page.getByLabel(/password/i).fill(testUser.password)
    await page.getByRole('button', { name: /register/i }).click()

    await expect(page).toHaveURL('/login')
  })

  test('shows validation error for empty email', async ({ page }) => {
    await page.getByRole('button', { name: /register/i }).click()

    await expect(page.getByText(/email is required/i)).toBeVisible()
  })

  test('shows validation error for invalid email', async ({ page }) => {
    await page.getByLabel(/email/i).fill('notanemail')
    await page.getByRole('button', { name: /register/i }).click()

    await expect(page.getByText(/invalid email/i)).toBeVisible()
  })

  test('disables submit button while loading', async ({ page }) => {
    await page.getByLabel(/email/i).fill(testUser.email)
    await page.getByLabel(/password/i).fill(testUser.password)
    await page.getByRole('button', { name: /register/i }).click()

    await expect(page.getByRole('button', { name: /register/i })).toBeDisabled()
  })
})
```

### Auth Flow Tests

```typescript
test.describe('Authentication', () => {
  test('full login flow', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(testUser.email)
    await page.getByLabel(/password/i).fill(testUser.password)
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText(testUser.email)).toBeVisible()
  })

  test('shows error on wrong password', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(testUser.email)
    await page.getByLabel(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page.getByText(/invalid credentials/i)).toBeVisible()
  })

  test('logout clears session', async ({ page }) => {
    // Login first
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(testUser.email)
    await page.getByLabel(/password/i).fill(testUser.password)
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL('/dashboard')

    // Logout
    await page.getByRole('button', { name: /logout/i }).click()
    await expect(page).toHaveURL('/login')

    // Verify session cleared — can't access protected route
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/login')
  })
})
```

### Loading, Error, and Empty State Tests

Every page/component with async data MUST test all four states:

```typescript
test.describe('User List', () => {
  test('shows loading state', async ({ page }) => {
    await page.goto('/users')
    await expect(page.getByRole('status')).toBeVisible()
  })

  test('shows user data after load', async ({ page }) => {
    await page.goto('/users')
    await expect(page.getByText(testUser.email)).toBeVisible()
  })

  test('shows empty state when no users', async ({ page }) => {
    // Seed empty state via API or test fixtures
    await page.goto('/users')
    await expect(page.getByText(/no users found/i)).toBeVisible()
  })

  test('shows error message on server failure', async ({ page }) => {
    // Trigger server error (e.g., stop backend, or use route interception)
    await page.route('**/api/users', route =>
      route.fulfill({ status: 500, body: 'Internal Server Error' })
    )
    await page.goto('/users')
    await expect(page.getByText(/something went wrong/i)).toBeVisible()
  })
})
```

### Navigation & Route Guard Tests

```typescript
test.describe('Protected Routes', () => {
  test('redirects to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/login')
  })

  test('preserves deep link after login', async ({ page }) => {
    await page.goto('/settings/profile')
    await expect(page).toHaveURL(/login/)

    await page.getByLabel(/email/i).fill(testUser.email)
    await page.getByLabel(/password/i).fill(testUser.password)
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page).toHaveURL('/settings/profile')
  })

  test('public routes accessible without auth', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })
})
```

### API Error Interception

Use `page.route()` to simulate backend failures without modifying the server:

```typescript
test('shows error toast on save failure', async ({ page }) => {
  await page.route('**/api/settings', route =>
    route.fulfill({ status: 500, body: JSON.stringify({ error: 'DB error' }) })
  )

  await page.goto('/settings')
  await page.getByLabel(/name/i).fill('New Name')
  await page.getByRole('button', { name: /save/i }).click()

  await expect(page.getByText(/failed to save/i)).toBeVisible()
})
```

---

## Playwright Query Priority

Use accessible locators. This is **not optional** — it validates accessibility and produces stable selectors.

| Priority | Locator | When to Use |
|----------|---------|-------------|
| 1 | `getByRole` | Buttons, links, headings, form controls |
| 2 | `getByLabel` | Form inputs with labels |
| 3 | `getByPlaceholder` | Inputs without visible labels |
| 4 | `getByText` | Non-interactive text content |
| 5 | `getByTestId` | **Only when no accessible locator works** |

---

## Vitest (Pure Logic Only)

Vitest is ONLY for testing functions with no DOM involvement.

### Zustand Store Tests

```typescript
import { useAuthStore } from '@/stores/authStore'

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState(useAuthStore.getInitialState())
  })

  it('initializes with null user', () => {
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('sets user on setUser action', () => {
    useAuthStore.getState().setUser({ id: '1', email: 'test@example.com' })
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('clears user on logout', () => {
    useAuthStore.getState().setUser({ id: '1', email: 'test@example.com' })
    useAuthStore.getState().logout()
    expect(useAuthStore.getState().user).toBeNull()
  })
})
```

### Utility Function Tests

```typescript
import { formatDate } from '@/utils/formatDate'

describe('formatDate', () => {
  it('formats ISO date to readable string', () => {
    expect(formatDate('2026-01-15T00:00:00Z')).toBe('Jan 15, 2026')
  })

  it('returns empty string for null input', () => {
    expect(formatDate(null)).toBe('')
  })
})
```

### Zod Schema Tests

```typescript
import { loginSchema } from '@/lib/validators'

describe('loginSchema', () => {
  it('accepts valid credentials', () => {
    const result = loginSchema.safeParse({ email: 'test@example.com', password: 'pass123' })
    expect(result.success).toBe(true)
  })

  it('rejects invalid email', () => {
    const result = loginSchema.safeParse({ email: 'notanemail', password: 'pass123' })
    expect(result.success).toBe(false)
  })
})
```

---

## Defensive Gates (REQUIRED)

### Gate F1: Render State Tests (Playwright)

For **every page/component with async data**, require Playwright tests for all four states.

| State | Test Pattern |
|-------|-------------|
| Loading | Verify spinner/skeleton visible on initial load |
| Success | Verify data renders after load |
| Empty | Verify empty state message when no data |
| Error | Use `page.route()` to simulate 500, verify error UI |

**Checklist:**
- [ ] Every page with API calls has loading, success, empty, error tests
- [ ] Error tests use `page.route()` interception (not backend mocks)

### Gate F2: User Input Boundary Tests (Playwright)

For **every form**, require Playwright tests for boundary inputs.

| What to Test | Example |
|-------------|---------|
| Empty form submission | `test('shows required field errors on empty submit')` |
| Max length input | `test('truncates or rejects input beyond max length')` |
| Special characters | `test('accepts unicode in name field')` |
| XSS payload | `test('escapes HTML in user-provided text')` |

**Checklist:**
- [ ] Every required field tested with empty submission
- [ ] Every text input tested with max-length value
- [ ] Every user-displayed field tested with `<script>` payload

### Gate F3: Navigation & Auth Guard Tests (Playwright)

For **every protected route**, require Playwright tests for unauthenticated access.

| What to Test | Example |
|-------------|---------|
| Protected route redirects | `test('redirects to /login when not authenticated')` |
| Deep link preservation | `test('returns to original URL after login')` |
| 401 triggers re-auth | `test('redirects to login on 401 API response')` |

**Checklist:**
- [ ] Every protected route tested without auth
- [ ] Deep link preservation after redirect
- [ ] Token expiration → redirect

### Gate F4: CRUD Operation Tests (Playwright)

For **every CRUD feature**, test the full cycle through the UI.

| What to Test | Example |
|-------------|---------|
| Create via form | `test('creates item and shows in list')` |
| Read/display | `test('displays item details correctly')` |
| Update via form | `test('updates item and reflects changes')` |
| Delete with confirm | `test('deletes item after confirmation')` |

**Checklist:**
- [ ] Every create form tested end-to-end (fill → submit → verify in list)
- [ ] Every edit form tested (load existing → change → save → verify)
- [ ] Every delete action tested (click → confirm → verify removed)

---

## Frontend Anti-Patterns

| Anti-Pattern | What To Do Instead |
|--------------|---------------------|
| Testing frontend with curl/HTTP requests | Use Playwright — test what the user sees |
| Vitest + jsdom for component interaction tests | Use Playwright against the running app |
| MSW mocking as primary test strategy | Use `page.route()` for error simulation, test happy paths against real backend |
| `getByTestId` as default locator | Use `getByRole`, `getByLabel`, `getByText` first |
| Testing internal state (useState, store internals) | Test visible behavior through the UI |
| Snapshot tests | Test behavior; snapshots break on any markup change |
| Mocking child components | Run against the full app in Playwright |
| Skipping loading/error/empty states | Every async page must test all four states |
| Running Playwright with `--headed`, `--debug`, or `--ui` flags | Always run headless. These flags pop up browser windows and break CI/automated flows |
| Omitting `headless: true` from playwright.config.ts | Always set `headless: true` explicitly — never rely on Playwright defaults |

---

## Frontend LLM Error-Prone Areas

AI-generated frontend code has specific failure patterns. **Add these to every frontend test plan:**

| Error Category | Playwright Test |
|----------------|----------------|
| **Conditional rendering gaps** | Test loading/error/empty states via `page.route()` interception |
| **Event handler binding** | Click buttons, submit forms, verify correct action happened |
| **Async race conditions** | Navigate away quickly after triggering async action, verify no crash |
| **Form validation gaps** | Submit empty/invalid forms, verify all error messages appear |
| **Auth flow edge cases** | Expired token, concurrent sessions, logout during pending request |
| **Navigation bugs** | Back button behavior, deep links, browser refresh on protected routes |

---

## Frontend Checklist (verify before completing Phase 7)

- [ ] Playwright tests written for every user-facing page/feature
- [ ] Every form tested: valid submit, empty submit, invalid input, loading state
- [ ] Every protected route tested without auth
- [ ] Every async page tested for loading/success/empty/error states
- [ ] `page.route()` used for error simulation (not MSW)
- [ ] Vitest used ONLY for pure logic (no DOM, no rendering)
- [ ] No `getByTestId` without a comment explaining why accessible locators don't work
- [ ] `npx playwright test` runs — all tests FAIL (RED state)
- [ ] `vitest --run` runs — all pure logic tests FAIL (RED state)
- [ ] `playwright.config.ts` has explicit `headless: true` (not relying on defaults)
- [ ] No `--headed`, `--debug`, or `--ui` flags in any test scripts or package.json
