# Next Steps

## Immediate next steps
- Fix existing frontend type/lint issues in `AuthContext.tsx`, `portfolio/[id]/page.tsx`, and `pension/page.tsx` so the frontend can pass a full `tsc --noEmit`
- **task-006**: Build a sentiment trend chart adapter that can consume `sentiment/history` responses for dashboard and watchlist visuals
- **task-007**: Extract the dashboard stats into reusable typed cards if they need to be shared outside the dashboard page

## What is blocked
- Server-side dashboard loading remains blocked on the current browser-only token strategy in `frontend/src/lib/api.ts`

## What needs review
- AuthContext.tsx: calls `apiClient.get()` / `apiClient.post()` which are not exposed — needs fix before any auth-dependent page can work
- `portfolio/[id]/page.tsx`: still imports `* as api` and calls `.get()` directly instead of using named `apiClient` methods
- `config.py`: `is_production` is a method but used as a property in `main.py` — potential runtime bug
- `schemas.py`: `@validator` is Pydantic v1 syntax inside a v2 model — should migrate to `@field_validator`
- `pension/page.tsx`: pension calculation requests still use snake_case keys that do not match the frontend client method signature
- Frontend verification failures remain in `pension/page.tsx`, `portfolio/[id]/page.tsx`, and `AuthContext.tsx`

## What can be deferred
- Watchlist domain (task-008): no backend support exists yet
- Historical snapshot plan (task-010): requires service layer first
- Full sentiment UI wiring beyond the dashboard summary signal: task-006 can add chart-ready history shaping later

## Updating this file
After each completed task, add:
- what should happen next
- what is blocked
- what needs review
- what can be deferred
