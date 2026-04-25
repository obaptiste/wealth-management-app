#!/usr/bin/env node
import { existsSync, readFileSync } from 'node:fs';

const required = [
  'CLAUDE.md',
  'agent/README.md',
  'agent/agent-config.json',
  'agent/tasks.json',
  'agent/memory/project-summary.md',
  'agent/memory/architecture.md',
  'agent/memory/current-state.md',
  'agent/memory/decisions.md',
  'agent/memory/known-issues.md',
  'agent/memory/next-steps.md',
  'agent/prompts/planner.md',
  'agent/prompts/worker.md',
  'agent/prompts/reviewer.md',
  'agent/prompts/pr-writer.md'
];

let ok = true;
for (const file of required) {
  if (!existsSync(file)) {
    ok = false;
    console.error(`MISSING: ${file}`);
  }
}

try {
  const tasks = JSON.parse(readFileSync('agent/tasks.json', 'utf-8'));
  for (const task of tasks) {
    for (const key of ['id', 'title', 'type', 'priority', 'status', 'description', 'files', 'acceptanceCriteria', 'riskLevel', 'suggestedAgent', 'createdAt', 'updatedAt', 'dependsOn']) {
      if (!(key in task)) {
        ok = false;
        console.error(`TASK ${task.id ?? '<unknown>'} missing key: ${key}`);
      }
    }
    if (!Array.isArray(task.dependsOn) || task.dependsOn.some((dependency) => typeof dependency !== 'string')) {
      ok = false;
      console.error(`TASK ${task.id ?? '<unknown>'} has invalid dependsOn; expected an array of strings`);
    }
  }
} catch (error) {
  ok = false;
  console.error(`Failed to parse tasks.json: ${error.message}`);
}

if (!ok) process.exit(1);
console.log('Agent harness healthcheck passed.');
