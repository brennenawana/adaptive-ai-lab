# Compiled Experience: WikiSkill, the LLM Wiki, and autoresearch (abstract)

**Date:** 2026-08-30 · **Status:** informative, never normative · **Extraction status:** not yet adjudicated

This is the site-renderable abstract of a full HTML report that lives beside this file as
`research/2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.html` (open it directly in a browser;
it is deliberately not routed through the site, whose corpus is markdown-only). The HTML
report is the citable artifact — cite it by anchor, e.g.
`2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.html#ws-ablation` — and it embeds a
machine-readable claims index (`<script id="claims-index">`) for agent ingestion.

## What the report is

A deep-dive into three sources, read in full on 2026-08-30, on compiling agent experience
into persistent knowledge and evolved skills — "fine-tuning without touching the weights":

1. **WikiSkill** (Tang et al., Google Research, arXiv:2608.27454, 27 Aug 2026) — a
   framework co-evolving agent skills with a persistent wiki; evaluated across five
   models and five benchmarks, including full appendices and verbatim agent prompts.
2. **Karpathy's "LLM Wiki" gist** — the idea file the paper credits: knowledge compiled
   once into a compounding wiki, not re-derived per query (raw / wiki / schema layers).
3. **karpathy/autoresearch** (March 2026) — the minimal autonomous-improvement harness:
   three files, one metric, keep/discard gating; 83 overnight experiments, 15 kept.

## Findings in brief

- Evolved markdown skills lift task accuracy without weight updates across all five
  models; a 9B model with skills beats a 27B model without (47.4% vs 39.4% average).
- Gains **grow** with executor capability (+12.3/+17.5/+23.9 points for Qwen 4B/9B/27B) —
  the folk claim "skills help small models most" is backwards; the real economics are
  substitution (cheap model + skills does big-model work) plus cross-model transfer.
- Skill discovery and skill execution are distinct capabilities: transferred skills often
  beat self-evolved ones; there is a capability floor and a documented negative-transfer
  mode (model-specific workarounds crater stronger executors, 50.5% → 18.1% worst case).
- The single most valuable mechanism is the **persistent wiki** feeding the skill
  proposer: +15.0 points on its own in ablation (48.7% → 63.7%, Gemini-3.5-Flash across
  four benchmarks); letting the *executor* read the wiki during training makes final
  skills worse (63.7% → 60.9%).
- Optimizer overhead is O(1) per iteration (1 consolidation call + a 10–20-turn ReAct
  proposer); training splits were 16–80 tasks. The loop is cheap; rollouts dominate.
- The repo already practices halves of this by hand (wholesaling compiled BRIEFs,
  PreCompact knowledge flush, ch. 12 failure harvesting, millwork "skills as
  experimental objects"); what is missing is agent-facing consolidated knowledge and any
  gated closed loop. WikiSkill is the cleanest external corroboration yet for the
  ch. 07 intervention-ladder ordering (rungs 2/4 before 7/8).

## Proposal carried by the report (informative only)

A karpathy-scale MVP (§8 of the HTML report): three arms (no skill / self-evolved by
Haiku 4.5 / Haiku executor + Opus 5 optimizer), ~150 tasks with deterministic scorers,
K = 8 iterations, pre-registered paired statistics under existing lab conventions —
testing the one configuration the paper never ran: frontier proposer with the cheap
executor in the rollout loop. Phase A calibrates the rig on public benchmark tasks;
Phase B reuses it on millwork document microtasks. Budget: low hundreds of dollars.

## Promotion path notes

Nothing here changes the playbook by itself. Per the promotion path, an adjudication row
pairs project corroboration with external evidence; this report supplies only the
external half (a single 3-day-old preprint — not yet external consensus), so its
findings land as candidate defaults at best, pending an executed lab experiment. The
report's sources are sources.yaml-compatible (`type: paper` / `official-repo`,
`evidence_strength: research-only`).
