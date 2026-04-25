#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';

const args = process.argv.slice(2);
const summary = args.length > 0 ? args.join(' ') : 'No summary provided';
const file = 'agent/memory/current-state.md';
const existing = readFileSync(file, 'utf-8');
const date = new Date().toISOString().slice(0, 10);

const entry = `\n## Update ${date}\n- ${summary}\n`;
writeFileSync(file, `${existing.trimEnd()}\n${entry}`, 'utf-8');
console.log(`Updated ${file}`);
