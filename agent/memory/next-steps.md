# Next Steps

## Immediate next steps
- **task-004**: Create portfolio summary service — now the highest-priority unblocked task
- **task-005**: Refactor dashboard data loading (still blocked by task-004)

## What is blocked
- task-005 (dashboard data loading) — blocked on task-004
- task-006 (sentiment trend chart adapter) — blocked on integrating normalized sentiment history into dashboard loaders

## What needs review
- AuthContext.tsx: calls `apiClient.get()` / `apiClient.post()` which are not exposed — needs fix before any auth-dependent page can work
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug
- `schemas.py`: `@validator` is Pydantic v1 syntax inside a v2 model — should migrate to `@field_validator`

## What can be deferred
- Watchlist domain (task-008): no backend support exists yet
- Historical snapshot plan (task-010): requires service layer first
- Full sentiment UI wiring: service exists now, but UI integration can follow portfolio service and data-loader work

## Updating this file
After each completed task, add:
- what should happen next
- what is blocked
- what needs review
- what can be deferred
