/** Per-space render-context factory + rendered-doc cache. */
import GithubSlugger from 'github-slugger';
import { IS_DEV } from './dev.ts';
import { pagesInSpace, readCanonical, type Space } from './corpus.ts';
import { ledgerIdSet } from './sources.ts';
import { loadGlossary } from './glossary.ts';
import { VERSIONS } from './versions.ts';
import { renderDoc, type RenderCtx, type RenderedDoc } from './markdown/render.ts';

const ctxCache = new Map<string, Omit<RenderCtx, 'repoPath' | 'base'>>();

export function spaceCtx(space: Space): Omit<RenderCtx, 'repoPath' | 'base'> {
  const key = space ?? '@current';
  const hit = IS_DEV ? undefined : ctxCache.get(key);
  if (hit) return hit;

  const caseRoutes = new Map<string, string>();
  for (const p of pagesInSpace(space)) {
    const m = p.repoPath.match(/^playbook\/examples\/(SCENARIO-\d{2})_/);
    if (m) caseRoutes.set(m[1]!, p.route);
  }
  const gitRef = space === null ? 'main' : (VERSIONS.find((v) => v.version === space)?.commit ?? 'main');

  const ctx = {
    space,
    gitRef,
    ledgerIds: ledgerIdSet(space),
    caseRoutes,
    glossarySlugs: loadGlossary(space).slugSet,
  };
  ctxCache.set(key, ctx);
  return ctx;
}

export function makeCtx(space: Space, repoPath: string, base: string): RenderCtx {
  return {
    ...spaceCtx(space),
    repoPath,
    base,
    anchorAliases:
      repoPath === 'playbook/references/STATISTICS_FORMULAS.md' ? formularyAliases(space) : null,
  };
}

/**
 * Chapters link into the statistics formulary with anchors like `#icc` that
 * have no matching heading — a canonical-source defect (those links are broken
 * on GitHub too; the playbook validator only checks glossary anchors). The
 * site derives an alias for each such incoming fragment: fragment tokens must
 * appear in order as prefixes of the heading-slug tokens; ambiguity resolves
 * to the shallowest, earliest heading; no match -> no alias (still reported
 * broken by the site's link validator). One manual entry is kept where token
 * matching cannot bridge canonical shorthand (`pass@k` ↔ `pass-at-k`).
 */
const aliasCache = new Map<string, Map<string, string>>();

function formularyAliases(space: Space): Map<string, string> {
  const key = space ?? '@current';
  const hit = IS_DEV ? undefined : aliasCache.get(key);
  if (hit) return hit;

  // headings + slugs of the formulary, in document order
  const src = readCanonical(space, 'playbook/references/STATISTICS_FORMULAS.md');
  const slugger = new GithubSlugger();
  const headings: { depth: number; slug: string; tokens: string[] }[] = [];
  for (const m of src.matchAll(/^(#{1,4})\s+(.+?)\s*$/gm)) {
    const slug = slugger.slug(m[2]!);
    headings.push({ depth: m[1]!.length, slug, tokens: slug.split('-').filter(Boolean) });
  }
  const slugSet = new Set(headings.map((h) => h.slug));

  // incoming fragments: every link to the formulary anywhere in this space
  const fragments = new Set<string>();
  for (const p of pagesInSpace(space)) {
    if (p.kind !== 'doc' && p.kind !== 'glossary') continue;
    if (p.repoPath === 'playbook/templates') continue;
    const text = readCanonical(space, p.repoPath);
    for (const m of text.matchAll(/STATISTICS_FORMULAS\.md#([A-Za-z0-9-]+)/g)) {
      fragments.add(m[1]!.toLowerCase());
    }
  }

  const matches = (frag: string, h: { tokens: string[] }): boolean => {
    const ft = frag.split('-').filter(Boolean);
    let i = 0;
    for (const t of ft) {
      while (i < h.tokens.length && !h.tokens[i]!.startsWith(t)) i++;
      if (i === h.tokens.length) return false;
      i++;
    }
    return true;
  };

  const out = new Map<string, string>();
  for (const frag of fragments) {
    if (slugSet.has(frag)) continue; // resolves natively
    const candidates = headings.filter((h) => matches(frag, h));
    if (candidates.length === 0) continue;
    const minDepth = Math.min(...candidates.map((c) => c.depth));
    out.set(frag, candidates.find((c) => c.depth === minDepth)!.slug);
  }
  // canonical shorthand `pass@k` slugs to `passk` — token matching cannot see it;
  // §8 is the formulary's only pass@k section (verified against the source)
  const passk = headings.find((h) => h.slug.includes('passk'));
  if (!out.has('pass-at-k-vs-pass-to-the-k') && passk && !slugSet.has('pass-at-k-vs-pass-to-the-k')) {
    out.set('pass-at-k-vs-pass-to-the-k', passk.slug);
  }
  aliasCache.set(key, out);
  return out;
}

const docCache = new Map<string, RenderedDoc>();

/** Render (with caching) a canonical file in a space. */
export function renderCanonicalDoc(space: Space, repoPath: string, base: string): RenderedDoc {
  const key = `${space ?? '@current'}:${repoPath}:${base}`;
  const hit = IS_DEV ? undefined : docCache.get(key);
  if (hit) return hit;
  const doc = renderDoc(readCanonical(space, repoPath), makeCtx(space, repoPath, base));
  docCache.set(key, doc);
  return doc;
}
