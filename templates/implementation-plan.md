# Implementation Plan

## Build Order

| # | Component | Dependencies | Story |
|---|-----------|-------------|-------|
| 1 | <component> | — | <story> |
| 2 | <component> | 1 | <story> |

## Milestones

| Milestone | Components | Stories | Criteria |
|-----------|-----------|---------|----------|
| M1: <name> | 1, 2 | <stories> | <what "done" looks like> |
| M2: <name> | 3, 4 | <stories> | <what "done" looks like> |

## File Ownership Matrix

> **Required for:** Large scope with 3+ stories when `orchestration.parallel_stories: true`
>
> Maps each story to the files it owns. Used by parallel Phase 8 to ensure worktree agents don't conflict.
>
> **Rules:**
> - No two stories may share files in the "Modifies" column
> - Files that multiple stories need (main.py, conftest.py, migrations) go in the Shared Files table below
> - Each story's worktree agent is restricted to files listed in its row
> - Interface Contracts define the public API each story exposes — verified at merge time

| Story | Creates | Modifies | Tests | Interface Contracts |
|-------|---------|----------|-------|---------------------|
| <story-1> | `app/auth/router.py`, `app/auth/service.py` | `app/core/config.py` | `tests/unit/test_auth.py` | `AuthService.authenticate(email, password) -> User` |
| <story-2> | `app/users/router.py`, `app/users/service.py` | — | `tests/unit/test_users.py` | `UserService.get_by_id(id) -> User` |
| <story-3> | `app/items/router.py`, `app/items/service.py` | — | `tests/unit/test_items.py` | `ItemService.list_by_user(user_id) -> list[Item]` |

## Shared Files (Integration Pass)

> Files listed here are NOT modified by individual worktree agents. They are handled during the merge integration step after all stories complete.

| File | Purpose | Stories That Need It |
|------|---------|---------------------|
| `app/main.py` | Router registration | All |
| `tests/conftest.py` | Shared fixtures | All |
| `alembic/versions/` | Migrations | All with DB changes |

## Shared File Integration Plan

> **Required.** Defines the exact changes each story needs in shared files. The merge step follows this plan — no ad-hoc edits.

### `app/main.py`

Each story adds one router registration line. Merge step appends all in build order:

```python
# Story 1: Auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])
# Story 2: Users
app.include_router(users.router, prefix="/users", tags=["users"])
# Story 3: Items
app.include_router(items.router, prefix="/items", tags=["items"])
```

### `tests/conftest.py`

Each story may need shared fixtures. List per-story fixture additions:

| Story | Fixtures Added | Dependencies |
|-------|---------------|-------------|
| <story-1> | `authenticated_client`, `test_user` | `db_session` |
| <story-2> | `user_factory` | `db_session` |
| <story-3> | `item_factory` | `db_session`, `test_user` |

### `alembic/versions/`

Migrations are generated during merge step only. Order:

1. <story-1> tables (e.g., `users`, `sessions`)
2. <story-2> tables (e.g., `profiles`) — FK to `users`
3. <story-3> tables (e.g., `items`) — FK to `users`
