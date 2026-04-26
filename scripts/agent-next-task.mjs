#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const tasks = JSON.parse(readFileSync(new URL('../agent/tasks.json', import.meta.url), 'utf-8'));

const done = new Set(tasks.filter((t) => t.status === 'done').map((t) => t.id));
const priority = { critical: 0, high: 1, medium: 2, low: 3 };
const risk = { low: 0, medium: 1, high: 2 };

const ready = tasks
  .filter((t) => t.status === 'todo' || t.status === 'in_progress')
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
