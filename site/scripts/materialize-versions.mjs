#!/usr/bin/env node
/**
 * Materialize historical playbook versions from git history into
 * site/.versions-cache/<version>/ (gitignored, build-time only).
 *
 * Source of truth: site/versions.json — an explicit version -> commit manifest.
 * Integrity: refuses to materialize a version whose committed playbook/VERSION
 * does not match the manifest entry. Historical prose is extracted byte-for-byte
 * with `git show <commit>:<path>`; nothing is edited.
 *
 * Idempotent: a version already materialized from the same commit is skipped
 * (delete .versions-cache/ or pass --force to re-extract).
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const siteDir = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repoDir = resolve(siteDir, '..');
const cacheDir = join(siteDir, '.versions-cache');
const force = process.argv.includes('--force');

const git = (...args) =>
  execFileSync('git', ['-C', repoDir, ...args], { encoding: 'buffer', maxBuffer: 64 * 1024 * 1024 });

const manifest = JSON.parse(readFileSync(join(siteDir, 'versions.json'), 'utf8'));

for (const v of manifest.versions) {
  const outDir = join(cacheDir, v.version);
  const metaPath = join(outDir, '.meta.json');

  if (!force && existsSync(metaPath)) {
    const meta = JSON.parse(readFileSync(metaPath, 'utf8'));
    if (meta.commit === v.commit) {
      console.log(`[versions] ${v.version} already materialized from ${v.commit.slice(0, 12)} — skipped`);
      continue;
    }
  }

  // Integrity gate: the committed VERSION file must match the manifest.
  const committedVersion = git('show', `${v.commit}:playbook/VERSION`).toString('utf8').trim();
  if (committedVersion !== v.version) {
    console.error(
      `[versions] INTEGRITY FAILURE: manifest says ${v.version} -> ${v.commit}, ` +
        `but playbook/VERSION at that commit reads "${committedVersion}". Refusing to build.`,
    );
    process.exit(1);
  }

  const allFiles = git('ls-tree', '-r', '--name-only', v.commit, '--', 'playbook/')
    .toString('utf8')
    .split('\n')
    .filter(Boolean);

  const excluded = (path) =>
    (v.exclude ?? []).some((e) => (e.endsWith('/') ? path.startsWith(e) : path === e));

  const files = allFiles.filter((f) => !excluded(f));

  rmSync(outDir, { recursive: true, force: true });
  for (const f of files) {
    const rel = f.replace(/^playbook\//, '');
    const dest = join(outDir, 'playbook', rel);
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, git('show', `${v.commit}:${f}`));
  }

  const commitDate = git('show', '-s', '--format=%ci', v.commit).toString('utf8').trim();
  writeFileSync(
    metaPath,
    JSON.stringify(
      {
        version: v.version,
        commit: v.commit,
        commitDate,
        date: v.date,
        label: v.label,
        fileCount: files.length,
        excluded: allFiles.filter(excluded),
      },
      null,
      2,
    ),
  );
  console.log(`[versions] materialized ${v.version} from ${v.commit.slice(0, 12)} (${files.length} files)`);
}
