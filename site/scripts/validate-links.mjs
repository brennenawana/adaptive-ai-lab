#!/usr/bin/env node
/**
 * Post-build link validation: every internal href in dist/ must resolve to a
 * built file, and every fragment must resolve to an element id on the target
 * page. Fails the build on any broken internal link or anchor.
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const dist = resolve(dirname(fileURLToPath(import.meta.url)), '..', 'dist');
const base = (process.env.SITE_BASE ?? '/').replace(/\/$/, '');

if (!existsSync(dist)) {
  console.error('[links] dist/ not found — run astro build first');
  process.exit(1);
}

const htmlFiles = [];
(function walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p);
    else if (name.endsWith('.html')) htmlFiles.push(p);
  }
})(dist);

const idCache = new Map();
function idsOf(file) {
  let ids = idCache.get(file);
  if (!ids) {
    const html = readFileSync(file, 'utf8');
    ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]));
    idCache.set(file, ids);
  }
  return ids;
}

function targetFile(path) {
  // '/x/y/' -> dist/x/y/index.html ; '/x.json' -> dist/x.json
  const rel = path.replace(/^\//, '');
  const asFile = join(dist, rel);
  if (rel.endsWith('/')) return join(asFile, 'index.html');
  if (/\.[a-z0-9]+$/i.test(rel)) return asFile;
  return join(asFile, 'index.html');
}

const problems = [];
let checked = 0;

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  for (const m of html.matchAll(/\bhref="([^"]+)"/g)) {
    const href = m[1];
    if (/^(https?:|mailto:|data:)/.test(href)) continue;
    checked++;
    const [rawPath, fragment] = href.split('#', 2);
    let target = file;
    if (rawPath) {
      let path = rawPath;
      if (base && path.startsWith(base + '/')) path = path.slice(base.length);
      if (!path.startsWith('/')) {
        problems.push(`${file.replace(dist, '')}: relative href "${href}"`);
        continue;
      }
      target = targetFile(path);
      if (!existsSync(target)) {
        // pagefind assets exist only after indexing; they are validated by presence of the dir
        problems.push(`${file.replace(dist, '')}: broken link "${href}"`);
        continue;
      }
    }
    if (fragment && target.endsWith('.html')) {
      const id = decodeURIComponent(fragment);
      if (id && !idsOf(target).has(id)) {
        problems.push(`${file.replace(dist, '')}: broken anchor "${href}"`);
      }
    }
  }
}

if (problems.length) {
  console.error(`[links] ${problems.length} broken internal links/anchors (of ${checked} checked):`);
  for (const p of problems.slice(0, 60)) console.error('  ' + p);
  if (problems.length > 60) console.error(`  … and ${problems.length - 60} more`);
  process.exit(1);
}
console.log(`[links] OK — ${checked} internal links/anchors validated across ${htmlFiles.length} pages`);
