/**
 * Research catalog metadata. The reports themselves are frozen and carry no
 * frontmatter; their catalog row (what it is, extraction status) and standing
 * annotations live ONLY in research/README.md — parsed here, never invented.
 */
import { readCanonical } from './corpus.ts';
import { IS_DEV } from './dev.ts';

export interface ResearchCatalogRow {
  file: string;
  whatItIs: string;
  extractionStatus: string;
}

export interface ResearchCatalog {
  rows: ResearchCatalogRow[];
  /** raw markdown bullets from "## Standing annotations" */
  annotations: string[];
}

let cached: ResearchCatalog | null = null;

export function researchCatalog(): ResearchCatalog {
  if (cached && !IS_DEV) return cached;
  const src = readCanonical(null, 'research/README.md');
  const rows: ResearchCatalogRow[] = [];
  const rowRe = /^\|\s*\[([^\]]+)\]\([^)]+\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*$/gm;
  let m: RegExpExecArray | null;
  while ((m = rowRe.exec(src))) {
    rows.push({ file: m[1]!.trim(), whatItIs: m[2]!.trim(), extractionStatus: m[3]!.trim() });
  }
  const annotations: string[] = [];
  const annSection = src.split(/^## Standing annotations\s*$/m)[1];
  if (annSection) {
    for (const line of annSection.split('\n')) {
      const b = line.match(/^- (.+)$/);
      if (b) annotations.push(b[1]!.trim());
    }
  }
  cached = { rows, annotations };
  return cached;
}

export function catalogFor(fileName: string): {
  row: ResearchCatalogRow | null;
  annotations: string[];
} {
  const c = researchCatalog();
  return {
    row: c.rows.find((r) => r.file === fileName) ?? null,
    annotations: c.annotations.filter((a) => a.includes(fileName)),
  };
}
