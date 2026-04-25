# Decisions

## [2026-04-25] Standardize the local agent harness around explicit JSON + script commands

**Context**
The repo had a partial harness (`agent-tools.sh`, memory, prompts, tasks), but it lacked consistent task fields, dedicated run logging scripts, and a strict review-gate oriented PR workflow.

**Decision**
Add/refresh a script-driven harness with:
- typed task metadata in `agent/tasks.json`,
- explicit next-task selection logic,
- run logging + memory update helpers,
- PR template + review gate guidance,
- root package scripts to run harness commands consistently.

**Rationale**
A uniform harness improves repeatability for both Codex and Claude while keeping humans in final control.

**Impact**
Agents can work semi-autonomously but must leave auditable artifacts (task status, run log, checks, memory updates) before review/merge.
