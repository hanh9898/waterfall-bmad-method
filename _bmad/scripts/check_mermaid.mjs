// Validate every ```mermaid``` block in docs/ + top-level READMEs using the
// official Mermaid parser (mermaid.parse), headless via jsdom — no browser.
//
// Requires devDependencies: mermaid, jsdom  (npm install)
// Usage: node _bmad/scripts/check_mermaid.mjs [projectRoot]
// Exit 0 if all blocks parse, 1 otherwise (CI-friendly).

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';
import { JSDOM } from 'jsdom';

const root = process.argv[2] ? process.argv[2] : process.cwd();

function collectMarkdown(dir, out) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) collectMarkdown(p, out);
    else if (name.endsWith('.md')) out.push(p);
  }
}

const files = [];
const docsDir = join(root, 'docs');
if (existsSync(docsDir)) collectMarkdown(docsDir, files);
for (const r of ['README.md', 'README.en.md']) {
  const p = join(root, r);
  if (existsSync(p)) files.push(p);
}
files.sort();

const blockRe = /```mermaid\n([\s\S]*?)```/g;

// Headless DOM so mermaid can initialize outside a browser.
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
try {
  Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
} catch { /* navigator may be read-only; mermaid.parse tolerates it */ }
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.SVGElement = dom.window.SVGElement;
globalThis.DOMParser = dom.window.DOMParser;

const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });

let totalBlocks = 0;
let failures = 0;

for (const file of files) {
  const text = readFileSync(file, 'utf8');
  const rel = relative(root, file).replace(/\\/g, '/');
  let m;
  let idx = 0;
  blockRe.lastIndex = 0;
  while ((m = blockRe.exec(text)) !== null) {
    idx += 1;
    totalBlocks += 1;
    const line = text.slice(0, m.index).split('\n').length;
    try {
      await mermaid.parse(m[1]);
    } catch (e) {
      failures += 1;
      const msg = (e && e.message ? e.message : String(e)).split('\n')[0];
      console.log(`FAIL  ${rel} (block ${idx}, line ${line})\n        -> ${msg}`);
    }
  }
}

if (failures) {
  console.log(`\nFAIL: ${failures}/${totalBlocks} mermaid block(s) invalid.`);
  process.exit(1);
}
console.log(`OK: all ${totalBlocks} mermaid block(s) parse across ${files.length} file(s).`);
