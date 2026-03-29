# Wealth App Project Instructions

## Project purpose

This project is a wealth management app focused on portfolio visibility, sentiment-informed analysis, watchlists, and clear data visualization.

## Primary stack

- Next.js
- TypeScript
- React
- PostgreSQL
- FastAPI
- SQLAlchemy
- Alembic

## Working principles

- Prefer small, safe, incremental changes
- Keep code readable and well-commented
- Avoid unnecessary abstraction
- Preserve existing architecture unless the task explicitly requires change
- Do not modify unrelated files
- Do not silently change data contracts
- If database schema changes, document the migration impact
- If API shapes change, update all dependent types and consumers
- Prefer server-safe patterns and predictable data flow
- Surface risks clearly instead of hiding uncertainty

## Agent workflow

- Read `CLAUDE.md` before starting work
- Read these context files before substantial implementation:
  - `agent/memory/project-summary.md`
  - `agent/memory/architecture.md`
  - `agent/memory/current-state.md`
  - `agent/memory/decisions.md`
  - `agent/memory/next-steps.md`
  - `agent/tasks.json`
- Complete only one task at a time unless the user explicitly changes scope
- Default to the highest-priority unblocked task in `agent/tasks.json` unless the user asks for a different task
- Before coding, state:
  - task selected
  - understanding
  - files to inspect
  - files to change
  - plan
  - risks or assumptions
- After implementation, update the relevant memory files and task status when the work changes project state
- Keep memory updates concrete:
  - `agent/memory/current-state.md` for what is true now
  - `agent/memory/decisions.md` for important implementation choices or trade-offs
  - `agent/memory/next-steps.md` for follow-up work
  - `agent/tasks.json` for task state, dependencies, or new tasks

## Standard commands

### Agent helper commands

- `source agent/agent-tools.sh && agent-check`
- `source agent/agent-tools.sh && agent-context`
- `source agent/agent-tools.sh && agent-status`
- `source agent/agent-tools.sh && agent-next`
- `source agent/agent-tools.sh && agent-blocked`
- `source agent/agent-tools.sh && agent-start`
- `source agent/agent-tools.sh && agent-review`
- `source agent/agent-tools.sh && agent-plan`
- `source agent/agent-tools.sh && agent-log`
- `source agent/agent-tools.sh && agent-done task-<id>`
- `source agent/agent-tools.sh && agent-in-progress task-<id>`

### Frontend commands

- `cd frontend && npm run dev`
- `cd frontend && npm run build`
- `cd frontend && npm run lint`

### Backend commands

- `cd backend && python3 -m uvicorn main:app --reload`
- `cd backend && pytest`
- `cd backend && python3 -m pytest tests/test_main.py`
- `cd backend && alembic upgrade head`

### Verification guidance

- Prefer the smallest relevant verification set for the files you changed
- For frontend-only changes, run at least the relevant `frontend` checks
- For backend-only changes, run at least the relevant `backend` tests
- For cross-cutting changes, run both frontend and backend verification where applicable
- If a command cannot run because of missing dependencies, environment variables, or services, say so explicitly

## Definition of done

A task is only complete when:

1. The requested behavior is implemented
2. Types are consistent
3. Relevant build or verification steps have been run
4. Important edge cases are noted
5. Relevant files in `agent/memory/` and `agent/tasks.json` are updated when project state changed
6. Next steps are suggested if work remains

## Coding style

- Use explicit TypeScript types where they improve clarity
- Keep functions small and focused
- Prefer descriptive names over clever names
- Add comments where intent may not be obvious
- Reuse existing utilities before introducing new ones

## Guardrails

- Do not invent market or portfolio data
- Do not fake successful API responses
- Do not mark tasks done without verification
- Do not perform broad refactors while completing a narrow task
