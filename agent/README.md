# Agent Scaffold

This folder contains the memory, task queue, and prompt files for a supervised agent workflow.

## Suggested first run

Use this prompt in Claude Code or Codex:

Read these files first:

- CLAUDE.md
- agent/memory/project-summary.md
- agent/memory/architecture.md
- agent/memory/current-state.md
- agent/memory/decisions.md
- agent/memory/next-steps.md
- agent/tasks.json
- agent/prompts/worker.md

Then act as the implementation agent described in agent/prompts/worker.md.

Start with task-001 unless there is a clearly higher-priority unblocked task.
Do not code immediately.
First produce:

1. task selected
2. understanding
3. files to inspect
4. files to change
5. plan
6. risks / assumptions
