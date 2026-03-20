#!/usr/bin/env zsh

set -euo pipefail

# -----------------------------
# basic paths
# -----------------------------
export AGENT_DIR="${AGENT_DIR:-agent}"
export AGENT_MEMORY_DIR="$AGENT_DIR/memory"
export AGENT_PROMPTS_DIR="$AGENT_DIR/prompts"
export AGENT_TASKS_FILE="$AGENT_DIR/tasks.json"
export AGENT_LOG_DIR="$AGENT_DIR/logs"

mkdir -p "$AGENT_LOG_DIR"

# -----------------------------
# helpers
# -----------------------------
agent-root() {
  git rev-parse --show-toplevel 2>/dev/null || pwd
}

agent-check() {
  local missing=0

  for file in \
    "CLAUDE.md" \
    "$AGENT_MEMORY_DIR/project-summary.md" \
    "$AGENT_MEMORY_DIR/architecture.md" \
    "$AGENT_MEMORY_DIR/current-state.md" \
    "$AGENT_MEMORY_DIR/decisions.md" \
    "$AGENT_MEMORY_DIR/next-steps.md" \
    "$AGENT_TASKS_FILE" \
    "$AGENT_PROMPTS_DIR/worker.md" \
    "$AGENT_PROMPTS_DIR/reviewer.md" \
    "$AGENT_PROMPTS_DIR/planner.md"
  do
    if [[ ! -f "$file" ]]; then
      echo "Missing: $file"
      missing=1
    fi
  done

  if [[ "$missing" -eq 0 ]]; then
    echo "Agent scaffold looks complete."
  else
    echo "Agent scaffold is incomplete."
    return 1
  fi
}

agent-status() {
  echo "Repo root: $(agent-root)"
  echo
  echo "Tasks file: $AGENT_TASKS_FILE"
  echo

  if [[ -f "$AGENT_TASKS_FILE" ]]; then
    echo "Task summary:"
    python3 - <<'PY'
import json
from collections import Counter

with open("agent/tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

status_counts = Counter(task.get("status", "unknown") for task in tasks)
priority_counts = Counter(task.get("priority", "unknown") for task in tasks)

print("By status:")
for k, v in sorted(status_counts.items()):
    print(f"  {k}: {v}")

print("\nBy priority:")
for k, v in sorted(priority_counts.items()):
    print(f"  {k}: {v}")

print("\nOpen tasks:")
for task in tasks:
    if task.get("status") != "done":
        deps = ", ".join(task.get("dependsOn", [])) or "none"
        print(f"- {task['id']} | {task['priority']} | {task['status']} | deps: {deps} | {task['title']}")
PY
  else
    echo "No tasks.json found."
  fi
}

agent-next() {
  if [[ ! -f "$AGENT_TASKS_FILE" ]]; then
    echo "Missing $AGENT_TASKS_FILE"
    return 1
  fi

  python3 - <<'PY'
import json

with open("agent/tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

done_ids = {t["id"] for t in tasks if t.get("status") == "done"}
priority_order = {"high": 0, "medium": 1, "low": 2}

unblocked = []
for task in tasks:
    if task.get("status") == "done":
        continue
    deps = task.get("dependsOn", [])
    if all(dep in done_ids for dep in deps):
        unblocked.append(task)

unblocked.sort(key=lambda t: (priority_order.get(t.get("priority", "low"), 99), t["id"]))

if not unblocked:
    print("No unblocked tasks found.")
else:
    t = unblocked[0]
    print(f"{t['id']}: {t['title']}")
    print(f"Priority: {t.get('priority')}")
    print(f"Status: {t.get('status')}")
    print(f"Description: {t.get('description')}")
PY
}

agent-start() {
  cat <<'EOF'
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

Complete only the highest-priority unblocked task.
Do not code immediately.

First produce:
1. task selected
2. understanding
3. files to inspect
4. files to change
5. plan
6. risks / assumptions
EOF
}

agent-review() {
  cat <<'EOF'
Read these files first:
- CLAUDE.md
- agent/memory/project-summary.md
- agent/memory/architecture.md
- agent/memory/current-state.md
- agent/memory/decisions.md
- agent/tasks.json
- agent/prompts/reviewer.md

Then act as the review agent described in agent/prompts/reviewer.md.

Review the most recent completed implementation.
Be sceptical and precise.

Output:
1. what is correct
2. what is risky
3. missing or weak verification
4. scope concerns
5. required fixes before acceptance
6. verdict
EOF
}

agent-plan() {
  cat <<'EOF'
Read these files first:
- CLAUDE.md
- agent/memory/project-summary.md
- agent/memory/architecture.md
- agent/memory/current-state.md
- agent/memory/decisions.md
- agent/tasks.json
- agent/prompts/planner.md

Then act as the planning agent described in agent/prompts/planner.md.

Take the next feature idea and break it into small implementation-ready tasks.
Return only JSON.
EOF
}

agent-log() {
  local stamp
  stamp="$(date +"%Y-%m-%d_%H-%M-%S")"
  local file="$AGENT_LOG_DIR/session_$stamp.md"

  cat > "$file" <<EOF
# Agent Session Log

Date: $(date)
Repo: $(agent-root)

## Current next task
$(agent-next 2>/dev/null || true)

## Notes
- 

## Outcome
- 

## Follow-up
- 
EOF

  echo "Created log: $file"
}

agent-done() {
  local task_id="${1:-}"
  if [[ -z "$task_id" ]]; then
    echo "Usage: agent-done task-001"
    return 1
  fi

  python3 - "$task_id" <<'PY'
import json
import sys

task_id = sys.argv[1]
path = "agent/tasks.json"

with open(path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

found = False
for task in tasks:
    if task.get("id") == task_id:
        task["status"] = "done"
        found = True
        break

if not found:
    print(f"Task not found: {task_id}")
    sys.exit(1)

with open(path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)
    f.write("\n")

print(f"Marked {task_id} as done.")
PY
}

agent-in-progress() {
  local task_id="${1:-}"
  if [[ -z "$task_id" ]]; then
    echo "Usage: agent-in-progress task-001"
    return 1
  fi

  python3 - "$task_id" <<'PY'
import json
import sys

task_id = sys.argv[1]
path = "agent/tasks.json"

with open(path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

found = False
for task in tasks:
    if task.get("id") == task_id:
        task["status"] = "in_progress"
        found = True
        break

if not found:
    print(f"Task not found: {task_id}")
    sys.exit(1)

with open(path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)
    f.write("\n")

print(f"Marked {task_id} as in_progress.")
PY
}

agent-help() {
  cat <<'EOF'
Available commands:

agent-check         # verify scaffold files exist
agent-status        # show task summary
agent-next          # show next unblocked task
agent-start         # print worker prompt
agent-review        # print reviewer prompt
agent-plan          # print planner prompt
agent-log           # create a dated session log
agent-done ID       # mark a task done
agent-in-progress ID# mark a task in progress
agent-help          # show this help
EOF
}