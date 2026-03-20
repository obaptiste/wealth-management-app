# Next Steps

## Immediate next steps
- **task-002**: Define shared domain types — consolidate `portfolio.ts` / `portfolios.ts` duplicates, establish canonical location for all domain types
- **task-009**: Document verification commands (typecheck, lint, build) — unblocked after task-001

## What is blocked
- task-003 (sentiment service) — blocked on task-002 (shared types)
- task-004 (portfolio summary service) — blocked on task-002
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
