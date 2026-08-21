/** Popover data: term definitions rendered from the canonical glossary. */
import type { APIRoute } from 'astro';
import { loadGlossary } from '../lib/glossary.ts';
import { makeCtx } from '../lib/rendering.ts';
import { renderFragment } from '../lib/markdown/render.ts';

export const GET: APIRoute = () => {
  const g = loadGlossary(null);
  const ctx = makeCtx(null, 'playbook/GLOSSARY.md', import.meta.env.BASE_URL);
  const out: Record<string, { term: string; html: string }> = {};
  for (const t of g.terms) {
    out[t.slug] = { term: t.term, html: renderFragment(t.defMarkdown, ctx) };
  }
  return new Response(JSON.stringify(out), {
    headers: { 'Content-Type': 'application/json' },
  });
};
