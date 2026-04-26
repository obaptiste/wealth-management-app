# Architecture

## System layout
- `frontend/`: Next.js App Router app, typed services and components.
- `backend/`: FastAPI API + SQLAlchemy models/migrations.
- `agent/`: local AI harness (memory, prompts, tasks, run logs).

## Runtime boundaries
1. **Backend data and domain logic**
   - Auth, portfolio CRUD, sentiment routes, snapshot jobs.
   - SQLAlchemy models + Alembic migrations.
2. **Frontend data access and shaping**
   - `src/lib/api.ts` as typed HTTP client.
   - `src/services/*` normalize/compose data for UI.
3. **Frontend presentation**
   - App Router pages + reusable components.
   - UI should render pre-shaped data; avoid heavy business logic in components.

## Design rules
- Keep data contracts stable and explicit (backend schemas + frontend types).
- Degrade safely when optional endpoints are unavailable.
- Prefer deterministic, testable utility/service functions.
- Keep task execution and project memory auditable under `agent/`.
