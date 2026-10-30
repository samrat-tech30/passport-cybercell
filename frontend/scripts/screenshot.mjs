#!/usr/bin/env node
// Screenshots for the UI loop (project-ui skill, ui-critic agent). Run from the repo root or frontend/.
//   node frontend/scripts/screenshot.mjs /                      desktop 1440x900, Agent tab
//   node frontend/scripts/screenshot.mjs / --run s2             pick scenario s2, press Run scenario, wait for the end
//   node frontend/scripts/screenshot.mjs / --run s2 --off       same with the shield off
//   node frontend/scripts/screenshot.mjs / --tab scoreboard     open a tab (agent | scoreboard | audit)
//   node frontend/scripts/screenshot.mjs / --projector          1280x720 (what the hall sees)
// Options: --width N --height N --full --base URL (default http://localhost:5173) --out DIR (default screenshots)
// Needs Playwright: `npm i -D playwright` in frontend/ (and `npx playwright install chromium` if no Chrome).
import { mkdirSync } from 'node:fs';

const argv = process.argv.slice(2);
const opt = { route: '/', width: 1440, height: 900, run: null, off: false, tab: null, full: false,
  base: 'http://localhost:5173', out: 'screenshots' };
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (!a.startsWith('--')) { opt.route = a.startsWith('/') ? a : `/${a}`; continue; }
  const key = a.slice(2);
  if (key === 'projector') { opt.width = 1280; opt.height = 720; }
  else if (['off', 'full'].includes(key)) opt[key] = true;
  else if (key in opt) opt[key] = argv[++i];
  else { console.error(`Unknown option ${a}`); process.exit(1); }
}

let chromium;
try { ({ chromium } = await import('playwright')); }
catch { console.error('Playwright is missing. Run in frontend/: npm i -D playwright  (then: npx playwright install chromium)'); process.exit(1); }

try { await fetch(opt.base, { method: 'HEAD' }); }
catch { console.error(`Nothing answers at ${opt.base}. Start it first: make frontend (and make backend).`); process.exit(1); }

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Number(opt.width), height: Number(opt.height) }, reducedMotion: 'reduce' });
const problems = [];
page.on('console', (m) => { if (m.type() === 'error') problems.push(m.text()); });
page.on('pageerror', (e) => problems.push(e.message));

await page.goto(opt.base + opt.route);
await page.waitForSelector('.topbar');
if (opt.tab) await page.click(`button.tab >> text=${opt.tab[0].toUpperCase()}${opt.tab.slice(1)}`);
if (opt.run) {
  await page.selectOption('select >> nth=0', opt.run);
  const on = (await page.getAttribute('[role=switch]', 'aria-checked')) === 'true';
  if (on === opt.off) await page.click('[role=switch]');
  await page.click('text=Run scenario');
  await page.waitForSelector('.done, dialog.approval[open], .error', { timeout: 15000 });
}
await page.waitForTimeout(400);
mkdirSync(opt.out, { recursive: true });
const name = `${opt.out}/${(opt.tab ?? 'agent')}${opt.run ? `-${opt.run}${opt.off ? '-off' : ''}` : ''}-${opt.width}x${opt.height}.png`;
await page.screenshot({ path: name, fullPage: Boolean(opt.full) });
await browser.close();
console.log(`saved ${name}`);
if (problems.length) { console.log('console errors:\n - ' + problems.join('\n - ')); }
