# SYNTH-09: An Inconclusive Moderation-Triage Upgrade

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

"Norrbridge Media," a social platform's trust-and-safety team, runs an
in-production content-moderation triage model that flags posts for human
moderator review. A larger candidate model is proposed as a replacement.
The team wants to know if it is actually better before paying more for it.

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

A cost-vs-quality upgrade decision on an already-production system:
**Tier 2**, consequential and customer-visible but reversible with no
regulatory dimension. That signature requires the full experiment-contract
machinery of chapter 04 — frozen comparison, MDE statement, look ledger —
but not chapter 13's Tier-3 provenance and audit set.

## The decisive moves

1. **Paired design on the frozen confirmation split.** Both candidates were
   scored on the same 400 items under one experiment contract. Same-item
   cross-arm comparison licenses [paired](../GLOSSARY.md#paired-design)
   standard errors — free power the team was not going to leave on the table.
2. **Clustering unit named and its ICC measured before any significance
   claim.** Outcomes correlate within content category (harassment, spam,
   self-harm-adjacent, and so on — the
   [clustering unit](../GLOSSARY.md#clustering-unit)). An ANOVA-style
   estimate from pilot data put ICC ≈ 0.30 — not assumed zero. With an
   average of 8 items per category,
   [design effect](../GLOSSARY.md#design-effect) DEFF = 1 + (8 − 1) × 0.30 =
   3.1, so [effective N](../GLOSSARY.md#effective-n) N_eff = 400 / 3.1 ≈ 129
   — well under the raw item count [EXT-STATS-001].
3. **MDE and an equivalence-margin licence pre-registered together, before
   data.** At N_eff ≈ 129, α = .05, power = .80, the cluster-robust paired
   procedure gave [MDE](../GLOSSARY.md#mde) ≈ 9 percentage points on the
   triage-quality score. The contract pre-registered ±9pp as an equivalence
   margin: the phrase "competitive (within ±9pp)" would be the licensed
   [descriptive vocabulary](../GLOSSARY.md#descriptive-vocabulary) reading
   *only if* the realized cluster-robust confidence interval on the paired
   difference landed entirely inside that margin. Pre-registration supplies
   who chose the words and when, not the resolving power to earn them — the
   interval still has to clear the bar. Decided before anyone had seen an
   outcome.
4. **[STOP CONDITION]** The result lands inside MDE — but the interval
   doesn't clear the equivalence margin either, so the verdict is
   INCONCLUSIVE, not "competitive." Measured delta: Candidate-Upgrade 88%
   vs. Candidate-Current 84%, a 4pp gain with a cluster-robust 95% CI of
   roughly [−3pp, +11pp]. That interval straddles zero and sits well inside
   the 9pp MDE, so no CONFIRMED or REFUTED difference is supported — but its
   upper bound (+11pp) also extends past the pre-registered ±9pp equivalence
   margin, so move 3's licensed "competitive" reading is not triggered
   either. Per principle P9, the recorded verdict is
   [INCONCLUSIVE](../GLOSSARY.md#inconclusive), reported with its CI: the
   comparison can rule out neither an 11-point Upgrade gain nor a 3-point
   Upgrade loss — exactly the tripwire (a sub-MDE margin about to be read as
   a real difference, *or* as an equivalence the data don't support) that
   the pre-registered rule exists to catch before either becomes a headline
   number.
5. **The deployment decision moved to economics instead of the unresolved
   quality question.** With quality unproven, cost per successful task
   decided it (chapter 11): Candidate-Upgrade runs ~2.3× the per-request cost
   of Candidate-Current for a gain the experiment cannot confirm. The
   incumbent was retained on that basis, not on the inconclusive quality
   result.
6. **The look ledger was updated, and its refresh trigger flagged.** This
   was look 4 of a pre-registered 5-look budget on the confirmation split
   before a mandatory suite-refresh review
   ([look ledger](../GLOSSARY.md#look-ledger)). With one look left, the team
   chose not to spend it re-running the same comparison — the next look is
   pre-registered for after the suite refresh, on a narrower question.

## What was skipped and why

- **pass^k reliability claims.** Both candidates are deterministic
  classifiers at inference (temperature 0 in production); repetition
  variance is not in play, so the pass^1/pass^k distinction does not apply.
- **New judge calibration.** The one subjective-severity dimension already
  has a calibrated judge from a prior release cycle; no new calibration was
  needed for this comparison.
- **Tier-3 provenance and security-review artifacts (13).** This is a
  Tier-2 signature — business-consequential, not safety/regulated — so the
  heavier record-of-record and threat-model machinery legitimately does not
  apply. Floor items (provenance sufficient to identify what produced a
  result, held-out exposure recorded) were kept regardless — the
  [never-skippable floor](../GLOSSARY.md#never-skippable-floor) is never
  skippable.
- **A hardware purchase decision (11's demand ledger).** Both candidates run
  on existing rented capacity; no capex question exists yet.

## Outcome

The experiment cost about 3 engineer-weeks (1 engineer building the
comparison, 1 analyst on the statistics and write-up) and used compute
already budgeted for routine evaluation — no new spend. The production
decision was: keep Candidate-Current. The write-up states plainly that the
result is INCONCLUSIVE on triage quality — the cluster-robust 95% CI
[−3pp, +11pp] does not exclude an 11-point gain for Candidate-Upgrade, so even
the pre-registered ±9pp equivalence margin is not satisfied — and that the
comparison cannot resolve which candidate is actually better at this
effective N. The deployment decision was made on cost with that uncertainty
stated, not by rounding the inconclusive result into either a difference or
an equivalence. The team recorded a plan
for the next cycle: after the suite refresh, run a narrower, higher-power
comparison restricted to the severe-violation stratum alone, where the
practical stakes are highest and a smaller true effect would still be worth
resolving.

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
