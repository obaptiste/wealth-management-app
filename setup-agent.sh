#!/usr/bin/env bash

set -euo pipefail

mkdir -p agent/memory
mkdir -p agent/prompts

cat > CLAUDE.md <<'EOF'
# Wealth App Project Instructions

## Project purpose
This project is a wealth management app focused on portfolio visibility, sentiment-informed analysis, watchlists, and clear data visualization.

## Primary stack
- Next.js
- TypeScript
- React
- PostgreSQL
- Prisma

## Working principles
- Prefer small, safe, incremental changes
- Keep code readable and well-commented
- Avoid unnecessary abstraction
- Preserve existing architecture unless the task explicitly requires change
- Do not modify unrelated files
- Do not silently change data contracts
- If Prisma schema changes, document the migration impact
- If API shapes change, update all dependent types and consumers
- Prefer server-safe patterns and predictable data flow
- Surface risks clearly instead of hiding uncertainty

## Definition of done
A task is only complete when:
1. The requested behavior is implemented
2. Types are consistent
3. Relevant build or verification steps have been run
4. Important edge cases are noted
5. Memory files are updated
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
EOF

cat > agent/memory/project-summary.md <<'EOF'
# Project Summary

## Project
Wealth management app

## Purpose
Build a practical wealth dashboard that helps users understand their holdings, track portfolio changes, monitor sentiment signals, and make more informed decisions.

## Core outcomes
- View portfolio holdings clearly
- Track watchlist assets
- Ingest or mock market/sentiment data safely
- Visualize trends and changes over time
- Surface notable signals, catalysts, and risk markers
- Create an architecture that can grow without turning into spaghetti

## Constraints
- Must remain readable and maintainable
- Must work cleanly with Next.js and TypeScript
- Must avoid breaking existing dashboard or auth flows
- Must keep data contracts explicit
- Must be deployable with a realistic modern web workflow

## What good looks like
A stable app with:
- clean data flow
- clear UI
- reliable typing
- modular services
- isolated business logic
- charts and dashboard summaries that are easy to interpret
EOF

cat > agent/memory/architecture.md <<'EOF'
# Architecture

## Current architectural intent
The app should separate concerns into the following layers:

### 1. Data access layer
Responsible for fetching external or internal data.
Examples:
- market data providers
- sentiment data providers
- database queries

### 2. Service layer
Responsible for normalizing, transforming, and combining data.
Examples:
- sentiment scoring services
- portfolio summary calculations
- watchlist signal generation

### 3. Application layer
Responsible for orchestrating what the UI needs.
Examples:
- dashboard loaders
- server actions
- route-level data composition

### 4. Presentation layer
Responsible for rendering data cleanly.
Examples:
- cards
- tables
- charts
- alerts
- watchlist panels

## Rules
- Keep external API logic out of UI components
- Keep transformation logic out of page files where possible
- Prefer one source of truth for each major domain concept
- Reuse shared types where practical
- Make it easy to replace mock data with real data later

## Candidate domains
- portfolio
- holdings
- watchlist
- sentiment
- market data
- alerts
- historical snapshots
EOF

cat > agent/memory/current-state.md <<'EOF'
# Current State

## Status
Early-to-mid build stage.

## Known direction
The app is intended to combine portfolio visibility with sentiment-aware analysis and dashboard-style data visualization.

## Current assumptions
- Some frontend/dashboard work already exists or is in progress
- Backend and integration work may still be partial
- Sentiment logic exists in some form but likely needs hardening
- Data contracts may still need normalization and cleanup

## Likely priorities
1. Establish reliable service boundaries
2. Normalize market and sentiment data
3. Make dashboard data loading predictable
4. Add visualizations for time-based changes
5. Reduce build and integration fragility

## Known risks
- Inconsistent API response shapes
- Leaky business logic in UI
- Tight coupling between components and data fetching
- Incomplete schema or migration discipline
- Build failures caused by scattered assumptions
EOF

cat > agent/memory/decisions.md <<'EOF'
# Decisions

## Initial decisions
- The project will use a task-driven agent workflow
- The agent should complete one task at a time
- The agent must update memory after each meaningful task
- The service layer should hold transformation and normalization logic
- UI components should receive already-shaped data where possible
- Verification matters more than confident prose

## Decision log format
Use this format for future entries:

### [YYYY-MM-DD] Decision title
Context:
What problem or question led to this decision?

