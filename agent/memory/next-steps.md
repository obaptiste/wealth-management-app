# Next Steps

## Immediate next steps
- Introduce a watchlist-oriented summary surface once the watchlist domain exists
- Review the runtime auth flow end-to-end now that the compile/build contract is aligned with `/auth/token` and `/auth/me`
- Establish the historical snapshot plan so portfolio and sentiment charts can evolve beyond the current 7-day loader path

## What is blocked
- Server-side dashboard loading remains blocked on the current browser-only token strategy in `frontend/src/lib/api.ts`

## What needs review
- The frontend auth UX still needs a live runtime check because the client now stores tokens locally and the backend expects OAuth form login semantics
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug
- `schemas.py`: `@validator` is Pydantic v1 syntax inside a v2 model — should migrate to `@field_validator`

## What can be deferred
- Watchlist domain (task-008): no backend support exists yet
- Historical snapshot plan (task-010): requires service layer first
- Broader dashboard analytics beyond the current summary cards and sentiment trend chart

## Updating this file
After each completed task, add:
- what should happen next
- what is blocked
- what needs review
- what can be deferred
