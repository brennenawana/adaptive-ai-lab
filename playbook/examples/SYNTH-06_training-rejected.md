# SYNTH-06: A Fine-Tune Request the Ladder Redirects to Retrieval and Spec

> [Index](../README.md) · [Examples](README.md)

**Synthetic worked example — all names and numbers invented.**

## Profile summary

"Halvorsen Archive Group," a regional public-media archive, wants a model to
auto-tag digitized historical photographs with subject, approximate location,
and usage-rights status for a public catalog. The team's working plan going
in is "let's fine-tune on our archivist-tagged photos."

| [Project profile](../GLOSSARY.md#project-profile) field | Value |
|---|---|
| Business outcome | Reduce a ~200,000-photo archivist tagging backlog |
| Task population & volume | ~3,000 photos/week need tagging |
| Criticality / failure cost | A wrong rights-status tag risks publishing an image the archive isn't licensed to publish |
| Quality/reliability target | Rights-status must be correct essentially always before auto-publish; subject/location has a looser, archivist-spot-checked bar |
| Latency / SLA | Batch, overnight runs acceptable |
| Privacy / security | Normal collection-agreement terms only |
| Data & knowledge availability | A per-collection rights database exists but isn't wired in; a controlled subject/location taxonomy exists in a style guide, also not wired in |
| Tool / action permissions | Read-only lookups (rights DB, taxonomy) once wired; no publish action from the model |
| Model candidates | One managed API model; one open-weights candidate under evaluation |
| Owned / rentable compute | One rented GPU node for evaluation runs |
| Managed APIs | One vendor endpoint |
| Budget | Small, grant-funded pilot |
| Staffing / time | 1 archivist + 1 engineer, part-time, ~10 weeks |
| Deployment environment | Internal batch pipeline |
| Observability constraints | Minimal, being built alongside the pilot |
| Regulatory / compliance | Contractual licensing/rights obligations; no external regulator |
| Existing evidence | None yet |
| Stakes / consequence tolerance | Tier 2 |

## Archetype & rigor tier

The team has not diagnosed an archetype at all — they have a solution
("fine-tune") in search of a problem, which is the point of this example.
Correctly routed, this is an evaluate-first, ladder-diagnosis project before
any training decision. Tier 2: a wrong rights tag carries real external
(contractual/reputational) consequence, but it is reversible pre-publish and
there is no external regulator forcing Tier 3.

## The decisive moves

1. **Evaluate first, before any training talk.** A small trusted eval is
   built from a stratified, held-out sample of already-tagged photos, scored
   against archivist gold tags. The rights-status field is a closed enum and
   scored exactly.
2. **Baseline the untrained model as it exists today.** Per chapter 05's
   simplest-credible-baseline default, the baseline runs with the production
   tools *as currently wired* — no rights DB, no taxonomy in context — the
   honest starting point, not the aspirational one.
3. **Diagnosis lands in two [canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy)
   classes, not one.** (a) **RC-3, missing/unreachable evidence** — the
   model is asked for a rights-status verdict that requires the per-collection
   licensing database, which is in neither its context nor its tool set; a
   measured [reachability ceiling](../GLOSSARY.md#reachability-ceiling) on
   the rights-status stratum sits near the floor regardless of which model
   answers. (b) **RC-6, task-specification gap** — subject/location tags
   scatter across synonyms because the controlled taxonomy was never given to
   the model; the model knows the concepts, it was never told the vocabulary.
4. **[STOP CONDITION]** fires before the fine-tune request goes further. A
   quality claim — "the model is bad at rights tagging" — is about to be made
   with no reachable evidence behind it. The instrument-before-score
   principle stops that claim cold: a stratum whose measured ceiling sits
   near the pass bar cannot support a capability verdict about the model
   answering inside it.
5. **Fix in ladder order, not by training.** Rung 2: the rights database is
   wired in as a lookup tool and the taxonomy as retrieved context; the same
   frozen eval is re-run unchanged. Rung 4: the taxonomy addition is also a
   specification fix — the vocabulary drift closes once the model is told
   the vocabulary, not given more examples of it.
6. **Training refused, with the evidence stated.** After rungs 2 and 4 close
   the measured gap to within the eval's MDE against the archivist baseline,
   no capability gap (RC-10/RC-11) remains to justify rung 7. The request is
   declined, and the decision — with the evidence, not just the outcome — is
   written into a method decision record so "let's just fine-tune it" cannot
   resurface later without new evidence.

## What was skipped and why

- **No fine-tuning pipeline, LoRA/full-FT decision, or forgetting gate.**
  None of chapter 09's machinery is reached: the never-train-around-defects
  rule forbids descending to rung 7 while rungs 2 and 4 are unexhausted, and
  once exhausted, the measured gap closed.
- **No pass^k / reliability machinery.** A batch tagging task, not a
  stochastic multi-turn agent.
- **No shadow/canary deployment yet.** The pilot stays pre-publish and
  human-gated by design; deployment-chapter machinery engages only once
  auto-publish is proposed in a later phase.
- **Hardware/compute economics stayed light.** One rented eval node; no
  purchase question raised.

## Outcome

- Effort: ~5 weeks to build the eval and wire in retrieval + taxonomy,
  against the ~10+ weeks the team's original fine-tune-first sketch assumed.
- Rights-status accuracy on the held-out stratum moves from an
  uninterpretable score below a ~52% reachability ceiling (before the rights
  DB was wired in) to 97% once the database is a reachable tool.
- Subject/location tag consistency (exact-match to the controlled
  vocabulary) rises from 61% to 89% once the taxonomy is in context.
- Training stays open as a future, evidence-gated option for a narrower gap
  the ladder might not close on its own — not ruled out permanently, just
  not justified yet. Contrast [SYNTH-07](SYNTH-07_training-justified.md),
  where a narrower gap does survive the same ladder.
- Cost avoided: no training-data curation, no fine-tune compute, no
  forgetting-gate suite — the grant pilot stays inside its allocated budget.

## Chapter trail

- [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) — trusted eval,
  reachability ceiling, task ontology/taxonomy
- [05. Model Runtime and Harness Selection](../05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) —
  simplest credible baseline
- [07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) —
  ladder diagnosis, rungs 2 and 4
- [08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) —
  context policy for the rights DB and taxonomy
- [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) — the
  instrument-before-score tripwire, never-train-around-defects rule
- `templates/METHOD_DECISION_RECORD.md` — records the refusal and its
  evidence

---

[Index](../README.md) · [Examples](README.md)
