#!/usr/bin/env node
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { argv } from 'node:process';

const defaultLogsDir = 'agent/logs';
let logsDir = defaultLogsDir;

try {
  const configUrl = new URL('../agent/agent-config.json', import.meta.url);
  const config = JSON.parse(readFileSync(configUrl, 'utf-8'));
  if (typeof config?.logging?.logsDir === 'string' && config.logging.logsDir.trim()) {
    logsDir = config.logging.logsDir;
  }
} catch {
  logsDir = defaultLogsDir;
}
if (!existsSync(logsDir)) mkdirSync(logsDir, { recursive: true });

const [taskId = 'unknown-task', ...noteParts] = argv.slice(2);
const note = noteParts.join(' ').trim() || 'No note provided';
const stamp = new Date().toISOString();
const line = `- ${stamp} | ${taskId} | ${note}\n`;

appendFileSync(`${logsDir}/agent-runs.log`, line, 'utf-8');
console.log(`Logged run: ${line.trim()}`);
