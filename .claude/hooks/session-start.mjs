#!/usr/bin/env node
// SessionStart hook: loads the project's memory into every new session (startup, resume, /clear, compaction).
// Prints LESSONS, then PROGRESS, then git state. Plain stdout becomes context, so keep it under ~9,000 characters.
import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';

const PROJECT = 'PASSPORT';
const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const LIMIT = 9000;
let source = 'startup';
try {
  const input = readFileSync(0, 'utf8');
  if (input.trim()) source = JSON.parse(input).source || source;
} catch { /* no stdin: fine */ }

const read = (rel) => {
  const p = join(root, rel);
  return existsSync(p) ? readFileSync(p, 'utf8').trim() : `(missing: ${rel})`;
};
const git = (args) => {
  try { return execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 3000 }).trim(); }
  catch { return ''; }
};
const cap = (text, max, note) => (text.length <= max ? text : `${text.slice(0, max)}\n… (${note})`);

const lessons = read('docs/LESSONS.md');
const progress = read('docs/PROGRESS.md');
const branch = git(['branch', '--show-current']);
const log = git(['log', '--oneline', '-5']);
const status = git(['status', '--short']).split('\n').filter(Boolean);

const warnings = [];
if (lessons.split('\n').length > 120) warnings.push('LESSONS.md is over 120 lines: merge duplicates, keep one line per lesson.');
if (progress.split('\n').length > 150) warnings.push('PROGRESS.md is over 150 lines: move finished details to AI-LOG.md.');
if (branch === 'main' && status.length) warnings.push('Uncommitted changes on main: work on a feature branch (CLAUDE.md, Git rules).');

const header = [
  `# ${PROJECT}: session memory (loaded automatically by .claude/hooks/session-start.mjs)`,
  source === 'compact'
    ? 'The conversation was just compacted. Re-read the files for the current task before editing, and keep to the plan in PROGRESS.md.'
    : 'Follow CLAUDE.md. Gate changes: passport-gate skill. API shapes: contracts/README.md. Facts: docs/FACTS.md. Never guess an API: verify-before-use skill. Done = make check passes.',
  ...warnings.map((w) => `WARNING: ${w}`),
].join('\n');

const gitBlock = branch || log
  ? ['## git', `branch: ${branch || '(none)'}`, log ? `last commits:\n${log}` : 'no commits yet',
     status.length ? `uncommitted (${status.length}):\n${status.slice(0, 15).join('\n')}${status.length > 15 ? '\n…' : ''}` : 'working tree clean'].join('\n')
  : '## git\n(not a git repository yet: see START-HERE.md)';

const budget = LIMIT - header.length - gitBlock.length - 200;
const lessonsBlock = `## docs/LESSONS.md\n${cap(lessons, Math.floor(budget * 0.35), 'truncated: open docs/LESSONS.md for the rest')}`;
const progressBlock = `## docs/PROGRESS.md\n${cap(progress, budget - lessonsBlock.length, 'truncated: run /start or open docs/PROGRESS.md')}`;

process.stdout.write([header, lessonsBlock, progressBlock, gitBlock].join('\n\n') + '\n');
process.exit(0);
