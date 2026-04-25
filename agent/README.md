# Agent Harness (Local, Review-First)

This harness provides a **controlled, semi-autonomous workflow** for AI agents (Codex/Claude) and humans to collaborate safely on this repo.

## Goals
- Maintain persistent project context (`agent/memory/*`).
- Track task backlog with explicit metadata (`agent/tasks.json`).
- Work **one task at a time** with clear acceptance criteria.
- Require checks, logs, and human review before merge.

## Directory structure

```txt
agent/
  memory/
    project-summary.md
    architecture.md
    current-state.md
    decisions.md
    known-issues.md
    next-steps.md
  prompts/
    planner.md
    worker.md
    reviewer.md
    pr-writer.md
  logs/
    .gitkeep
  runs/
    .gitkeep
  tasks.json
  agent-config.json
  README.md
```

## Root scripts
Run from repo root:

- `npm run agent:health` — validate harness structure + task schema.
- `npm run agent:plan` — print task plan grouped by status.
- `npm run agent:next` — output highest-priority unblocked safest task.
- `npm run agent:log -- <task-id> <note>` — append run note.
- `npm run agent:update-memory -- "<summary>"` — append update to `current-state.md`.

Quality scripts:
- `npm run lint`
- `npm run test`
- `npm run check`
- `npm run fix`
- `npm run format`

## Human review gate (required)
Before merge:
1. Confirm a valid task ID is referenced in PR.
2. Confirm checks run are listed with honest outcomes.
3. Review risk and rollback notes.
4. Confirm memory/task files were updated if project state changed.
5. Approve manually (no auto-merge from agent workflow).

## Suggested daily workflow
1. `npm run agent:health`
2. `npm run agent:next`
3. `npm run agent:log -- <task-id> "starting"`
4. Implement only the selected task.
5. Run checks (`npm run lint` + targeted tests).
6. Update memory/tasks.
7. `npm run agent:log -- <task-id> "completed checks"`
8. Prepare PR using `.github/pull_request_template.md`.
9. Human reviews and decides merge.

## Optional external AI integration
No external API is required for this harness.

If future automation is added, keep it optional and environment-based (for example):
- `OPENAI_API_KEY` (optional)
- `ANTHROPIC_API_KEY` (optional)

Never commit real keys. Use `.env` locally only.
