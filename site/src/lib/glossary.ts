/**
 * Parse playbook/GLOSSARY.md (per space) into structured terms.
 * Format (verified corpus-wide): H1, blockquote header, intro paragraphs,
 * a "Thematic index:" paragraph block, '---', then 101 uniform entries of
 * exactly one `### term` heading + one paragraph, '---', nav footer.
 */
import GithubSlugger from 'github-slugger';
import { readCanonical, type Space } from './corpus.ts';
import { IS_DEV } from './dev.ts';

export interface GlossaryTerm {
  term: string;
  slug: string;
  /** raw markdown of the definition paragraph */
  defMarkdown: string;
}

export interface GlossaryTheme {
  name: string;
  slugs: string[];
}

export interface Glossary {
  terms: GlossaryTerm[];
  themes: GlossaryTheme[];
  slugSet: Set<string>;
  /** intro paragraphs before the thematic index (raw markdown) */
  introMarkdown: string;
}

const cache = new Map<string, Glossary>();

export function loadGlossary(space: Space): Glossary {
  const key = space ?? '@current';
  const hit = IS_DEV ? undefined : cache.get(key);
  if (hit) return hit;

  const src = readCanonical(space, 'playbook/GLOSSARY.md');
  const slugger = new GithubSlugger();

  const terms: GlossaryTerm[] = [];
  const entryRe = /^### (.+)\n([\s\S]*?)(?=\n### |\n---\s*$|\n---\n)/gm;
  let m: RegExpExecArray | null;
  while ((m = entryRe.exec(src))) {
    const term = m[1]!.trim();
    terms.push({ term, slug: slugger.slug(term), defMarkdown: m[2]!.trim() });
  }

  // thematic index: lines like '**Measurement validity** — [a](#a) · [b](#b) …'
  const themes: GlossaryTheme[] = [];
  const themeRe = /\*\*([^*]+)\*\*\s*—\s*((?:\[[^\]]+\]\(#[^)]+\)(?:\s*·\s*)?)+)/g;
  const beforeEntries = src.slice(0, src.indexOf('\n### '));
  while ((m = themeRe.exec(beforeEntries))) {
    const slugs = [...m[2]!.matchAll(/\(#([^)]+)\)/g)].map((x) => x[1]!);
    themes.push({ name: m[1]!.trim(), slugs });
  }

  // intro: text between the header blockquote and the thematic index
  let introMarkdown = '';
  const bodyStart = src.indexOf('\n\n', src.indexOf('\n> '));
  const themIdx = src.indexOf('Thematic index');
  if (bodyStart > -1 && themIdx > bodyStart) {
    introMarkdown = src.slice(bodyStart, themIdx).trim().replace(/\n\n[^\n]*$/, '');
  }

  const g: Glossary = { terms, themes, slugSet: new Set(terms.map((t) => t.slug)), introMarkdown };
  cache.set(key, g);
  return g;
}