Decision:
What was chosen?

Reason:
Why was this the best option?

Impact:
What files, flows, or future work does this affect?
EOF

cat > agent/memory/next-steps.md <<'EOF'
# Next Steps

## Immediate next steps
- Define first implementation-ready tasks
- Confirm service boundaries for sentiment and portfolio logic
- Build a clean starting sequence for dashboard data flow
- Add safe verification habits to every task cycle

## Updating this file
After each completed task, add:
- what should happen next
- what is blocked
- what needs review
- what can be deferred
EOF

cat > agent/tasks.json <<'EOF'
[
  {
    "id": "task-001",
    "title": "Audit current app structure",
    "description": "Inspect the codebase and identify where portfolio logic, sentiment logic, data fetching, and dashboard rendering currently live.",
    "priority": "high",
    "status": "todo",
    "dependsOn": [],
    "acceptanceCriteria": [
      "Relevant folders and files are identified",
      "Current data flow is summarized",
      "Risks or messy boundaries are documented in current-state.md"
    ]
  },
  {
    "id": "task-002",
    "title": "Define shared domain types",
    "description": "Create or consolidate TypeScript types for holdings, watchlist items, sentiment results, portfolio summaries, and historical snapshots.",
    "priority": "high",
    "status": "todo",
    "dependsOn": ["task-001"],
    "acceptanceCriteria": [
      "Shared types exist in a clear location",
      "Major domain objects have explicit types",
      "Existing consumers compile against the updated types"
    ]
  },
  {
    "id": "task-003",
    "title": "Create sentiment service module",
    "description": "Implement a service that accepts raw sentiment inputs and returns normalized sentiment data for the rest of the app.",
    "priority": "high",
    "status": "todo",
    "dependsOn": ["task-002"],
    "acceptanceCriteria": [
      "Service file exists",
      "Normalization rules are explicit",
      "Output type is stable and documented",
      "No UI component performs raw sentiment normalization"
    ]
  },
  {
    "id": "task-004",
    "title": "Create portfolio summary service",
    "description": "Implement a service that calculates total value, allocation summaries, and simple gain/loss metrics from portfolio data.",
    "priority": "high",
    "status": "todo",
    "dependsOn": ["task-002"],
    "acceptanceCriteria": [
      "Summary calculations are isolated from UI",
      "Output types are predictable",
      "Edge cases for missing or partial data are handled"
    ]
  },
  {
    "id": "task-005",
    "title": "Refactor dashboard data loading",
    "description": "Move dashboard-level data orchestration into a dedicated loader or server-side composition layer.",
    "priority": "high",
    "status": "todo",
    "dependsOn": ["task-003", "task-004"],
    "acceptanceCriteria": [
      "Dashboard page no longer contains scattered business logic",
      "Loader composes sentiment and portfolio data cleanly",
      "Data dependencies are easier to understand"
    ]
  },
  {
    "id": "task-006",
    "title": "Build sentiment trend chart input adapter",
    "description": "Create an adapter that converts sentiment history into chart-friendly data structures.",
    "priority": "medium",
    "status": "todo",
    "dependsOn": ["task-003"],
    "acceptanceCriteria": [
      "Chart data mapping is isolated",
      "Adapter handles empty or incomplete history safely",
      "Presentation components receive ready-to-render data"
    ]
  },
  {
    "id": "task-007",
    "title": "Build portfolio summary cards",
    "description": "Create UI cards for total portfolio value, allocation highlights, and top-level movement metrics.",
    "priority": "medium",
    "status": "todo",
    "dependsOn": ["task-004", "task-005"],
    "acceptanceCriteria": [
      "Cards render from typed summary data",
      "No calculation logic is embedded in card components",
      "Loading and empty states are sensible"
    ]
  },
  {
    "id": "task-008",
    "title": "Add watchlist signal panel",
    "description": "Create a panel that shows selected watchlist assets with sentiment or catalyst-related indicators.",
    "priority": "medium",
    "status": "todo",
    "dependsOn": ["task-003", "task-005"],
    "acceptanceCriteria": [
      "Watchlist panel uses normalized data",
      "Signal logic is not hardcoded into presentation components",
      "Panel can tolerate incomplete upstream data"
    ]
  },
  {
    "id": "task-009",
    "title": "Add verification commands and documentation",
    "description": "Document the commands used to typecheck, lint, build, and test the app or relevant modules.",
    "priority": "medium",
    "status": "todo",
    "dependsOn": ["task-001"],
    "acceptanceCriteria": [
      "Verification commands are documented",
      "Agent can report what checks should run after each task",
      "Known command failures are noted if they exist"
    ]
  },
  {
    "id": "task-010",
    "title": "Establish historical snapshot plan",
    "description": "Define how the app should store or simulate historical portfolio and sentiment snapshots for charting and comparisons.",
    "priority": "medium",
    "status": "todo",
    "dependsOn": ["task-003", "task-004"],
    "acceptanceCriteria": [
      "Snapshot model is described",
      "Storage direction is documented",
      "Trade-offs between mock and persistent history are explained"
    ]
  }
]
EOF

