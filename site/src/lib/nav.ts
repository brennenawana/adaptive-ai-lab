/** Sidebar/topnav models, derived from the corpus — never hand-duplicated. */
import { pagesInSpace, titleOf, type PageDef, type Space } from './corpus.ts';
import { spacePrefix } from './routes.ts';
import { IS_DEV } from './dev.ts';

export interface NavItem {
  label: string;
  route: string; // space-relative
  fullRoute: string;
  /** small leading tag, e.g. chapter number or CASE id */
  tag?: string;
}

export interface NavGroup {
  title: string | null;
  items: NavItem[];
}

const cache = new Map<string, Map<string, NavGroup[]>>();

function labelFor(p: PageDef, space: Space): { label: string; tag?: string } {
  const t = titleOf(space, p.repoPath);
  const ch = t.match(/^(\d\d)\.\s+(.+)$/);
  if (ch) return { label: ch[2]!, tag: ch[1]! };
  const cs = t.match(/^(CASE-\d{3}|SYNTH-\d{2}):?\s+(.+)$/);
  if (cs) return { label: cs[2]!, tag: cs[1]! };
  return { label: t };
}

function item(p: PageDef, space: Space): NavItem {
  const { label, tag } = labelFor(p, space);
  return { label, tag, route: p.route, fullRoute: p.fullRoute };
}

/** Sidebar groups per site section, for one space. */
export function sidebarFor(section: string, space: Space): NavGroup[] {
  const key = space ?? '@current';
  let bySection = IS_DEV ? undefined : cache.get(key);
  if (!bySection) {
    bySection = buildSidebars(space);
    cache.set(key, bySection);
  }
  return bySection.get(section) ?? [];
}

function buildSidebars(space: Space): Map<string, NavGroup[]> {
  const pages = pagesInSpace(space);
  const by = (pred: (p: PageDef) => boolean) =>
    pages.filter(pred).sort((a, b) => a.order - b.order || a.repoPath.localeCompare(b.repoPath));

  const pre = spacePrefix(space);

  const playbook: NavGroup[] = [
    {
      title: null,
      items: [
        { label: 'The Playbook', route: '/playbook/', fullRoute: `${pre}/playbook/` },
        ...by((p) => p.repoPath === 'playbook/QUICKSTART.md').map((p) => item(p, space)),
      ],
    },
    {
      title: 'The book',
      items: by((p) => /^playbook\/\d\d_/.test(p.repoPath)).map((p) => item(p, space)),
    },
    {
      title: 'Templates',
      items: by((p) => p.group === 'templates').map((p) => item(p, space)),
    },
    {
      title: 'Reference',
      items: [
        { label: 'Glossary', route: '/playbook/glossary/', fullRoute: `${pre}/playbook/glossary/` },
        { label: 'Changelog', route: '/changelog/', fullRoute: `${pre}/changelog/` },
      ],
    },
  ];

  const references: NavGroup[] = [
    {
      title: 'References',
      items: [
        { label: 'Source ledger', route: '/references/sources/', fullRoute: `${pre}/references/sources/` },
        ...by((p) => p.repoPath === 'playbook/references/STATISTICS_FORMULAS.md').map((p) => item(p, space)),
        ...by((p) => p.repoPath === 'playbook/references/VENDOR_RECIPE_NOTES.md').map((p) => item(p, space)),
      ],
    },
  ];

  const cases: NavGroup[] = [
    {
      title: null,
      items: by((p) => p.repoPath === 'playbook/examples/README.md').map((p) => ({
        ...item(p, space),
        label: 'Case library',
      })),
    },
    {
      title: 'Scenarios — illustrated lessons',
      items: by((p) => /SCENARIO-\d+_/.test(p.repoPath)).map((p) => item(p, space)),
    },
    {
      title: 'Synthetic worked examples',
      items: by((p) => /SYNTH-\d+_/.test(p.repoPath)).map((p) => item(p, space)),
    },
    {
      title: 'Walkthrough',
      items: by((p) => p.repoPath.includes('WALKTHROUGH')).map((p) => item(p, space)),
    },
  ];

  return new Map<string, NavGroup[]>([
    ['playbook', playbook],
    ['references', references],
    ['cases', cases],
    ['changelog', playbook],
  ]);
}

/** Ordered reading sequence for prev/next within a group. */
export function readingSequence(space: Space, group: PageDef['group']): PageDef[] {
  return pagesInSpace(space)
    .filter((p) => p.group === group)
    .sort((a, b) => a.order - b.order || a.repoPath.localeCompare(b.repoPath));
}

export function prevNext(page: PageDef): { prev: NavItem | null; next: NavItem | null } {
  const seq = readingSequence(page.space, page.group);
  const i = seq.findIndex((p) => p.repoPath === page.repoPath);
  if (i === -1) return { prev: null, next: null };
  const prev = i > 0 ? item(seq[i - 1]!, page.space) : null;
  const next = i < seq.length - 1 ? item(seq[i + 1]!, page.space) : null;
  return { prev, next };
}
