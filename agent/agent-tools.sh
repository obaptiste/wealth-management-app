#!/usr/bin/env bash

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
    AGENT_TASKS_FILE="$AGENT_TASKS_FILE" python3 - <<'PY'
import json
import os
from collections import Counter

path = os.environ["AGENT_TASKS_FILE"]

with open(path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

status_counts = Counter(task.get("status", "unknown") for task in tasks)
priority_counts = Counter(task.get("priority", "unknown") for task in tasks)

print("By status:")
for k, v in sorted(status_counts.items()):
    print(f"  {k}: {v}")

print("\nBy priority:")
for k, v in sorted(priority_counts.items()):
    print(f"  {k}: {v}")

done_ids = {t["id"] for t in tasks if t.get("status") == "done"}

in_progress = [t for t in tasks if t.get("status") == "in_progress"]
if in_progress:
    print("\nIn progress:")
    for task in in_progress:
        started = task.get("startedAt", "—")
        print(f"- {task['id']} | {task['priority']} | started: {started} | {task['title']}")

print("\nOpen tasks (todo):")
for task in tasks:
    if task.get("status") not in ("done", "in_progress"):
        deps = task.get("dependsOn", [])
        blocked = any(dep not in done_ids for dep in deps)
        label = "BLOCKED" if blocked else "ready"
        deps_str = ", ".join(deps) or "none"
        print(f"- {task['id']} | {task['priority']} | {label} | deps: {deps_str} | {task['title']}")
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

  AGENT_TASKS_FILE="$AGENT_TASKS_FILE" python3 - <<'PY'
import json
import os

path = os.environ["AGENT_TASKS_FILE"]

with open(path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

done_ids = {t["id"] for t in tasks if t.get("status") == "done"}
priority_order = {"high": 0, "medium": 1, "low": 2}
# in_progress tasks sort ahead of todo tasks at the same priority level
status_order = {"in_progress": 0, "todo": 1}

unblocked = []
for task in tasks:
    if task.get("status") == "done":
        continue
    deps = task.get("dependsOn", [])
    if all(dep in done_ids for dep in deps):
        unblocked.append(task)

unblocked.sort(key=lambda t: (
    priority_order.get(t.get("priority", "low"), 99),
    status_order.get(t.get("status", "todo"), 99),
    t["id"],
))

if not unblocked:
    print("No unblocked tasks found.")
else:
    t = unblocked[0]
    print(f"{t['id']}: {t['title']}")
    print(f"Priority: {t.get('priority')}")
    print(f"Status: {t.get('status')}")
    if t.get("startedAt"):
        print(f"Started: {t['startedAt']}")
    print(f"Description: {t.get('description')}")
PY
}

agent-blocked() {
  if [[ ! -f "$AGENT_TASKS_FILE" ]]; then
    echo "Missing $AGENT_TASKS_FILE"
    return 1
  fi

  AGENT_TASKS_FILE="$AGENT_TASKS_FILE" python3 - <<'PY'
import json
import os

path = os.environ["AGENT_TASKS_FILE"]

with open(path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

done_ids = {t["id"] for t in tasks if t.get("status") == "done"}
id_to_title = {t["id"]: t["title"] for t in tasks}

blocked = []
for task in tasks:
    if task.get("status") == "done":
        continue
    missing_deps = [dep for dep in task.get("dependsOn", []) if dep not in done_ids]
    if missing_deps:
        blocked.append((task, missing_deps))

if not blocked:
    print("No blocked tasks.")
else:
    print("Blocked tasks:")
    for task, missing in blocked:
        print(f"\n- {task['id']} | {task['priority']} | {task['title']}")
        for dep in missing:
            label = id_to_title.get(dep, dep)
            dep_status = next((t.get("status", "?") for t in tasks if t["id"] == dep), "?")
            print(f"    waiting on: {dep} ({dep_status}) — {label}")
PY
}

agent-context() {
  # Print all memory files in a single pass so agents can read context with
  # one command instead of opening seven files individually. This reduces the
  # per-session token overhead when priming an agent with project state.
  for file in \
    "CLAUDE.md" \
    "$AGENT_MEMORY_DIR/project-summary.md" \
    "$AGENT_MEMORY_DIR/architecture.md" \
    "$AGENT_MEMORY_DIR/current-state.md" \
    "$AGENT_MEMORY_DIR/decisions.md" \
    "$AGENT_MEMORY_DIR/next-steps.md"
  do
    if [[ -f "$file" ]]; then
      echo "===== $file ====="
      cat "$file"
      echo
    else
      echo "===== $file (missing) ====="
      echo
    fi
  done
}

agent-start() {
  cat <<'EOF'
Run `source agent/agent-tools.sh && agent-context` to load all project context
in one step, then read agent/tasks.json and agent/prompts/worker.md.

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
Run `source agent/agent-tools.sh && agent-context` to load all project context
in one step, then read agent/tasks.json and agent/prompts/reviewer.md.

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
Run `source agent/agent-tools.sh && agent-context` to load all project context
in one step, then read agent/tasks.json and agent/prompts/planner.md.

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

## Next task
$(agent-next 2>/dev/null || echo "(none)")

## Blocked tasks
$(agent-blocked 2>/dev/null || echo "(none)")

## Notes
- 

## Outcome
- 

## Follow-up
- 
EOF

  echo "Created log: $file"
}

# -----------------------------
# shared internal helper
# Sets task status and optional timestamp fields.
# Usage: _agent_set_task_status <task-id> <status> [timestamp-key] [timestamp-value]
# -----------------------------
_agent_set_task_status() {
  local task_id="$1"
  local new_status="$2"
  local ts_key="${3:-}"
  local ts_val="${4:-}"

  AGENT_TASKS_FILE="$AGENT_TASKS_FILE" python3 - "$task_id" "$new_status" "$ts_key" "$ts_val" <<'PY'
import json
import os
import sys

task_id = sys.argv[1]
new_status = sys.argv[2]
ts_key = sys.argv[3] if len(sys.argv) > 3 else ""
ts_val = sys.argv[4] if len(sys.argv) > 4 else ""
path = os.environ["AGENT_TASKS_FILE"]

with open(path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

found = False
for task in tasks:
    if task.get("id") == task_id:
        task["status"] = new_status
        if ts_key and ts_val:
            task[ts_key] = ts_val
        found = True
        break

if not found:
    print(f"Task not found: {task_id}")
    sys.exit(1)

with open(path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)
    f.write("\n")

print(f"Marked {task_id} as {new_status}.")
PY
}

agent-done() {
  local task_id="${1:-}"
  if [[ -z "$task_id" ]]; then
    echo "Usage: agent-done task-001"
    return 1
  fi
  local today
  today="$(date +"%Y-%m-%d")"
  _agent_set_task_status "$task_id" "done" "completedAt" "$today"
}

agent-in-progress() {
  local task_id="${1:-}"
  if [[ -z "$task_id" ]]; then
    echo "Usage: agent-in-progress task-001"
    return 1
  fi
  local today
  today="$(date +"%Y-%m-%d")"
  _agent_set_task_status "$task_id" "in_progress" "startedAt" "$today"
}

agent-help() {
  cat <<'EOF'
Available commands:

agent-check          # verify scaffold files exist
agent-status         # show task summary (in-progress, todo, blocked)
agent-next           # show next unblocked task (in-progress first)
agent-blocked        # show blocked tasks and what is blocking them
agent-context        # print all memory files in one pass (for agent priming)
agent-start          # print worker prompt
agent-review         # print reviewer prompt
agent-plan           # print planner prompt
agent-log            # create a dated session log
agent-done ID        # mark a task done (sets completedAt)
agent-in-progress ID # mark a task in progress (sets startedAt)
agent-help           # show this help
EOF
}