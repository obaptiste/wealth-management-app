# Next Steps

## Immediate
1. Use `npm run agent:next` and begin with the highest-priority unblocked task.
2. For each task, create a run record (`npm run agent:log -- ...`) before coding.
3. Run lint/test checks after each change and capture results in the run log + PR body.

## Near-term
- Add/expand tests for the highest-risk backend and frontend integration paths.
- Tighten CI so PRs fail fast on lint/type/test regressions.
- Remove or quarantine stale/generated artifacts that are not source-of-truth.

## Human review reminders
- Confirm task acceptance criteria are truly met, not just code-complete.
- Verify rollback notes and operational risk statements on every PR.
