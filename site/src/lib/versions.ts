/** Playbook version manifest access (site/versions.json + materialized metas). */
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { SITE_DIR } from './repo.ts';

const siteDir = SITE_DIR;

export interface VersionEntry {
  version: string;
  commit: string;
  date: string;
  label: string;
  exclude?: string[];
}

export interface VersionMeta extends VersionEntry {
  commitDate: string;
  fileCount: number;
  excluded: string[];
}

const manifest = JSON.parse(readFileSync(join(siteDir, 'versions.json'), 'utf8')) as {
  versions: VersionEntry[];
};

/** All historical versions, newest first (as ordered in the manifest). */
export const VERSIONS: VersionEntry[] = manifest.versions;

/** The version string of the current working playbook/. */
export const CURRENT_VERSION: string = readFileSync(
  join(siteDir, '..', 'playbook', 'VERSION'),
  'utf8',
).trim();

export function versionCacheDir(version: string): string {
  return join(siteDir, '.versions-cache', version);
}

export function versionMeta(version: string): VersionMeta {
  const p = join(versionCacheDir(version), '.meta.json');
  if (!existsSync(p)) {
    throw new Error(
      `Version ${version} is not materialized. Run: node scripts/materialize-versions.mjs`,
    );
  }
  return JSON.parse(readFileSync(p, 'utf8')) as VersionMeta;
}

/** Files (repo-relative under playbook/) present in a materialized version. */
export function versionHasFile(version: string, playbookRelPath: string): boolean {
  return existsSync(join(versionCacheDir(version), 'playbook', playbookRelPath));
}
