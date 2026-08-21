/**
 * Load playbook/references/sources.yaml — the source ledger, the record of
 * record for every citation the playbook makes. SOURCES.md is generated from
 * this file by the playbook's own tool; the site renders the yaml directly.
 */
import { load as parseYaml } from 'js-yaml';
import { readCanonical, type Space } from './corpus.ts';
import { IS_DEV } from './dev.ts';

export interface SourceEntry {
  id: string;
  org: string;
  title: string;
  url: string | null;
  type: string;
  pub_date: string | null;
  last_verified: string | null;
  tool_version?: string | null;
  maturity: string;
  classification: 'FOLLOW' | 'ADAPT' | 'REFERENCE' | 'DEPRECATED' | 'CASE';
  evidence_strength: string;
  claims: string;
  chapters: string[];
  freshness: string;
  superseded_by: string | null;
  notes?: string | null;
}

export const CLASSIFICATION_ORDER = ['FOLLOW', 'ADAPT', 'REFERENCE', 'DEPRECATED', 'CASE'] as const;

export const CLASSIFICATION_BLURB: Record<string, string> = {
  FOLLOW: 'Adopt this recipe as written; validate only your project-specific parameters.',
  ADAPT: 'Sound core, but adapt it — parts are project-specific, stale, or need validation.',
  REFERENCE: 'Background evidence and context; not an executable recipe.',
  DEPRECATED: 'Superseded or no longer current — kept for the record, do not follow.',
  CASE: 'Internal case study — real project evidence curated into the playbook.',
};

const cache = new Map<string, SourceEntry[]>();

export function loadSources(space: Space): SourceEntry[] {
  const key = space ?? '@current';
  const hit = IS_DEV ? undefined : cache.get(key);
  if (hit) return hit;
  const raw = parseYaml(readCanonical(space, 'playbook/references/sources.yaml')) as {
    sources: SourceEntry[];
  };
  cache.set(key, raw.sources);
  return raw.sources;
}

export function ledgerIdSet(space: Space): Set<string> {
  return new Set(loadSources(space).map((s) => s.id));
}
