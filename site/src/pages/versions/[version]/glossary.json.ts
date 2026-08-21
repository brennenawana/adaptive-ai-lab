/** Popover data for historical spaces — rendered from that version's glossary. */
import type { APIRoute } from 'astro';
import { loadGlossary } from '../../../lib/glossary.ts';
import { makeCtx } from '../../../lib/rendering.ts';
import { renderFragment } from '../../../lib/markdown/render.ts';
import { VERSIONS } from '../../../lib/versions.ts';

export function getStaticPaths(): { params: { version: string } }[] {
  return VERSIONS.map((v) => ({ params: { version: v.version } }));
}

export const GET: APIRoute = ({ params }) => {
  const version = params.version!;
  const g = loadGlossary(version);
  const ctx = makeCtx(version, 'playbook/GLOSSARY.md', import.meta.env.BASE_URL);
  const out: Record<string, { term: string; html: string }> = {};
  for (const t of g.terms) {
    out[t.slug] = { term: t.term, html: renderFragment(t.defMarkdown, ctx) };
  }
  return new Response(JSON.stringify(out), {
    headers: { 'Content-Type': 'application/json' },
  });
};
