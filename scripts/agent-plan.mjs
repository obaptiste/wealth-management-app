#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const tasks = JSON.parse(readFileSync(new URL('../agent/tasks.json', import.meta.url), 'utf-8'));

const grouped = tasks.reduce((acc, task) => {
  acc[task.status] ??= [];
  acc[task.status].push(task);
  return acc;
}, {});

console.log('Agent Task Plan Summary');
for (const status of ['in_progress', 'todo', 'blocked', 'done']) {
  const list = grouped[status] ?? [];
  if (list.length === 0) continue;
  console.log(`\n${status.toUpperCase()} (${list.length})`);
  for (const t of list) {
    console.log(`- ${t.id} [${t.priority}] (${t.type}) ${t.title}`);
  }
}
