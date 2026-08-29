/**
 * Canonical-Markdown -> HTML pipeline.
 *
 * Renders repository files (chapters, templates, scenarios, glossary…)
 * with presentation-layer enhancements that bind ONLY to explicit source
 * semantics discovered in the corpus:
 *   - badge callouts:  **[PRINCIPLE] …**, [STOP CONDITION], [DECISION GATE], …
 *   - doctrine marker: `status: doctrine — not yet exercised`
 *   - citation tokens: [EXT-…-NNN] / [NV-…] / [SCENARIO: SCENARIO-NN]
 *     linkified only when the ID exists in references/sources.yaml (the record
 *     of record) — unknown tokens are left as literal text
 *   - glossary links (GLOSSARY.md#term) get popover affordances
 *   - internal links rewritten to site routes; links to unrendered repo files
 *     become canonical GitHub links (at the exact commit for historical spaces)
 *
 * The pipeline never alters canonical prose: no reflow, no math pass, no
 * syntax-highlighting guesses (all corpus fences are bare ASCII/unicode
 * diagrams and formulas), no smart typography.
 */
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import { visit, SKIP } from 'unist-util-visit';
import { toString as mdToString } from 'mdast-util-to-string';
import GithubSlugger from 'github-slugger';
import { posix } from 'node:path';
import type { Root as MdastRoot, RootContent as MdastContent } from 'mdast';
import type { Root as HastRoot, Element, ElementContent, Text as HastText } from 'hast';

import { repoPathToRoute, spacePrefix } from '../routes.ts';
import type { Space } from '../corpus.ts';

export interface RenderCtx {
  space: Space;
  /** repo-relative path of the file being rendered */
  repoPath: string;
  /** site base path, always ending in '/' (import.meta.env.BASE_URL) */
  base: string;
  /** git ref for canonical-source links: 'main' or the version's commit */
  gitRef: string;
  /** all known source-ledger IDs for this space */
  ledgerIds: ReadonlySet<string>;
  /** SCENARIO-NN -> space-relative route */
  caseRoutes: ReadonlyMap<string, string>;
  /** valid glossary anchor slugs for this space */
  glossarySlugs: ReadonlySet<string>;
  /** optional collector for link validation */
  collectLink?: (targetRepoPath: string, anchor: string | null, from: string) => void;
  /**
   * Presentation-layer anchor aliases: fragment -> existing heading slug.
   * Used where canonical links cite anchors that have no matching heading in
   * the target file (a canonical-source defect, broken on GitHub as well) —
   * the site lands the reader on the derived-matching heading instead.
   */
  anchorAliases?: ReadonlyMap<string, string> | null;
}

export interface TocEntry {
  depth: number;
  text: string;
  slug: string;
}

export interface DocMeta {
  /** e.g. "~25 min" (chapters) */
  readingTime?: string;
  /** rendered inline HTML fragment */
  prerequisites?: string;
  /** templates: rendered "Governing chapter: …" fragment */
  governingChapter?: string;
  /** templates: rendered purpose lede from the header blockquote */
  templateLede?: string;
  /** SYNTH files: the italic synthetic disclaimer, rendered */
  synthDisclaimer?: string;
}

export interface RenderedDoc {
  html: string;
  title: string | null;
  toc: TocEntry[];
  meta: DocMeta;
}

/* ------------------------------------------------------------------ */
/* helpers                                                            */
/* ------------------------------------------------------------------ */

const NAV_LINK_TEXT = /^(?:← Previous|Index|Next →|Glossary|Examples|Quickstart|Principles|00 — Principles)$/;

function joinBase(base: string, route: string): string {
  return base.replace(/\/$/, '') + route;
}

function el(tagName: string, properties: Record<string, unknown>, children: ElementContent[] = []): Element {
  return { type: 'element', tagName, properties: properties as Element['properties'], children };
}

function text(value: string): HastText {
  return { type: 'text', value };
}

