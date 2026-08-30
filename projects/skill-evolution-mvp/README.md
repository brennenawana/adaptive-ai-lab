# Skill-Evolution MVP

**Status: Phase 0 complete (rig built, smoke test passed, $1.07 equivalent spent).
Contract SE-1 freezes at the first commit; Phase 1 runs next.**

The lab's validation experiment for WikiSkill-style skill evolution, sized like
karpathy/autoresearch: three directories, one metric, hard budget caps, overnight scale.
It tests the one configuration the source paper never ran — a frontier optimizer with a
cheap executor *in the rollout loop*.

It is also a practice run of the playbook's primary use — client engagements: a client
shows their current AI-assisted process; the lab proves at small, fixed cost how it
would improve it. Phases 0–2 validate the improvement machine on a public task suite
with borrowed answer keys; Phase 3 practices the full client work pattern on a real
prospective-client domain (millwork), including building the answer keys. Reference
hierarchy and the full mapping: `PLAN.md` §1.

Grounding: `research/2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.html` (§8 is the design
this project executes; the claims index there carries the evidence base).

| File | Role |
|---|---|
| `PLAN.md` | The game plan: readiness, structure decision, architecture, phases, budget and stop criteria, proof standard |
| `IMPLEMENTATION.md` | The running story of how the plan became a working experiment |
| `SE1_EXPERIMENT_CONTRACT.md` | The pre-registration: frozen values, stop rules, statistics, verdict readings — written before the data |
| `rig/` | The experiment code: 11 modules, one gateway, fail-closed budget meter |
| `runs/` | Ledgers, look ledger, wiki snapshots, accepted skills (committed); raw traces stay local (gitignored) |

Decision layer: this project is archetype-lab-internal (methodology validation, not a
client system). Its findings feed the promotion path as the **project-evidence half** of
a future EVIDENCE_MAP row whose external half is the WikiSkill paper.
