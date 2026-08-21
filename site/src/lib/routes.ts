/**
 * Single source of truth: canonical repository path -> site route.
 *
 * A "space" is either the current site ('' prefix, built from the working
 * tree) or a historical version ('/versions/<v>' prefix, built from the
 * git-materialized snapshot). The mapping below is space-relative; the same
 * page in another space differs only by prefix, which is what the version
 * selector relies on.
 */

/** kebab-case a canonical filename stem: "00_PRINCIPLES_AND_SCOPE" -> "00-principles-and-scope" */
export function fileSlug(stem: string): string {
  return stem.replace(/_/g, '-').toLowerCase();
}

export interface RouteInfo {
  /** Space-relative route, with leading + trailing slash, e.g. "/playbook/quickstart/". */
  route: string;
  /** Top-level site section the page belongs to. */
  section: 'playbook' | 'references' | 'cases' | 'changelog' | 'research';
}

/**
 * Map a repo-relative path (e.g. "playbook/03_EVALUATION_FOUNDATION.md") to
 * its space-relative site route. Returns null for files that are not rendered
 * as pages (VERSION, tools/, yaml — the ledger page renders from sources.yaml
 * but is addressed via SOURCES.md/sources.yaml both).
 */
export function repoPathToRoute(repoPath: string): RouteInfo | null {
  const p = repoPath.replace(/^\.\//, '');

  // ---- research/ (current space only; never versioned) ----
  if (p.startsWith('research/')) {
    const rest = p.slice('research/'.length);
    if (rest === 'README.md') return { route: '/research/', section: 'research' };
    const m = rest.match(/^(.+)\.md$/);
    if (m) return { route: `/research/${fileSlug(m[1]!)}/`, section: 'research' };
    return null;
  }

  if (!p.startsWith('playbook/')) return null;
  const rest = p.slice('playbook/'.length);

  // top-level playbook files
  if (rest === 'README.md') return { route: '/playbook/', section: 'playbook' };
  if (rest === 'QUICKSTART.md') return { route: '/playbook/quickstart/', section: 'playbook' };
  if (rest === 'GLOSSARY.md') return { route: '/playbook/glossary/', section: 'playbook' };
  if (rest === 'CHANGELOG.md') return { route: '/changelog/', section: 'changelog' };
  if (rest === 'VERSION') return null;

  const chapter = rest.match(/^(\d\d)_(.+)\.md$/);
  if (chapter) {
    return { route: `/playbook/${chapter[1]}-${fileSlug(chapter[2]!)}/`, section: 'playbook' };
  }

  if (rest === 'templates/' || rest === 'templates') {
    return { route: '/playbook/templates/', section: 'playbook' };
  }
  const template = rest.match(/^templates\/(.+)\.md$/);
  if (template) {
    return { route: `/playbook/templates/${fileSlug(template[1]!)}/`, section: 'playbook' };
  }

  if (rest === 'references/SOURCES.md' || rest === 'references/sources.yaml') {
    return { route: '/references/sources/', section: 'references' };
  }
  if (rest === 'references/STATISTICS_FORMULAS.md') {
    return { route: '/references/statistics-formulas/', section: 'references' };
  }
  if (rest === 'references/VENDOR_RECIPE_NOTES.md') {
    return { route: '/references/vendor-recipe-notes/', section: 'references' };
  }

  const example = rest.match(/^examples\/(.+)\.md$/);
  if (example) {
    const stem = example[1]!;
    if (stem === 'README') return { route: '/cases/', section: 'cases' };
    return { route: `/cases/${fileSlug(stem)}/`, section: 'cases' };
  }

  return null;
}

/** Prefix for a space: '' for current, '/versions/<v>' for a historical one. */
export function spacePrefix(version: string | null): string {
  return version ? `/versions/${version}` : '';
}

/** Full space-aware route for a repo path, or null if unrendered. */
export function routeInSpace(repoPath: string, version: string | null): string | null {
  const info = repoPathToRoute(repoPath);
  if (!info) return null;
  return spacePrefix(version) + info.route;
}
