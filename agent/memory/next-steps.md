# Next Steps

## Immediate next steps
- **task-003**: Create sentiment service module — now unblocked by type consolidation
- **task-004**: Create portfolio summary service — now unblocked by canonical shared domain types
- **task-009**: Document verification commands (typecheck, lint, build)

## What is blocked
- task-005 (dashboard data loading) — blocked on task-003 and task-004

## What needs review
- AuthContext.tsx: calls `apiClient.get()` / `apiClient.post()` which are not exposed — needs fix before any auth-dependent page can work
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug
- `schemas.py`: `@validator` is Pydantic v1 syntax inside a v2 model — should migrate to `@field_validator`

## What can be deferred
- Watchlist domain (task-008): no backend support exists yet
- Historical snapshot plan (task-010): requires service layer first
- Sentiment trend chart (task-006): requires sentiment service (task-003) first

## Updating this file
After each completed task, add:
- what should happen next
- what is blocked
- what needs review
- what can be deferred
