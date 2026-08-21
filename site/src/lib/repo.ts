/** Repository locations + canonical-source (GitHub) link helpers. */
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

declare const __SITE_DIR__: string | undefined;

/** Absolute path of site/ — injected by astro.config at build time (the
 * bundled prerender output cannot derive it from import.meta.url); the
 * import.meta fallback covers plain-node execution of these libs. */
export const SITE_DIR: string =
  typeof __SITE_DIR__ === 'string'
    ? __SITE_DIR__
    : fileURLToPath(new URL('../..', import.meta.url));

/** Absolute path of the repository root (site/ lives directly under it). */
export const REPO_ROOT = resolve(SITE_DIR, '..');

export const GITHUB_REPO = 'https://github.com/brennenawana/adaptive-ai-lab';

/** Link to a file in the canonical repository at a given ref (branch or commit). */
export function githubBlobUrl(repoRelPath: string, ref = 'main'): string {
  return `${GITHUB_REPO}/blob/${ref}/${repoRelPath}`;
}

export function githubCommitUrl(sha: string): string {
  return `${GITHUB_REPO}/commit/${sha}`;
}
