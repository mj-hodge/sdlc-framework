````markdown
# Architecture

## Research Findings

**Stack:** FastAPI, PostgreSQL, SQLAlchemy 2.0, React

**Current Best Practices Applied:**
- FastAPI dependency injection for clean testing (source: FastAPI docs)
- SQLAlchemy 2.0 with async sessions (source: SQLAlchemy docs)
- Pydantic v2 for validation and serialization (source: Pydantic docs)
- Repository pattern optional with SQLAlchemy 2.0 — using direct session injection

**Development Accelerators:**
- SQLModel for combined Pydantic + SQLAlchemy models (reduces boilerplate)
- FastAPI automatic OpenAPI docs
- Alembic autogenerate for migrations

**Anti-Patterns Avoided:**
- No microservices — single deployable with module separation
- No over-abstraction — using FastAPI patterns directly

---

## Domain Structure

```
app/
├── auth/           # Authentication domain
│   ├── router.py   # API endpoints
│   ├── service.py  # Business logic
│   ├── models.py   # SQLAlchemy models
│   ├── schemas.py  # Pydantic schemas
│   └── dependencies.py
├── users/          # User profile domain
│   ├── router.py
│   ├── service.py
│   ├── models.py
│   └── schemas.py
├── core/           # Shared infrastructure
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   └── exceptions.py
└── main.py
```

## Domain Boundaries

| Domain | Responsibility | Owns |
|--------|----------------|------|
| auth | Authentication, sessions, tokens | Session data, tokens |
| users | User profiles, preferences | User profile data |
| core | Shared infrastructure | Config, DB connection, security utils |

## Interfaces

| From | To | Interface |
|------|-----|-----------|
| auth | users | `get_user_by_email(email) -> User` |
| users | auth | None (users doesn't call auth) |

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Modular monolith | Single deployment, clear modules, no network overhead |
| SQLAlchemy 2.0 async | Current best practice, matches FastAPI async |
| JWT in httpOnly cookie | More secure than localStorage |
| No repository pattern | SQLAlchemy session injection is sufficient |

---

## Database Schema

### users table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | ON UPDATE now() |

### sessions table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| token_hash | VARCHAR(255) | NOT NULL |
| expires_at | TIMESTAMP | NOT NULL |
| created_at | TIMESTAMP | DEFAULT now() |

**Indexes:**
- users.email (unique)
- sessions.user_id
- sessions.expires_at (for cleanup)

---

## API Design

### POST /auth/register
```
Request:
{
  "email": "user@example.com",
  "password": "securepassword"
}

Response (201):
{
  "id": "uuid",
  "email": "user@example.com"
}

Errors:
- 409:
  `{ "type": "/problems/conflict", "title": "Conflict", "status": 409, "detail": "Email already exists" }`
- 422:
  `{ "type": "/problems/validation-error", "title": "Validation Error", "status": 422, "detail": "..." }`
```

### POST /auth/login
```
Request:
{
  "email": "user@example.com",
  "password": "securepassword"
}

Response (200):
{
  "message": "Login successful"
}
+ Set-Cookie: session=<token>; HttpOnly; Secure

Errors:
- 401:
  `{ "type": "/problems/authentication-error", "title": "Authentication Error", "status": 401, "detail": "Invalid credentials" }`
- 422:
  `{ "type": "/problems/validation-error", "title": "Validation Error", "status": 422, "detail": "..." }`
```

### POST /auth/logout
```
Response (200):
{
  "message": "Logged out"
}
+ Clear-Cookie: session
```

### GET /users/me
```
Response (200):
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}

Errors:
- 401:
  `{ "type": "/problems/authentication-error", "title": "Authentication Error", "status": 401, "detail": "Not authenticated" }`
```

---

## Implementation Plan

### Phase 1: Core Setup (Day 1)
- [ ] Project structure
- [ ] Database connection
- [ ] Alembic migrations setup
- [ ] Base models and schemas

### Phase 2: Auth Domain (Days 2-3)
- [ ] User model and migrations
- [ ] Registration endpoint
- [ ] Password hashing
- [ ] Login endpoint
- [ ] JWT/session handling
- [ ] Logout endpoint

### Phase 3: User Domain (Day 4)
- [ ] User profile endpoint
- [ ] Auth dependency for protected routes

### Phase 4: Integration (Day 5)
- [ ] End-to-end testing
- [ ] Error handling polish
- [ ] Documentation

---

Ready for approval to proceed to Test Design.
````
