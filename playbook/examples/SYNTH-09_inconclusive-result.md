# SYNTH-09: An Inconclusive Moderation-Triage Upgrade

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

The bigger model scored 88%. The one already in production scored 84%. Four
points is the sort of margin that gets a model promoted — and this experiment
could not tell whether those four points were real.

"Norrbridge Media" is a social platform's trust-and-safety team. It runs a
content-moderation triage model in production that flags posts for human
moderator review, and a larger candidate has been proposed to replace it. The
team wants to know whether it is actually better before paying more for it.

| [Project profile](../GLOSSARY.md#project-profile) field | Value |
|---|---|
| Business outcome | Decide whether to replace the production moderation-triage model with a larger candidate |
| Task population & volume | ~50,000 user posts/day queued for triage before human moderator review |
| Criticality / failure cost | Missing a severe-violation post costs trust and moderator escalation; over-flagging wastes moderator queue time |
| Quality / reliability target | A composite triage-quality score (precision/recall blend); the severe-violation stratum must not regress |
| Latency / SLA | Sub-second triage per post, unchanged by either candidate |
| Privacy / security / residency | Public and semi-public post content only; no new residency constraint |
| Tool / action permissions | None — pure classification, no write actions beyond the flag itself |
| Model candidates | Candidate-Current (incumbent, in production) vs. Candidate-Upgrade (larger, ~2.3× inference cost) |
| Owned / rentable compute | Existing rented inference capacity for both candidates; no purchase question |
| Existing evidence | Production logs, a frozen evaluation suite already in its second release, one calibrated judge dimension from a prior cycle |
| Stakes / consequence tolerance | **Tier 2** — consequential, customer-visible, reversible |

## Archetype & rigor tier

A cost-versus-quality upgrade decision on a system that is already in
production. **Tier 2**: consequential and customer-visible, but reversible,
with no regulatory dimension.

That signature requires the full experiment-contract machinery of chapter 04
— a frozen comparison, a stated MDE, a look ledger. It does not require
chapter 13's Tier-3 provenance and audit set.

## The decisive moves

1. **A paired design on the frozen confirmation split.** Both candidates were
   scored on the same 400 items under one experiment contract. Comparing
   arms on the same item licenses
   [paired](../GLOSSARY.md#paired-design) standard errors — free statistical
   power the team was not going to leave on the table.
2. **The clustering unit was named, and its correlation measured, before any
   significance claim.** Outcomes are not independent: posts within a content
   category — harassment, spam, self-harm-adjacent, and so on — resemble each
   other, which makes the category the
   [clustering unit](../GLOSSARY.md#clustering-unit). An ANOVA-style estimate
   from pilot data put that within-category correlation at ICC ≈ 0.30. It was
   not assumed to be zero. With an average of 8 items per category, the
   [design effect](../GLOSSARY.md#design-effect) is
   DEFF = 1 + (8 − 1) × 0.30 = 3.1, so the
   [effective N](../GLOSSARY.md#effective-n) is N_eff = 400 / 3.1 ≈ 129 —
   well under the raw item count [EXT-STATS-001].
3. **The MDE and a licence for the word "competitive" were pre-registered
   together, before data.** At N_eff ≈ 129, α = .05, and power = .80, the
   cluster-robust paired procedure gives an
   [MDE](../GLOSSARY.md#mde) ≈ 9 percentage points on the triage-quality
   score. The contract then pre-registered ±9pp as an equivalence margin, and
   fixed what could be said about it: the phrase "competitive (within ±9pp)"
   would become licensed
   [descriptive vocabulary](../GLOSSARY.md#descriptive-vocabulary) *only if*
   the realized cluster-robust confidence interval on the paired difference
   landed entirely inside that margin. Pre-registration supplies who chose
   the words and when. It does not supply the resolving power to earn them —
   the interval still has to clear the bar. All of this was decided before
   anyone had seen an outcome.
4. **[STOP CONDITION]** The honest answer is "we still don't know," and the
   pre-registered rule is what forces it to be written down that way.

   The measured result: Candidate-Upgrade 88% against Candidate-Current 84%
   — a 4pp gain, with a cluster-robust 95% confidence interval of roughly
   **[−3pp, +11pp]**.

   That interval fails two different tests, and it matters that they are
   different.

   *It cannot support a difference.* The interval straddles zero, and the
   whole 4pp sits well inside the design's own 9pp MDE. Nothing here is
   CONFIRMED or REFUTED.

   *It cannot support an equivalence either.* Its upper bound of +11pp
   reaches past the ±9pp margin move 3 pre-registered, so the licensed
   "competitive" reading is not triggered. The data did not earn that phrase.

   What is left is the verdict principle P9 makes first-class:
   [INCONCLUSIVE](../GLOSSARY.md#inconclusive), reported with its interval.
   This comparison can rule out neither an 11-point gain for Candidate-Upgrade
   nor a 3-point loss. That is the whole result, and it *is* a result.

   This is precisely the tripwire the pre-registered rule exists to catch: a
   sub-MDE margin about to become a headline number, either as a real
   difference *or* as an equivalence the data do not support.
5. **With quality unresolved, the decision moved to the question the evidence
   could actually answer.** That question is cost per successful task
   (chapter 11): per request, Candidate-Upgrade runs about 2.3×
   Candidate-Current, in exchange for a gain the experiment cannot confirm.
   The incumbent was retained on that basis — on the economics, stated as
   such, and explicitly not on the inconclusive quality result, which decided
   nothing.
6. **The look ledger was updated, and its refresh trigger flagged.** This was
   look 4 of a pre-registered 5-look budget on the confirmation split before
   a mandatory suite-refresh review
   ([look ledger](../GLOSSARY.md#look-ledger)). With one look left, the team
   chose not to spend it re-running the same comparison. The next look is
   pre-registered for after the suite refresh, on a narrower question.

## What was skipped and why

- **pass^k reliability claims.** Both candidates are deterministic
  classifiers at inference — temperature 0 in production — so repetition
  variance is not in play and the pass^1/pass^k distinction does not apply.
- **New judge calibration.** The one subjective-severity dimension already
  has a calibrated judge from a prior release cycle. No new calibration was
  needed for this comparison.
- **Tier-3 provenance and security-review artifacts (13).** This is a Tier-2
  signature — business-consequential, not safety- or regulation-bound — so
  the heavier record-of-record and threat-model machinery legitimately does
  not apply. The floor items were kept regardless: provenance sufficient to
  identify what produced a result, and held-out exposure recorded. The
  [never-skippable floor](../GLOSSARY.md#never-skippable-floor) is never
  skippable.
- **A hardware purchase decision (11's demand ledger).** Both candidates run
  on existing rented capacity. No capex question exists yet.

## Outcome

The experiment cost about 3 engineer-weeks — 1 engineer building the
comparison, 1 analyst on the statistics and the write-up — and used compute
already budgeted for routine evaluation. No new spend. The production
decision was to keep Candidate-Current.

The write-up says plainly that the result is INCONCLUSIVE on triage quality.
The cluster-robust 95% CI of [−3pp, +11pp] does not exclude an 11-point gain
for Candidate-Upgrade, so not even the pre-registered ±9pp equivalence margin
is satisfied, and the comparison cannot resolve which candidate is actually
better at this effective N. That sentence is the finding. The deployment
decision was then made on cost, with the uncertainty stated alongside it —
not by rounding an inconclusive result into either a difference or an
equivalence.

The team recorded a plan for the next cycle: after the suite refresh, run a
narrower, higher-power comparison restricted to the severe-violation stratum
alone, where the practical stakes are highest and a smaller true effect would
still be worth resolving.

## Chapter trail

- [01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) —
  profile, stakes tier
- [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) — clustering
  unit, frozen suite
- [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) —
  ICC → DEFF → N_eff → MDE chain, INCONCLUSIVE, descriptive vocabulary, look
  ledger
- [11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md) —
  cost-per-successful-task decision
- [14. Decision Trees and Checklists](../14_DECISION_TREES_AND_CHECKLISTS.md) —
  the sub-MDE tripwire

---

> [Index](../README.md) · [Examples](README.md)
