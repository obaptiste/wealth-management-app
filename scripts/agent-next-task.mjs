#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const tasks = JSON.parse(readFileSync(new URL('../agent/tasks.json', import.meta.url), 'utf-8'));
const agentConfig = JSON.parse(readFileSync(new URL('../agent/agent-config.json', import.meta.url), 'utf-8'));

function toRankMap(values = []) {
  return Object.fromEntries(values.map((value, index) => [value, index]));
}

const taskSelection = agentConfig.taskSelection ?? {};
const done = new Set(tasks.filter((t) => t.status === 'done').map((t) => t.id));
const priority = toRankMap(taskSelection.priorityOrder);
const risk = toRankMap(taskSelection.riskOrder);
const readyStatuses = new Set(taskSelection.statusReady ?? []);

const ready = tasks
  .filter((t) => readyStatuses.has(t.status))
  .filter((t) => (t.dependsOn ?? []).every((dep) => done.has(dep)))
  .sort((a, b) => {
    const p = (priority[a.priority] ?? 99) - (priority[b.priority] ?? 99);
    if (p !== 0) return p;
    const r = (risk[a.riskLevel] ?? 99) - (risk[b.riskLevel] ?? 99);
    if (r !== 0) return r;
    return a.id.localeCompare(b.id);
  });

if (ready.length === 0) {
  console.log('No unblocked tasks available.');
  process.exit(0);
}

const next = ready[0];
console.log(JSON.stringify(next, null, 2));
