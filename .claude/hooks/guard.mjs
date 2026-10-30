#!/usr/bin/env node
// PostToolUse guard for Edit/Write. Adapted for PASSPORT from the team's hackathon starter.
// Checks: overclaiming words in UI text, raw colours outside tokens.css, secrets in files,
// and PASSPORT invariants in the backend (tools only via the gate, no unsafe calls).
// Exit 2 + stderr = Claude sees the problems and fixes them. Exit 0 = fine. Never blocks on its own errors.
// Exceptions: put `design-ok: <reason>`, `copy-ok: <reason>` or `gate-ok: <reason>` on the same line.
import { readFileSync, existsSync } from 'node:fs';
import { relative, isAbsolute, join, sep } from 'node:path';

// ======================= CONFIG =======================
const CONFIG = {
  uiCode: /^frontend\/src\/.+\.(tsx|ts|css)$/,
  uiExempt: /^frontend\/src\/styles\/tokens\.css$/,
  backendCode: /^backend\/app\/.+\.py$/,
  // the only files allowed to call tool functions
  toolCallers: /^backend\/app\/(gate\/handle\.py|tools\/registry\.py)$/,
  banned: [
    ['100%', 'say the measured number from the eval'], ['guaranteed', 'remove it'], ['guarantee', 'remove it'],
    ['unhackable', 'remove it'], ['unbreakable', 'remove it'], ['bulletproof', 'remove it'],
    ['military-grade', 'remove it'], ['bank-grade', 'remove it'], ['impossible to bypass', 'say what it blocks'],
    ['blocks all attacks', 'say which scenarios it blocks'], ['fully secure', 'say the honest limit'],
    ['revolutionary', 'say what it does'], ['seamless', 'say what it does'], ['ai-powered', 'say what the model does'],
  ],
  allowedPhrases: [],
  skipSecrets: /^(docs|contracts|design|prompts|\.claude)\//,
  secrets: [
    [/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/, 'a JWT / signed token'],
    [/-----BEGIN (?:EC |RSA |ENCRYPTED |OPENSSH )?PRIVATE KEY-----/, 'a private key'],
    [/\bsk-(?:proj-|or-v1-)?[A-Za-z0-9_-]{20,}/, 'an API secret key (sk-…)'],
    [/\bgsk_[A-Za-z0-9]{20,}/, 'a Groq API key'],
    [/\bAIza[0-9A-Za-z_-]{30,}/, 'a Google API key'],
    [/\bAKIA[0-9A-Z]{16}\b/, 'an AWS access key'],
    [/\bghp_[A-Za-z0-9]{30,}/, 'a GitHub token'],
    [/postgres(?:ql)?:\/\/[^:\s]+:[^@\s]+@/, 'a database URL with a password'],
    [/nmb_live_CANARY_[0-9a-f]{8,}|CANARY_db_[0-9a-f]{8,}/, 'a generated canary value (copied from a log?)'],
  ],
  backendUnsafe: [
    [/\beval\(|\bexec\(/, 'eval/exec on data'],
    [/shell\s*=\s*True/, 'subprocess with shell=True'],
    [/\bpickle\.loads?\(/, 'pickle on data'],
    [/\byaml\.load\((?![^)]*SafeLoader)/, 'yaml.load without SafeLoader (use yaml.safe_load)'],
    [/f["'][^"']*\b(SELECT|INSERT|UPDATE|DELETE)\b[^"']*\{/i, 'SQL built with an f-string (use ? parameters)'],
    [/allow_origins\s*=\s*\[\s*["']\*["']/, 'CORS open to *'],
  ],
};
// ======================================================

const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
let input = {};
try { input = JSON.parse(readFileSync(0, 'utf8') || '{}'); } catch { process.exit(0); }
const raw = input.tool_input?.file_path || input.tool_input?.path || '';
if (!raw) process.exit(0);
const abs = isAbsolute(raw) ? raw : join(root, raw);
const rel = relative(root, abs).split(sep).join('/');
if (rel.startsWith('..') || !existsSync(abs)) process.exit(0);
let text;
try { text = readFileSync(abs, 'utf8'); } catch { process.exit(0); }

const problems = [];
const add = (line, msg) => problems.push(line ? `line ${line}: ${msg}` : msg);
const lines = text.split('\n');

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const BANNED_RE = CONFIG.banned.map(([w, hint]) => [w, hint, new RegExp(`(?<![\\p{L}\\p{M}\\p{N}_-])${esc(w)}(?![\\p{L}\\p{M}\\p{N}_-])`, 'iu')]);
const bannedIn = (s) => {
  let t = s.toLowerCase();
  for (const p of CONFIG.allowedPhrases) t = t.split(p.toLowerCase()).join(' ');
  return BANNED_RE.filter(([, , re]) => re.test(t)).map(([w, hint]) => `"${w}" (${hint})`);
};

// ---------- 1. UI code: tokens only + wording ----------
const HEX = /#[0-9a-fA-F]{3,8}\b/;
const RGB = /\brgba?\(\s*\d/;
if (CONFIG.uiCode.test(rel) && !CONFIG.uiExempt.test(rel)) {
  lines.forEach((ln, i) => {
    const n = i + 1;
    if (/design-ok/.test(ln) || /^\s*(\/\/|\*|\/\*)/.test(ln)) return;
    if (HEX.test(ln) && !/(href|id)\s*=\s*["']#/.test(ln)) add(n, `raw colour ${ln.match(HEX)[0]}: use a token from src/styles/tokens.css`);
    if (RGB.test(ln) && rel.endsWith('.css')) add(n, 'raw rgb() colour: use a token (or color-mix with tokens)');
    if (/\.(tsx|jsx)$/.test(rel) && !/copy-ok/.test(ln)) {
      const texts = [...ln.matchAll(/>([^<>{}]*[\p{L}][^<>{}]*)</gu)].map((m) => m[1]);
      for (const m of ln.matchAll(/\b(?:aria-label|title|alt|placeholder)=["']([^"']+)["']/g)) texts.push(m[1]);
      for (const s of texts) { const hits = bannedIn(s); if (hits.length) add(n, `wording ${hits.join(', ')}`); }
    }
  });
}

// ---------- 2. Backend: PASSPORT invariants + unsafe calls ----------
if (CONFIG.backendCode.test(rel)) {
  lines.forEach((ln, i) => {
    const n = i + 1;
    if (/gate-ok/.test(ln) || /^\s*#/.test(ln)) return;
    if (!CONFIG.toolCallers.test(rel) && /\brun_tool\(/.test(ln))
      add(n, 'tools may only run through app/gate/handle.py (rule 1 in CLAUDE.md)');
    for (const [re, what] of CONFIG.backendUnsafe) if (re.test(ln)) add(n, `unsafe: ${what}`);
    if (/except\s+Exception[^:]*:\s*$/.test(ln) && /gate\//.test(rel) && !/decide\.py$/.test(rel))
      add(n, 'broad except in the gate: make sure the result is DENY (fail closed), or add "gate-ok: <reason>"');
  });
}

// ---------- 3. secrets anywhere (except docs and examples) ----------
if (!CONFIG.skipSecrets.test(rel) && !/(^|\/)\.env/.test(rel)) {
  lines.forEach((ln, i) => { for (const [re, what] of CONFIG.secrets) if (re.test(ln)) add(i + 1, `${what} in a file: secrets live only in .env files and the host's settings`); });
}

if (problems.length) {
  process.stderr.write(`guard: ${rel}\n${problems.slice(0, 25).map((p) => ` - ${p}`).join('\n')}${problems.length > 25 ? `\n - … ${problems.length - 25} more` : ''}\n` +
    'Fix these. If one is a real exception, add "design-ok: <reason>", "copy-ok: <reason>" or "gate-ok: <reason>" on that line.\n');
  process.exit(2);
}
process.exit(0);
