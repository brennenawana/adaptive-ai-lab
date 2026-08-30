# Research

Generic research and external evidence informing the Adaptive AI Systems Playbook.
This layer is **informative, never normative**: a research report changes nothing by
itself — it becomes method only through the promotion path below.

## What belongs here

Deep-research and evidence reports that would still matter if any single project
disappeared: vendor-methodology audits, statistical reviews, market/hardware
verification, methodology corroboration. Project-specific research (run to answer one
project's implementation question) lives with that project under `projects/<name>/`.

## Conventions

- **Naming:** `YYYY-MM-DD_Topic.md`, date = report date. Flat directory — no
  subdirectories until the corpus demands them.
- **Frozen on landing.** Reports are never edited after they land: living code and
  committed evidence may cite them **by line number** (e.g.
  `fis_platform/stats.py` and `artifacts/mstat_standing_facts.json` cite the
  2026-08-20 report's lines 66/84/94), so any reflow breaks machine-checked anchors.
  Corrections arrive as new dated reports or as annotations in this index.
- **Promotion path (research → rule):** report finding → adjudication row in
  `docs/playbook-development/EVIDENCE_MAP.md` (with FIS/project corroboration and an
  A–H class) → playbook chapter rule with evidence-strength label →
  `playbook/CHANGELOG.md` entry. External sources cited by the playbook are recorded
  in `playbook/references/sources.yaml` (the record of record).

## Reports

| Report | What it is | Extraction status |
|---|---|---|
| [2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md](2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md) | Adversarially-verified NVIDIA vendor-methodology audit: 14-stage lifecycle map, gap matrix, toolchain boundary, deprecation watchlist | Absorbed into playbook chapters 05/06/07/09/10/12 and `references/VENDOR_RECIPE_NOTES.md` |
| [2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md](2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md) | Methodology + statistics review (ICC/N_eff re-derivation, consequence-bearing tolerances), Aug-2026 hardware market verification, staged purchase triggers | Absorbed into playbook chapters 03/04/07/09/11/13; FIS-specific decisions re-anchored in `projects/fis/` living docs and `docs/COMPUTE_POLICY.md` |
| [2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.md](2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.md) | Deep-dive on compiling agent experience into evolved skills (WikiSkill arXiv:2608.27454, Karpathy LLM-Wiki gist, karpathy/autoresearch): evidence review, playbook gap analysis, MVP skill-evolution experiment proposal | Not yet adjudicated; candidate corroboration for ch. 07 ladder ordering pending the §8 MVP experiment |

## Standing annotations

- **HTML companion (2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.md):** that .md is an abstract; the full citable report is the sibling file `2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.html` (self-contained; cite by `#anchor` instead of line number; embeds a JSON claims index). Intentionally not linked from site-rendered markdown — the site corpus is markdown-only and its link validator would fail on an `.html` href.

- **SPRT caveat (2026-08-20 report):** its §2.3 gap-matrix retains two stale
  pre-correction rows suggesting SPRT-style sequential rules. Its own §2.2 /
  Appendix C corrections (and the playbook) govern — **SPRT was rejected.** Do not
  adopt §2.3 rows in isolation.
- Both reports cross-cite each other by bare sibling filename and must stay
  co-located in this directory.
- Historical citations elsewhere in the repository reference these files at their
  pre-2026-08 path `docs/research/<name>`; per the standing path-map rule those
  citations inside frozen/historical documents are intentionally not rewritten.
