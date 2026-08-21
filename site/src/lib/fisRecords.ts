/**
 * CASE files cite their source-project primary records as bare backticked
 * filenames (e.g. `R6_EXPERIMENT_CONTRACT.md` §6). The repository's explicit
 * path map (projects/fis/README.md) resolves those historical names to their
 * current homes, including two renames recorded there. We linkify a citation
 * ONLY when the resolved file actually exists in the repository — this exposes
 * relationships already encoded, and fabricates none.
 */
import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from './repo.ts';

/** Renames recorded in the projects/fis/README.md path map. */
const RENAMES: Record<string, string> = {
  'AI_SYSTEMS_LAB_MASTER_PLAN.md': 'PROJECT_PLAN.md',
  'EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md': 'PLAYBOOK_ADAPTATION.md',
};

let cached: Map<string, string> | null = null;

/** bare filename -> repo-relative path of the primary record */
export function fisRecordMap(): Map<string, string> {
  if (cached) return cached;
  const map = new Map<string, string>();
  const fisDir = join(REPO_ROOT, 'projects', 'fis');
  if (existsSync(fisDir)) {
    for (const name of readdirSync(fisDir)) {
      if (name.endsWith('.md')) map.set(name, `projects/fis/${name}`);
    }
  }
  const researchDir = join(REPO_ROOT, 'research');
  if (existsSync(researchDir)) {
    for (const name of readdirSync(researchDir)) {
      if (name.endsWith('.md') && name !== 'README.md') map.set(name, `research/${name}`);
    }
  }
  for (const [oldName, newName] of Object.entries(RENAMES)) {
    const target = `projects/fis/${newName}`;
    if (existsSync(join(REPO_ROOT, target))) map.set(oldName, target);
  }
  cached = map;
  return map;
}
