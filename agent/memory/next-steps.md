# Next Steps

## Immediate next steps
- **task-007**: Extract the dashboard stats into reusable typed cards if they need to be shared outside the dashboard page
- Build a sentiment chart component that consumes `SentimentChartPoint[]` from the dashboard loader
- Review the runtime auth flow end-to-end now that the compile/build contract is aligned with `/auth/token` and `/auth/me`

## What is blocked
- Server-side dashboard loading remains blocked on the current browser-only token strategy in `frontend/src/lib/api.ts`

## What needs review
- The frontend auth UX still needs a live runtime check because the client now stores tokens locally and the backend expects OAuth form login semantics
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug
- `schemas.py`: `@validator` is Pydantic v1 syntax inside a v2 model — should migrate to `@field_validator`

## What can be deferred
- Watchlist domain (task-008): no backend support exists yet
- Historical snapshot plan (task-010): requires service layer first
- Full sentiment UI wiring beyond the dashboard summary signal: the chart adapter exists now, but a chart component can follow when the dashboard layout is ready

## Updating this file
After each completed task, add:
- what should happen next
- what is blocked
- what needs review
- what can be deferred
