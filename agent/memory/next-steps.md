# Next Steps

## Immediate next steps

- Establish the historical snapshot plan so portfolio and sentiment charts can evolve beyond the current 7-day loader path
- Review the runtime auth flow end-to-end now that the compile/build contract is aligned with `/auth/token` and `/auth/me`
- Validate the watchlist flow in a live authenticated environment

## What is blocked

- Server-side dashboard loading remains blocked on the current browser-only token strategy in `frontend/src/lib/api.ts`
- Backend test execution in this environment is still blocked by missing Python dependencies such as `python-jose`

## What needs review

- The frontend auth UX still needs a live runtime check because the client now stores tokens locally and the backend expects OAuth form login semantics
- The live `/watchlist` runtime contract should be exercised with real authenticated requests, especially add/remove flows and 401 handling
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug

## What can be deferred

- Historical snapshot plan (task-010): requires service layer first
- Broader dashboard analytics beyond the current summary cards and sentiment trend chart

## Updating this file

After each completed task, add:

- what should happen next
- what is blocked
- what needs review
- what can be deferred
