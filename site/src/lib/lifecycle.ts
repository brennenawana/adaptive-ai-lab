/**
 * The playbook lifecycle as a navigation model for the visual map and the
 * per-chapter orientation strip. This is a NAVIGATION/LEARNING AID derived
 * from the playbook's own lifecycle line (playbook/README.md "The lifecycle")
 * — it is not an independent normative source.
 */

export interface LifecycleStage {
  name: string;
  desc: string;
  /** chapter numbers ('01'…) this stage maps to */
  chapters: string[];
}

export const STAGES: LifecycleStage[] = [
  {
    name: 'Decision context',
    desc: 'Turn a fuzzy request into a profile, a stated decision, and first actions.',
    chapters: ['01'],
  },
  {
    name: 'Execution-system definition',
    desc: 'Pin what “the same system” means; measure reproducibility boundaries before comparing anything.',
    chapters: ['02'],
  },
  {
    name: 'Trusted evaluation substrate',
    desc: 'Build the versioned eval with integrity gates and measured ceilings — before optimization.',
    chapters: ['03'],
  },
  {
    name: 'Experimental design',
    desc: 'Frozen contracts, MDE, consequence-bearing tolerances, INCONCLUSIVE as an outcome.',
    chapters: ['04'],
  },
  {
    name: 'Baseline & candidates',
    desc: 'Simplest credible baseline first; bounded candidate sets; runtime regimes, not winners.',
    chapters: ['05'],
  },
  {
    name: 'Failure diagnosis',
    desc: 'Classify observed failures in the canonical taxonomy; instrument defects first.',
    chapters: ['03', '07'],
  },
  {
    name: 'Evidence-selected intervention',
    desc: 'Climb the intervention ladder with diagnostic gates — retrieval/tools/routing before training.',
    chapters: ['07', '08', '09'],
  },
  {
    name: 'Performance & capacity',
    desc: 'Characterize serving performance and capacity fit against real constraints.',
    chapters: ['06'],
  },
  {
    name: 'Economics',
    desc: 'Rent vs buy vs API as a measured decision: demand ledgers and pre-committed triggers.',
    chapters: ['11'],
  },
  {
    name: 'Deployment',
    desc: 'Shadow and canary with restraint; rollback as a designed, rehearsed path.',
    chapters: ['10'],
  },
  {
    name: 'Observability & learning',
    desc: 'Telemetry floor for experimentation; harvest production evidence back into the eval (→ 03).',
    chapters: ['12'],
  },
];

/** Cross-cutting chapters that sit under/over the whole lifecycle. */
export const CROSS_CUTTING: { num: string; role: string }[] = [
  { num: '00', role: 'Normative core — the twelve principles and the rigor dial govern every stage' },
  { num: '13', role: 'Governance, provenance and security — instantiated at intake for Tier-3 work' },
  { num: '14', role: 'Every gate and checklist from 00–13, condensed for use during execution' },
];

/** Stage index for a chapter number, or -1 for cross-cutting chapters. */
export function stageForChapter(num: string): number {
  return STAGES.findIndex((s) => s.chapters[0] === num || s.chapters.includes(num));
}
