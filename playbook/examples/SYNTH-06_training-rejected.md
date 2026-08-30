# SYNTH-06: A Fine-Tune Request the Ladder Redirects to Retrieval and Spec

> [Index](../README.md) · [Examples](README.md)

**Synthetic worked example — all names and numbers invented.**

## Profile summary

This team arrived with the answer already picked. "Let's fine-tune on our
archivist-tagged photos" was the plan before anyone had measured what the
model got wrong, or why — a solution in search of a problem, which is the
whole reason this example is here.

"Halvorsen Archive Group" is a regional public-media archive sitting on a
backlog of roughly 200,000 digitized historical photographs that archivists
tag by hand. The proposed tool would read a photograph and assign three
things for the public catalog: subject, approximate location, and
usage-rights status.

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

There is no archetype here yet, because nothing has been diagnosed. A
fine-tune is a repair, and the project has not established what it is
repairing. Routed correctly, this is an evaluate-first project that owes a
ladder diagnosis before any training decision gets made.

**Tier 2.** A wrong rights tag has a real consequence outside the building:
the archive could publish an image it is not licensed to publish, which is a
contractual and reputational problem, not an internal one. But nothing
reaches the catalog without a human step, so the error is reversible before
it escapes — and no external regulator forces the heavier Tier-3 set.

## The decisive moves

1. **Evaluate first, before anyone says the word "training."** A small
   trusted eval is built from a stratified, held-out sample of photographs
   the archivists have already tagged, scored against those tags as gold.
   Rights status is a closed list of allowed values, so it is scored exactly.
   No judgment is involved in marking it right or wrong.
2. **Baseline the model as it exists today, not as it is meant to exist.**
   Chapter 05's simplest-credible-baseline default means running with the
   production tools *as currently wired* — no rights database, no taxonomy in
   context. That is the honest starting point. The aspirational one would
   have measured a system nobody had built yet.
3. **The diagnosis lands in two classes of the
   [canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy),
   not one.** The model is being asked two different kinds of question, and
   it is failing them for two different reasons.

   *It cannot know.* A rights-status verdict depends on the per-collection
   licensing database, and the model has no path to that database — not in
   its context, not in its tool set. Measured, the best score anything could
   achieve on the rights-status stratum sits near the floor, whichever model
   answers. That measured best-possible score is the stratum's
   [reachability ceiling](../GLOSSARY.md#reachability-ceiling). **(RC-3,
   missing/unreachable evidence.)**

   *It was never told.* Subject and location tags scatter across synonyms,
   because the controlled taxonomy lives in a style guide the model has never
   seen. It knows the concepts perfectly well. It does not know which word
   the catalog wants. **(RC-6, task-specification gap.)**
4. **[STOP CONDITION]** fires, and it stops the fine-tune request cold.
   A quality claim — "the model is bad at rights tagging" — is about to be
   made with no reachable evidence behind it. This is
   the instrument-before-score principle doing its one job: a stratum whose
   measured ceiling sits near the pass bar cannot support a capability
   verdict about the model answering inside it. The score is not measuring
   the model. It is measuring a question the model was never given the
   evidence to answer.
5. **Fix in ladder order — which is not the training order.** Rung 2: the
   rights database is wired in as a lookup tool, and the taxonomy goes into
   retrieved context. The same frozen eval is re-run, unchanged. Rung 4: that
   taxonomy addition doubles as a specification fix. The vocabulary drift
   closes once the model is *told* the vocabulary — not once it is shown more
   examples of it.
6. **Training is refused, and the refusal is written down with its
   evidence.** After rungs 2 and 4, the gap left against the archivist
   baseline is smaller than the eval's own [MDE](../GLOSSARY.md#mde) — the
   smallest difference this eval could reliably detect. No capability gap
   (RC-10/RC-11) survives to justify descending to rung 7. The request is
   declined, and the decision goes into a method decision record with the
   evidence attached, not just the outcome. That is what stops "let's just
   fine-tune it" from resurfacing next quarter on no new evidence.

## What was skipped and why

- **No fine-tuning pipeline, LoRA/full-FT decision, or forgetting gate.**
  None of chapter 09's machinery is reached. The never-train-around-defects
  rule forbids descending to rung 7 while rungs 2 and 4 are unexhausted —
  and once they were exhausted, the measured gap had closed.
- **No pass^k / reliability machinery.** This is a batch tagging task, not a
  stochastic multi-turn agent.
- **No shadow/canary deployment yet.** The pilot stays pre-publish and
  human-gated by design. The deployment chapter's machinery engages only when
  auto-publish is proposed, in a later phase.
- **Hardware and compute economics stayed light.** One rented eval node, and
  no purchase question was ever raised.

## Outcome

- Effort: ~5 weeks to build the eval and wire in retrieval plus taxonomy,
  against the ~10+ weeks the team's original fine-tune-first sketch assumed.
- Rights-status accuracy on the held-out stratum moves from an
  uninterpretable score below a ~52% reachability ceiling — the state before
  the rights database was wired in — to 97% once that database is a reachable
  tool.
- Subject/location tag consistency, measured as exact match to the controlled
  vocabulary, rises from 61% to 89% once the taxonomy is in context.
- Training stays open as a future, evidence-gated option for a narrower gap
  the ladder might not close on its own. It is not ruled out permanently;
  it is not justified yet. Contrast
  [SYNTH-07](SYNTH-07_training-justified.md), where a narrower gap does
  survive the same ladder.
- Cost avoided: no training-data curation, no fine-tune compute, no
  forgetting-gate suite. The grant pilot stays inside its allocated budget.

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
