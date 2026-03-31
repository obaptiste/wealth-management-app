# Next Steps

## Immediate next steps

- Add scheduled and backfill snapshot capture (task-013): introduce a repeatable way to capture daily snapshots and backfill missing days
- Review the runtime auth flow end-to-end now that the compile/build contract is aligned with `/auth/token` and `/auth/me`
- Validate the watchlist and portfolio history flows in a live authenticated environment

## What is blocked

- Server-side dashboard loading remains blocked on the current browser-only token strategy in `frontend/src/lib/api.ts`
- Historical portfolio charts remain blocked until snapshot persistence exists; current price history writes are opportunistic and not sufficient for whole-portfolio reconstruction
- Backend test execution in this environment is still blocked by missing Python dependencies such as `python-jose`

## What needs review

- The frontend auth UX still needs a live runtime check because the client now stores tokens locally and the backend expects OAuth form login semantics
- The live `/watchlist` runtime contract should be exercised with real authenticated requests, especially add/remove flows and 401 handling
- Snapshot write timing needs a final product decision: scheduled daily job versus temporary snapshot-on-read fallback
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
