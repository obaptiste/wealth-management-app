#!/usr/bin/env node
import { appendFileSync, existsSync, mkdirSync } from 'node:fs';
import { argv } from 'node:process';

const logsDir = 'agent/logs';
if (!existsSync(logsDir)) mkdirSync(logsDir, { recursive: true });

const [taskId = 'unknown-task', ...noteParts] = argv.slice(2);
const note = noteParts.join(' ').trim() || 'No note provided';
const stamp = new Date().toISOString();
const line = `- ${stamp} | ${taskId} | ${note}\n`;

appendFileSync(`${logsDir}/agent-runs.log`, line, 'utf-8');
console.log(`Logged run: ${line.trim()}`);
