/**
 * Corpus enumeration: which canonical files exist in a given space
 * (current working tree, or a materialized historical version), and how each
 * maps to a site page. Content is read from the canonical location at build
 * time — never copied into the site tree.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from './repo.ts';
import { repoPathToRoute, spacePrefix, type RouteInfo } from './routes.ts';
import { versionCacheDir, VERSIONS } from './versions.ts';

/** null = current space (working tree); otherwise a historical version string. */
export type Space = string | null;

export type PageKind = 'doc' | 'glossary' | 'sources' | 'changelog' | 'templates-index';

export interface PageDef {
  /** repo-relative canonical path, e.g. "playbook/03_EVALUATION_FOUNDATION.md" */
  repoPath: string;
  /** space-relative route (leading+trailing slash) */
  route: string;
  /** full route including version prefix */
  fullRoute: string;
  section: RouteInfo['section'];
  kind: PageKind;
  space: Space;
  /** document group used for ordering/prev-next: 'book' | 'templates' | 'cases' | 'references' | 'research' */
  group: 'book' | 'templates' | 'cases' | 'references' | 'research' | 'meta';
  /** order within its group */
  order: number;
}

/** Root directory that holds `playbook/` (and for current, `research/`) for a space. */
export function spaceRoot(space: Space): string {
  return space === null ? REPO_ROOT : versionCacheDir(space);
}

/** Read a canonical file from a space. */
export function readCanonical(space: Space, repoPath: string): string {
  return readFileSync(join(spaceRoot(space), repoPath), 'utf8');
}

export function canonicalExists(space: Space, repoPath: string): boolean {
  return existsSync(join(spaceRoot(space), repoPath));
}

function kindFor(repoPath: string): PageKind {
  if (repoPath === 'playbook/GLOSSARY.md') return 'glossary';
  if (repoPath === 'playbook/references/SOURCES.md') return 'sources';
  if (repoPath === 'playbook/CHANGELOG.md') return 'changelog';
  return 'doc';
}

function groupFor(repoPath: string): PageDef['group'] {
  if (/^playbook\/(\d\d_.+|QUICKSTART)\.md$/.test(repoPath)) return 'book';
  if (repoPath.startsWith('playbook/templates/')) return 'templates';
  if (repoPath.startsWith('playbook/examples/')) return 'cases';
  if (repoPath.startsWith('playbook/references/')) return 'references';
  if (repoPath.startsWith('research/')) return 'research';
  return 'meta';
}

/** Reading order inside a group (drives prev/next). */
function orderFor(repoPath: string): number {
  const chapter = repoPath.match(/^playbook\/(\d\d)_/);
  if (repoPath === 'playbook/QUICKSTART.md') return -1;
  if (chapter) return Number(chapter[1]);
  const caseM = repoPath.match(/^playbook\/examples\/CASE-(\d+)_/);
  if (caseM) return Number(caseM[1]);
  const synthM = repoPath.match(/^playbook\/examples\/SYNTH-(\d+)_/);
  if (synthM) return 100 + Number(synthM[1]);
  if (repoPath.startsWith('playbook/examples/WALKTHROUGH')) return 200;
  if (repoPath === 'playbook/examples/README.md') return -1;
  if (repoPath === 'playbook/references/SOURCES.md') return 1;
  if (repoPath === 'playbook/references/STATISTICS_FORMULAS.md') return 2;
  if (repoPath === 'playbook/references/VENDOR_RECIPE_NOTES.md') return 3;
  if (repoPath === 'research/README.md') return -1;
  return 50;
}

/** All markdown files (repo-relative) that render as pages in a space. */
function listRepoPaths(space: Space): string[] {
  const root = spaceRoot(space);
  const out: string[] = [];
  const pushDir = (rel: string) => {
    const abs = join(root, rel);
    if (!existsSync(abs)) return;
    for (const name of readdirSync(abs)) {
      if (name.endsWith('.md')) out.push(`${rel}/${name}`);
    }
  };
  // playbook top level
  const pbAbs = join(root, 'playbook');
  for (const name of readdirSync(pbAbs)) {
    if (name.endsWith('.md')) out.push(`playbook/${name}`);
  }
  pushDir('playbook/templates');
  pushDir('playbook/references');
  pushDir('playbook/examples');
  if (space === null) pushDir('research'); // research is never versioned
  return out.sort();
}

/** Every page in a space. */
export function pagesInSpace(space: Space): PageDef[] {
  const out: PageDef[] = [
    // generated index over templates/ (the dir has no README of its own)
    {
      repoPath: 'playbook/templates',
      route: '/playbook/templates/',
      fullRoute: `${spacePrefix(space)}/playbook/templates/`,
      section: 'playbook',
      kind: 'templates-index',
      space,
      group: 'meta',
      order: 0,
    },
  ];
  for (const repoPath of listRepoPaths(space)) {
    const info = repoPathToRoute(repoPath);
    if (!info) continue;
    out.push({
      repoPath,
      route: info.route,
      fullRoute: spacePrefix(space) + info.route,
      section: info.section,
      kind: kindFor(repoPath),
      space,
      group: groupFor(repoPath),
      order: orderFor(repoPath),
    });
  }
  return out;
}

/** Every page across the current space and all materialized versions. */
export function allPages(): PageDef[] {
  const spaces: Space[] = [null, ...VERSIONS.map((v) => v.version)];
  return spaces.flatMap((s) => pagesInSpace(s));
}

/** Extract the document title from its first H1 line. */
export function titleOf(space: Space, repoPath: string): string {
  const text = readCanonical(space, repoPath);
  const m = text.match(/^#\s+(.+?)\s*$/m);
  if (m) return m[1]!;
  return repoPath.split('/').pop()!.replace(/\.md$/, '');
}
