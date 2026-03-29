# Next Steps

## Immediate next steps

- Merge and validate the backend watchlist branch against the new dashboard watchlist panel
- Build the watchlist frontend: add `getWatchlist()`, `addToWatchlist()`, `removeFromWatchlist()` to `frontend/src/lib/api.ts`; add a `/watchlist` page that calls those methods
- Review the runtime auth flow end-to-end now that the compile/build contract is aligned with `/auth/token` and `/auth/me`
- Establish the historical snapshot plan so portfolio and sentiment charts can evolve beyond the current 7-day loader path

## What is blocked

- Server-side dashboard loading remains blocked on the current browser-only token strategy in `frontend/src/lib/api.ts`
- Live watchlist population is blocked on the backend watchlist ORM/schema/endpoint branch not being present in this branch yet

## What needs review

- The frontend auth UX still needs a live runtime check because the client now stores tokens locally and the backend expects OAuth form login semantics
- The exact `/watchlist` response shape should be verified once the backend branch merges, especially any embedded sentiment fields
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug
- `schemas.py`: `@validator` is Pydantic v1 syntax inside a v2 model — should migrate to `@field_validator`

## What can be deferred

- Historical snapshot plan (task-010): requires service layer first
- Broader dashboard analytics beyond the current summary cards and sentiment trend chart

## Updating this file

After each completed task, add:

- what should happen next
- what is blocked
- what needs review
- what can be deferred