/** Is this blockquote pure navigation/header chrome? */
function isNavBlockquote(node: MdastContent): boolean {
  if (node.type !== 'blockquote') return false;
  const raw = mdToString(node);
  if (raw.includes('Part of the')) return true;
  if (raw.startsWith('Index:')) return true; // templates header
  // nav-only line(s): every link is a nav label and there is little other text
  const links: string[] = [];
  visit(node as never, 'link', (l: { children?: unknown[] }) => {
    links.push(mdToString(l as never));
  });
  if (links.length === 0) return false;
  const navLinks = links.filter((t) => NAV_LINK_TEXT.test(t));
  const residue = raw
    .replace(/·/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  const linkChars = links.join('').length;
  return navLinks.length >= 1 && residue.length - linkChars < 20;
}

/* ------------------------------------------------------------------ */
/* mdast stage: structure extraction                                  */
/* ------------------------------------------------------------------ */

interface Extracted {
  title: string | null;
  headerRawSlices: string[]; // raw markdown of removed leading chrome
}

function extractStructure(tree: MdastRoot, source: string, ctx: RenderCtx): Extracted {
  const out: Extracted = { title: null, headerRawSlices: [] };
  const kids = tree.children;

  // title = first H1
  if (kids[0]?.type === 'heading' && kids[0].depth === 1) {
    out.title = mdToString(kids[0]);
    kids.shift();
  }

  const isSynth = /^playbook\/examples\/SYNTH-\d+_/.test(ctx.repoPath);

  {
    // strip leading nav/header blockquotes (chapters, glossary, quickstart,
    // README, CHANGELOG, templates, examples index, walkthrough, synth)
    while (kids.length && isNavBlockquote(kids[0]!)) {
      const n = kids.shift()!;
      const s = n.position ? source.slice(n.position.start.offset!, n.position.end.offset!) : '';
      out.headerRawSlices.push(s);
    }
    // templates: a header blockquote may carry a purpose lede + "Index: …
    // Governing chapter: …" and may not be the very first node
    if (ctx.repoPath.startsWith('playbook/templates/')) {
      for (let i = 0; i < Math.min(kids.length, 3); i++) {
        const n = kids[i]!;
        if (n.type === 'blockquote') {
          const t = mdToString(n);
          if (t.includes('Index:') && t.includes('Governing chapter')) {
            const s = n.position ? source.slice(n.position.start.offset!, n.position.end.offset!) : '';
            out.headerRawSlices.push(s);
            kids.splice(i, 1);
            break;
          }
        }
      }
    }
    if (isSynth || ctx.repoPath.startsWith('playbook/examples/WALKTHROUGH')) {
      // italic synthetic-disclaimer paragraph
      const first = kids[0];
      if (
        first?.type === 'paragraph' &&
        first.children.length === 1 &&
        first.children[0]!.type === 'emphasis' &&
        /^Synthetic worked example/.test(mdToString(first))
      ) {
        const s = first.position ? source.slice(first.position.start.offset!, first.position.end.offset!) : '';
        out.headerRawSlices.push(s);
        kids.shift();
        if (kids[0]?.type === 'thematicBreak') kids.shift();
      }
    }
  }

  // strip trailing footer nav: [--- , blockquote(nav)] or just blockquote(nav)
  while (kids.length) {
    const last = kids[kids.length - 1]!;
    if (isNavBlockquote(last)) {
      kids.pop();
      continue;
    }
    if (last.type === 'thematicBreak' && kids.length >= 2 && isNavBlockquote(kids[kids.length - 2]!)) {
      // unusual order; handled by loop
      kids.pop();
      continue;
    }
    if (last.type === 'thematicBreak' && kids.length >= 1) {
      // a '---' immediately preceding a removed footer blockquote
      const removedFooter = out; // we only strip the hr if we already removed a nav bq this pass
      void removedFooter;
      break;
    }
    break;
  }
  // if the new last node is a thematic break left over from a removed footer, drop it
  if (kids.length && kids[kids.length - 1]!.type === 'thematicBreak') {
    kids.pop();
  }

  // raw HTML never exists in the corpus; render literal text for safety
  visit(tree as never, 'html', (node: { type: string; value?: string }) => {
    node.type = 'text';
  });

  return out;
}

/* ------------------------------------------------------------------ */
/* hast stage: links, tokens, badges, headings, tables                */
/* ------------------------------------------------------------------ */

/** Resolve a markdown link target to a site href. */
function resolveHref(
  target: string,
  ctx: RenderCtx,
): { href: string; cls?: string[]; data?: Record<string, string>; external?: boolean } {
  if (/^(https?:)?\/\//.test(target) || target.startsWith('mailto:')) {
    return { href: target, cls: ['ext'], external: true };
  }
  const [pathPart, anchorPart] = target.split('#', 2) as [string, string?];
  const anchor = anchorPart ? `#${anchorPart}` : '';
  if (!pathPart) return { href: anchor || '#' };

  const dir = posix.dirname(ctx.repoPath);
  const resolved = posix.normalize(posix.join(dir, pathPart));

  ctx.collectLink?.(resolved, anchorPart ?? null, ctx.repoPath);

  const info = repoPathToRoute(resolved);
  if (info) {
    const href = joinBase(ctx.base, spacePrefix(ctx.space) + info.route) + anchor;
    if (resolved === 'playbook/GLOSSARY.md' && anchorPart && ctx.glossarySlugs.has(anchorPart)) {
      return { href, cls: ['gloss'], data: { 'data-term': anchorPart } };
    }
    return { href };
  }
  // A repository file that is not published as a page. The standalone site has
  // no repository to point at, so the link text is kept and the link is dropped.
  return { href: '', cls: ['unlinked'] };
}

const TOKEN_RE =
  /\[(FOLLOW|ADAPT|REFERENCE|DEPRECATED|SCENARIO):\s*([A-Z0-9-]+)\]|\[((?:NV|EXT|INT)-[A-Z0-9-]*\d{3}[A-C]?)\]/g;

/** Linkify citation/case tokens inside a text node; returns replacement nodes or null. */
function linkifyTokens(value: string, ctx: RenderCtx): ElementContent[] | null {
  TOKEN_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  const parts: ElementContent[] = [];
  let last = 0;
  const sourcesRoute = joinBase(ctx.base, spacePrefix(ctx.space) + '/references/sources/');
  while ((m = TOKEN_RE.exec(value))) {
    const [full, verdict, verdictId, bareId] = m;
    let node: ElementContent | null = null;
    if (verdict && verdictId) {
      if (verdictId.startsWith('SCENARIO-') && ctx.caseRoutes.has(verdictId)) {
        node = el(
          'a',
          {
            href: joinBase(ctx.base, spacePrefix(ctx.space) + ctx.caseRoutes.get(verdictId)!),
            className: ['token', 'token-case'],
            title: `Scenario ${verdictId}`,
          },
          [text(full)],
        );
      } else if (ctx.ledgerIds.has(verdictId)) {
        node = el(
          'a',
          {
            href: `${sourcesRoute}#${verdictId.toLowerCase()}`,
            className: ['token', 'token-src', `token-${verdict.toLowerCase()}`],
            title: `Source ${verdictId} — verdict ${verdict}`,
          },
          [text(full)],
        );
      }
    } else if (bareId && ctx.ledgerIds.has(bareId)) {
      node = el(
        'a',
        {
          href: `${sourcesRoute}#${bareId.toLowerCase()}`,
          className: ['token', 'token-src'],
          title: `Source ${bareId}`,
        },
        [text(full)],
      );
    }
    if (node) {
      if (m.index > last) parts.push(text(value.slice(last, m.index)));
      parts.push(node);
      last = m.index + full.length;
    }
  }
  if (parts.length === 0) return null;
  if (last < value.length) parts.push(text(value.slice(last)));
  return parts;
}

const BADGE_KINDS: Record<string, string> = {
  PRINCIPLE: 'principle',
  'DECISION GATE': 'gate',
  'STOP CONDITION': 'stop',
  DEFAULT: 'default',
  PARAMETER: 'parameter',
  REJECTED: 'rejected',
  FOLLOW: 'vendor',
  ADAPT: 'vendor',
  REFERENCE: 'vendor',
};
const BADGE_RE = /^\[(PRINCIPLE|DECISION GATE|STOP CONDITION|DEFAULT|PARAMETER|REJECTED|FOLLOW|ADAPT|REFERENCE)\]\s?/;

/** If a <strong> starts with a badge token, replace it with a styled chip; return kind. */
function chipifyStrong(strong: Element): string | null {
  const first = strong.children[0];
  if (!first || first.type !== 'text') return null;
  const m = first.value.match(BADGE_RE);
  if (!m) return null;
  const kind = BADGE_KINDS[m[1]!]!;
  const rest = first.value.slice(m[0].length);
  const chip = el('span', { className: ['badge-chip', `chip-${kind}`, `chip-${m[1]!.toLowerCase().replace(/ /g, '-')}`] }, [
    text(m[1]!),
  ]);
  const newChildren: ElementContent[] = [chip];
  if (rest) newChildren.push(text(rest.length && !rest.startsWith(' ') ? ` ${rest}` : rest));
  strong.children = [...newChildren, ...strong.children.slice(1)];
  return kind;
}

function isTag(n: ElementContent | undefined, tag: string): n is Element {
  return !!n && n.type === 'element' && n.tagName === tag;
}

function transformHast(tree: HastRoot, ctx: RenderCtx): TocEntry[] {
  const slugger = new GithubSlugger();
  const toc: TocEntry[] = [];

  /* -- links -- */
  visit(tree, 'element', (node: Element) => {
    if (node.tagName !== 'a') return;
    const href = node.properties?.href;
    if (typeof href !== 'string') return;
    const r = resolveHref(href, ctx);
    node.properties!.href = r.href;
    if (r.cls) {
      const existing = Array.isArray(node.properties!.className) ? (node.properties!.className as string[]) : [];
      node.properties!.className = [...existing, ...r.cls];
    }
    if (r.data) Object.assign(node.properties!, r.data);
    if (r.external) {
      node.properties!.rel = ['noopener'];
    }
  });

  /* -- citation tokens in text (outside code/links) -- */
  visit(tree, 'element', (node: Element, _index, parent) => {
    if (node.tagName === 'code' || node.tagName === 'pre' || node.tagName === 'a') return SKIP;
    void parent;
    for (let i = 0; i < node.children.length; i++) {
      const child = node.children[i]!;
      if (child.type === 'text') {
        const repl = linkifyTokens(child.value, ctx);
        if (repl) {
          node.children.splice(i, 1, ...repl);
          i += repl.length - 1;
        }
      }
    }
  });

  /* -- badge chips + callout wrapping (top level and blockquotes) -- */
  const wrapCallouts = (children: ElementContent[]) => {
    for (let i = 0; i < children.length; i++) {
      const raw = children[i]!;
      if (raw.type !== 'element' || (raw.tagName !== 'p' && raw.tagName !== 'blockquote')) continue;
      const node: Element = raw;
      if (node.tagName === 'blockquote') {
        // badge inside the first paragraph of a blockquote -> class the quote
        const firstP = (node.children as ElementContent[]).find((c) => isTag(c, 'p'));
        if (firstP && isTag(firstP, 'p')) {
          const firstStrong = (firstP.children as ElementContent[]).find((c) => isTag(c, 'strong'));
          if (firstStrong && isTag(firstStrong, 'strong') && firstP.children.indexOf(firstStrong) <= 1) {
            const kind = chipifyStrong(firstStrong);
            if (kind) {
              node.properties = node.properties ?? {};
              node.properties.className = ['callout', kind];
            }
          }
        }
        continue;
      }
      // paragraph starting with a badge strong -> wrap in a callout div
      const p = node;
      const firstChild = (p.children as ElementContent[])[0];
      if (isTag(firstChild, 'strong')) {
        const kind = chipifyStrong(firstChild);
        if (kind) {
          children[i] = el('div', { className: ['callout', kind] }, [p]);
          continue;
        }
      }
      // italic doctrine line -> doctrine callout
      if (
        isTag(firstChild, 'em') &&
        p.children.length === 1 &&
        hastTextContent(firstChild).startsWith('status: doctrine')
      ) {
        children[i] = el('div', { className: ['callout', 'doctrine'] }, [p]);
      }
    }
  };
  wrapCallouts(tree.children as ElementContent[]);
  // also chipify badge strongs inside list items (chip only, no box)
  visit(tree, 'element', (node: Element) => {
    if (node.tagName !== 'li') return;
    visit(node, 'element', (inner: Element) => {
      if (inner.tagName === 'strong') chipifyStrong(inner);
    });
    return SKIP;
  });

  /* -- doctrine inline code chip -- */
  visit(tree, 'element', (node: Element) => {
    if (node.tagName !== 'code') return;
    const t = hastTextContent(node);
    if (t.startsWith('status: doctrine')) {
      node.properties = node.properties ?? {};
      node.properties.className = ['doctrine-chip'];
    }
  });

  /* -- headings: ids + anchors + toc -- */
  visit(tree, 'element', (node: Element) => {
    if (!/^h[1-4]$/.test(node.tagName)) return;
    const depth = Number(node.tagName[1]);
    const txt = hastTextContent(node);
    const slug = slugger.slug(txt);
    node.properties = node.properties ?? {};
    node.properties.id = slug;
    if (ctx.anchorAliases) {
      for (const [frag, target] of ctx.anchorAliases) {
        if (target === slug) {
          node.children.unshift(el('span', { id: frag, className: ['anchor-alias'] }, []));
        }
      }
    }
    if (depth >= 2) {
      toc.push({ depth, text: txt, slug });
      node.children.push(
        el(
          'a',
          {
            className: ['heading-anchor'],
            href: `#${slug}`,
            'aria-label': `Link to “${txt}”`,
            'data-pagefind-ignore': 'all',
          },
          [text('#')],
        ),
      );
    }
  });

  /* -- code fences: ascii diagrams & mermaid -- */
  visit(tree, 'element', (node: Element) => {
    if (node.tagName !== 'pre') return;
    const code = node.children.find((c) => isTag(c, 'code'));
    if (!code || !isTag(code, 'code')) return;
    const cls = (code.properties?.className as string[] | undefined) ?? [];
    if (cls.includes('language-mermaid')) {
      node.tagName = 'pre';
      node.properties = { className: ['mermaid'] };
      node.children = [text(hastTextContent(code))];
      return;
    }
    const content = hastTextContent(code);
    if (/[│▼►├└┌┐┘┤┬┴↺]|──|→/.test(content)) {
      node.properties = node.properties ?? {};
      node.properties.className = ['ascii-diagram'];
    }
  });

  /* -- tables: scroll wrapper -- */
  visit(tree, 'element', (node: Element, index, parent) => {
    if (node.tagName !== 'table' || index === undefined || !parent) return;
    if (isTag(parent as ElementContent, 'div')) {
      const p = parent as Element;
      const pc = p.properties?.className as string[] | undefined;
      if (pc?.includes('table-scroll')) return;
    }
    (parent as Element | HastRoot).children[index] = el('div', { className: ['table-scroll'] }, [node]);
    return SKIP;
  });

  return toc;
}

function hastTextContent(node: Element): string {
  let out = '';
  visit(node, 'text', (t: HastText) => {
    out += t.value;
  });
  return out;
}

/* ------------------------------------------------------------------ */
/* public API                                                         */
/* ------------------------------------------------------------------ */

const parser = unified().use(remarkParse).use(remarkGfm);
const toHast = unified().use(remarkRehype, { allowDangerousHtml: false });
const stringifier = unified().use(rehypeStringify);

/** Render a markdown fragment (no structure extraction) to inline-safe HTML. */
export function renderFragment(markdown: string, ctx: RenderCtx): string {
  const mdast = parser.parse(markdown) as MdastRoot;
  visit(mdast as never, 'html', (node: { type: string }) => {
    node.type = 'text';
  });
  const hast = toHast.runSync(mdast) as HastRoot;
  transformHast(hast, ctx);
  return stringifier.stringify(hast) as string;
}

/** Strip outer <p> wrapper from a rendered one-paragraph fragment. */
export function renderInlineFragment(markdown: string, ctx: RenderCtx): string {
  const html = renderFragment(markdown, ctx).trim();
  const m = html.match(/^<p>([\s\S]*)<\/p>$/);
  return m ? m[1]! : html;
}

function parseChapterHeaderMeta(rawSlices: string[], ctx: RenderCtx, meta: DocMeta): void {
  const raw = rawSlices.join('\n').replace(/^> ?/gm, '');
  const rt = raw.match(/\*\*Reading time:\*\*\s*(~?\d+\s*min)/);
  if (rt) meta.readingTime = rt[1]!;
  const prereq = raw.match(/\*\*Prerequisites:\*\*\s*([\s\S]+?)(?:\n\n|$)/);
  if (prereq) {
    meta.prerequisites = renderInlineFragment(prereq[1]!.replace(/\s+/g, ' ').trim(), ctx);
  }
  const gov = raw.match(/Governing chapter:\s+([\s\S]+?)\s*$/);
  if (gov) {
    meta.governingChapter = renderInlineFragment(gov[1]!.replace(/\s+/g, ' ').trim(), ctx);
  }
  // template purpose lede: blockquote text before the "Index:" line
  const idxPos = raw.indexOf('Index:');
  if (idxPos > 0 && raw.includes('Governing chapter')) {
    const lede = raw.slice(0, idxPos).replace(/\s+/g, ' ').trim();
    if (lede) meta.templateLede = renderInlineFragment(lede, ctx);
  }
}

/** Render a full canonical document. */
export function renderDoc(source: string, ctx: RenderCtx): RenderedDoc {
  const mdast = parser.parse(source) as MdastRoot;
  const extracted = extractStructure(mdast, source, ctx);

  const meta: DocMeta = {};
  if (extracted.headerRawSlices.length) {
    parseChapterHeaderMeta(extracted.headerRawSlices, ctx, meta);
    const synth = extracted.headerRawSlices.find((s) => s.includes('Synthetic worked example'));
    if (synth) meta.synthDisclaimer = renderInlineFragment(synth.replace(/^\*|\*$/g, ''), ctx);
  }

  const hast = toHast.runSync(mdast) as HastRoot;
  const toc = transformHast(hast, ctx);
  const html = stringifier.stringify(hast) as string;

  return { html, title: extracted.title, toc, meta };
}
