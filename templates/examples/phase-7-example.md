````markdown
# Test Plan

## Overview

Based on: Auth feature design (Phase 6) + Security review (Phase 6b)
Scope: Medium
Coverage target: 60%

## Test Structure

```
tests/
├── unit/
│   └── test_auth_service.py      # Business logic
├── integration/
│   └── test_auth_api.py          # API endpoints
└── conftest.py                    # Shared fixtures
```

## Shared Fixtures (conftest.py)

```python
@pytest.fixture
def test_user():
    """Create a test user for auth tests.

    Returns a user dict with known credentials for testing.
    Password is 'testpass123' before hashing.
    """
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "hashed_password": hash_password("testpass123")
    }

@pytest.fixture
def authenticated_client(client, test_user):
    """Client with valid auth token.

    Use this when testing endpoints that require authentication.
    """
    # Login and attach token to client
    response = client.post("/auth/login", json={
        "email": test_user["email"],
        "password": "testpass123"
    })
    token = response.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

---

## Unit Tests: Auth Service

Location: `tests/unit/test_auth_service.py`

### `test_hash_password_returns_different_value_than_input`

**Verifies:** Password hashing doesn't store plaintext

**Why this matters:** Security fundamental - passwords must never be stored as-is

**Arrange:**
- Plain password string: "mysecurepassword"

**Act:**
- Call `hash_password("mysecurepassword")`

**Assert:**
- Result is not equal to "mysecurepassword"
- Result is a string of expected hash length

**Implementation notes:**
- Use bcrypt; result should start with "$2b$"

---

### `test_verify_password_returns_true_for_correct_password`

**Verifies:** Correct password passes verification

**Arrange:**
- Hash a known password: `hashed = hash_password("correct")`

**Act:**
- Call `verify_password("correct", hashed)`

**Assert:**
- Returns `True`

---

### `test_verify_password_returns_false_for_wrong_password`

**Verifies:** Wrong password fails verification

**Arrange:**
- Hash a known password: `hashed = hash_password("correct")`

**Act:**
- Call `verify_password("wrong", hashed)`

**Assert:**
- Returns `False`

---

## Integration Tests: Auth API

Location: `tests/integration/test_auth_api.py`

### `test_register_with_valid_data_creates_user`

**Verifies:** Registration endpoint creates new user

**Why this matters:** Core registration flow must work

**Arrange:**
- Prepare valid registration data:
  ```json
  {"email": "new@example.com", "password": "securepass123"}
  ```

**Act:**
- POST `/auth/register` with the data

**Assert:**
- Response status: 201
- Response contains user ID
- Response contains email (not password)
- User exists in database

---

### `test_register_with_existing_email_returns_409`

**Verifies:** Duplicate email rejected

**Why this matters:** Prevents duplicate accounts

**Arrange:**
- Create existing user with email "exists@example.com"
- Prepare registration with same email

**Act:**
- POST `/auth/register` with duplicate email

**Assert:**
- Response status: 409 (Conflict)
- Error message mentions email already exists

---

### `test_register_with_invalid_email_returns_400`

**Verifies:** Email validation works

**Arrange:**
- Prepare data with invalid email: `{"email": "notanemail", "password": "test123"}`

**Act:**
- POST `/auth/register`

**Assert:**
- Response status: 400
- Error message mentions invalid email

---

### `test_login_with_valid_credentials_returns_token`

**Verifies:** Successful login returns auth token

**Why this matters:** Core authentication flow

**Arrange:**
- Create test user with known credentials
- Prepare login data matching those credentials

**Act:**
- POST `/auth/login`

**Assert:**
- Response status: 200
- Response contains token
- Token is valid JWT format

---

### `test_login_with_wrong_password_returns_401`

**Verifies:** Wrong password rejected

**Arrange:**
- Create test user
- Prepare login with wrong password

**Act:**
- POST `/auth/login`

**Assert:**
- Response status: 401
- Generic error message (don't reveal if email exists)

---

### `test_login_with_nonexistent_email_returns_401`

**Verifies:** Unknown email rejected (same response as wrong password)

**Why this matters:** Security - don't reveal which emails exist

**Arrange:**
- Prepare login with email that doesn't exist

**Act:**
- POST `/auth/login`

**Assert:**
- Response status: 401
- Same error message as wrong password (prevents enumeration)

---

### `test_get_current_user_with_valid_token_returns_user`

**Verifies:** Authenticated endpoint returns user data

**Arrange:**
- Use `authenticated_client` fixture

**Act:**
- GET `/users/me`

**Assert:**
- Response status: 200
- Response contains email
- Response does NOT contain password or hash

---

### `test_get_current_user_without_token_returns_401`

**Verifies:** Protected endpoint rejects unauthenticated requests

**Arrange:**
- Use regular client (no auth)

**Act:**
- GET `/users/me`

**Assert:**
- Response status: 401

---

### `test_logout_clears_session`

**Verifies:** Logout invalidates the session

**Arrange:**
- Use `authenticated_client` fixture
- Verify can access protected endpoint

**Act:**
- POST `/auth/logout`

**Assert:**
- Response status: 200
- Subsequent request to `/users/me` returns 401

---

## Security Tests (from Security Review)

### `test_login_rate_limited_after_5_attempts`

**Verifies:** Brute force protection (from security requirement M1)

**Arrange:**
- Create test user

**Act:**
- Send 6 login requests with wrong password in quick succession

**Assert:**
- First 5 return 401
- 6th returns 429 (Too Many Requests)

---

### `test_password_not_in_response`

**Verifies:** Password/hash never returned

**Arrange:**
- Create user, login

**Act:**
- GET `/users/me`

**Assert:**
- Response does not contain "password" key
- Response does not contain "hashed_password" key

---

## Coverage Summary

| Component | Tests | Target Coverage |
|-----------|-------|-----------------|
| Auth service (unit) | 3 | 80% |
| Auth API (integration) | 10 | 70% |
| Security (integration) | 2 | N/A (critical paths) |

Total: 15 tests

---

Ready for Phase 8 - Implementation can begin with TDD workflow.
````