cat > agent/prompts/worker.md <<'EOF'
# Worker Prompt

You are the implementation agent for this project.

Your job is to complete exactly one task at a time, with minimal risk and maximum clarity.

## Required reading
Read these files before doing any work:
- CLAUDE.md
- agent/memory/project-summary.md
- agent/memory/architecture.md
- agent/memory/current-state.md
- agent/memory/decisions.md
- agent/memory/next-steps.md
- agent/tasks.json

## Rules
- Complete only the highest-priority unblocked task unless explicitly told otherwise
- Do not change unrelated files
- Prefer the smallest safe implementation that satisfies the task
- Do not silently invent requirements
- Do not claim success without verification
- Keep business logic out of UI where practical
- Preserve readability and existing patterns unless there is a strong reason not to
- Note uncertainty clearly

## Workflow
1. Identify the highest-priority unblocked task
2. Summarize your understanding of the task
3. List the files you expect to inspect or change
4. Write a short implementation plan of 4 to 7 steps
5. Identify risks or assumptions
6. Implement the task
7. Run or describe relevant verification steps
8. Summarize exactly what changed
9. Propose updates for:
   - agent/memory/current-state.md
   - agent/memory/decisions.md
   - agent/memory/next-steps.md
   - agent/tasks.json

## Output format
Use this exact structure:

### Task selected
...

### Understanding
...

### Files to inspect
...

### Files to change
...

### Plan
1. ...
2. ...
3. ...

### Risks / assumptions
- ...
- ...

### Implementation summary
...

### Verification
- Command:
- Result:

### Memory updates
#### current-state.md
...

#### decisions.md
...

#### next-steps.md
...

#### tasks.json
...
EOF

cat > agent/prompts/reviewer.md <<'EOF'
# Reviewer Prompt

You are the review agent.

Your job is to review the completed task with precision, scepticism, and respect for project constraints.

## Required reading
Read:
- CLAUDE.md
- agent/memory/project-summary.md
- agent/memory/architecture.md
- agent/memory/current-state.md
- agent/memory/decisions.md
- agent/tasks.json

Also inspect:
- the task that was marked complete
- the changed files
- any reported verification output

## Review goals
Determine whether the implementation is:
- correct
- scoped appropriately
- safe
- understandable
- consistent with project architecture

## Check for
- The task requirements were actually satisfied
- Unrelated files were not changed without justification
- Type or contract risks were introduced
- Business logic leaked into UI unnecessarily
- Edge cases were ignored
- Verification was weak, skipped, or misleading
- Memory and task tracking were properly updated

## Output format
Use this exact structure:

### What is correct
- ...

### What is risky
- ...

### Missing or weak verification
- ...

### Scope concerns
- ...

### Required fixes before acceptance
- ...

### Verdict
pass / revise
EOF

cat > agent/prompts/planner.md <<'EOF'
# Planner Prompt

You are the planning agent.

Your job is to convert project goals or feature requests into small, implementation-ready tasks.

## Planning rules
- Break work into tasks that can be completed independently where possible
- Avoid vague tasks like "improve dashboard"
- Prefer tasks that produce observable outputs
- Include dependencies clearly
- Keep tasks narrow enough that they can be reviewed properly
- Highlight risks where architecture is uncertain

## Output format
Return a JSON array of task objects with:
- id
- title
- description
- priority
- status
- dependsOn
- acceptanceCriteria

## Quality bar
A good task:
- has one clear goal
- affects a coherent area of the codebase
- can be verified
- does not hide multiple major features inside one title
EOF

cat > agent/README.md <<'EOF'
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
EOF

echo "Agent scaffold created."
echo "Next step: open agent/README.md and paste the suggested first-run prompt into Claude Code or Codex."