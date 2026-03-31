# Next Steps

## Immediate next steps

- Review the runtime auth flow end-to-end now that the compile/build contract is aligned with `/auth/token` and `/auth/me`
- Exercise the snapshot job path in a real environment with one dedicated scheduler process
- Validate the watchlist and portfolio history flows in a live authenticated environment

## What is blocked

- Server-side dashboard loading remains blocked on the current browser-only token strategy in `frontend/src/lib/api.ts`
- Backend test execution in this environment is still blocked by missing Python dependencies such as `python-jose`

## What needs review

- The frontend auth UX still needs a live runtime check because the client now stores tokens locally and the backend expects OAuth form login semantics
- The live `/watchlist` runtime contract should be exercised with real authenticated requests, especially add/remove flows and 401 handling
- Snapshot capture timing should be validated against product expectations now that the scheduler defaults to 22:00 UTC via environment configuration
- The optional dedicated scheduler process needs deployment-level wiring in the real environment
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug

## What can be deferred

- Broader dashboard analytics beyond the current summary cards and sentiment trend chart
- Persisted sentiment daily summaries can be deferred until raw `SentimentResult` aggregation becomes a performance problem

## Updating this file

After each completed task, add:

- what should happen next
- what is blocked
- what needs review
- what can be deferred
