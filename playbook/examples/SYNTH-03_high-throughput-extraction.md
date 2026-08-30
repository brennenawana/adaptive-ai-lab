# SYNTH-03: High-Throughput Manifest Extraction

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

Four million scanned freight manifests a day, twelve fields to pull off each one. Ten of
those fields are ordinary: get one wrong and somebody corrects it downstream. The other
two — hazmat class and an over-weight flag — feed routing decisions directly, and a wrong
value there is a different kind of event entirely. No judge is needed anywhere in this
project, because years of manually-keyed manifests supply an answer key and a script can
mark every field right or wrong against it. So the real question is not which model is
best. It is how small and cheap a model this pipeline can run before those two dangerous
fields start to slip.

The [project profile](../GLOSSARY.md#project-profile) fields that route this
project (template: [PROJECT_PROFILE](../templates/PROJECT_PROFILE.md)):

| Field | Value |
|---|---|
| Business outcome | Replace manual keying of freight-carrier shipment manifests with automated extraction, at a cost per successful extraction below the manual baseline |
| Task population & volume | ~4 million scanned manifest documents/day; a closed 12-field schema per document |
| Criticality / failure cost | Mixed: most fields are operationally important but correctable; two fields (hazmat class, over-weight flag) feed downstream routing decisions directly and carry a much higher failure cost |
| Quality / reliability target | Field-level exact match against a large existing manually-keyed corpus; the two safety-relevant fields held to a much tighter tolerance than the rest |
| Latency / throughput / SLA | Offline batch; throughput-bound against a fixed daily processing window, not interactive latency |
| Privacy / security / residency | Ordinary business data; no special residency requirement |
| Data & knowledge availability | Years of manually-keyed historical manifests — a large, ready-made ground-truth corpus |
| Tool / action permissions | None — pure extraction, no external actions taken by the system |
| Model candidates | A frontier-capable managed-API model down to small open-weights models on rented GPU capacity |
| Owned compute | None at start |
| Rentable compute | Yes — elastic, and the primary execution surface |
| Capex / recurring budget | Recurring compute spend is the dominant, deliberately-managed cost line |
| Staffing / time | A small platform team with ongoing operational ownership |
| Deployment environment | Batch pipeline; no interactive UI |
| Existing evidence | A large historical manually-keyed corpus; strong existing basis for ground truth |
| Stakes / consequence tolerance | Tier 2 overall; the two safety-relevant fields carry Tier-3-flavored consequence handling for that slice only |

## Archetype & rigor tier

The routing facts: a closed schema that is objectively verifiable, extreme volume, no
owned hardware at start, and elastic rented compute as the natural execution surface.
Together they make this a high-volume extraction project with deterministic grading,
where the central design variable is **cost per successful task** rather than raw model
capability. That is what pulls chapter 11's economics machinery into the middle of the
work and keeps it there, instead of leaving it for a final sanity check.

Stakes tier is **Tier 2 (Consequential)** overall. Rigor attaches to a decision's
consequence rather than to the project (00 §6), so the two safety-relevant fields do not
drag the whole project to Tier 3. Only their own consequence-bearing tolerance inherits
stricter handling — curtailed exact counting with a hard consequence — because that is
where the consequence actually concentrates.

## The decisive moves

1. **Deterministic grading from day one.** Every field can be checked against the
   historical manually-keyed corpus, so chapter 03's decision rule applies with nothing
   left over: deterministic exact-match grading, no judge, and no judge-calibration
   protocol anywhere in this project.
2. **Consequence-bearing tolerance split by field criticality.** The 12-field schema is
   stratified (chapter 04) into a *standard* group and a *safety-relevant* group (hazmat
   class, over-weight flag). Each group gets its own tolerance, pre-registered — written
   down before any data is collected — along with what happens when it breaks:

   | Field group | Tolerance | Consequence on breach | Projected cost if PROCEED |
   |---|---|---|---|
   | Standard (10 fields) | ≤ 3 errors per 500-item sample | RECALIBRATE prompt/parsing | Re-run sample, ~2 platform-hours |
   | Safety-relevant (2 fields) | ≤ 1 error per 2,000-item sample | ABORT the candidate for this field group | Candidate not shipped for these fields until fixed |

3. **[STOP CONDITION] The safety-relevant tolerance is breached mid-sweep.** The team is
   sweeping downward from the large pilot model toward a cheaper one, chasing a cost
   target. [Curtailed exact counting](../GLOSSARY.md#curtailed-exact-counting) — count
   violations as they land and halt the moment the count passes what the tolerance
   allows — stops the safety-relevant-field sample at its second violation. The
   pre-registered tolerance allowed one, so it is breached. The first instinct is to note
   the miss and ship anyway, since the ten
   standard fields still look strong; that move is exactly the unpriced-escape-hatch
   anti-pattern named in [00 §9](../00_PRINCIPLES_AND_SCOPE.md), and a tolerance whose
   breach costs nothing was never a tolerance. So the pre-registered consequence fires as
   written: the smaller candidate is **not** shipped for the two safety-relevant fields.
   What ships instead is a mixed operating point. The smaller candidate handles the ten
   standard fields, and the two safety-relevant fields route through a
   grammar-constrained output path (ladder rung 3, output enforcement) that is
   re-measured against the same tolerance before anyone trusts it.
4. **Operating-point selection against the batch window, not raw throughput.** Chapter
   06's [operating point](../GLOSSARY.md#operating-point) — the concurrency and batch
   size the system is declared to run at — is chosen from a sweep at the scale the daily
   window actually demands. The number it is chosen on is
   [goodput](../GLOSSARY.md#goodput): throughput counted only where the schema's quality
   gates are met. A candidate that is fastest on paper but pushes more items into
   RECALIBRATE cycles does not win.
5. **Cost per successful task drives the size decision, after the quality gates pass and
   never before.** Chapter 11's expected cost per solve is cost divided by the measured
   pass rate at the chosen operating point, and it is computed only once both tolerance
   groups have cleared their gates. That number, not the sticker per-token price, is what
   justifies moving off the large pilot model.
6. **Demand ledger opened before any purchase conversation.** The mixed operating point
   draws a steady, large, highly predictable number of GPU-hours, and that draw is logged
   in the [demand ledger](../GLOSSARY.md#demand-ledger) (chapter 11) for a full month
   before hardware ownership is even discussed. The purchase question is deliberately
   deferred here, not answered.

## What was skipped and why

- **Judge-calibration protocol (chapter 03):** not applicable, since the domain is fully
  deterministic.
- **A learned or deterministic routing cascade (chapter 08):** considered at design time,
  not built at launch. An [oracle analysis](../GLOSSARY.md#oracle-analysis) — what a
  perfect router would have been worth — showed the achievable gain from a two-tier
  cascade was small next to the gate's own cost, given how the schema's difficulty is
  actually distributed. A single frozen operating point ships first, alongside the mixed
  path from move 3, and the cascade stays a documented option rather than a premature
  build.
- **Fine-tuning (chapter 09):** the standard-field error rate already clears its gate with
  prompting and grammar constraints (ladder rungs 3–4), so there is no
  [RC-10](../GLOSSARY.md#canonical-failure-taxonomy) evidence to justify descending
  further.
- **Full Tier-3 machinery:** not adopted project-wide. Only the safety-relevant field
  group inherits the stricter tolerance and consequence discipline, per the rule of
  proportion.

## Outcome

The shipped configuration is the mixed one that move 3's RECALIBRATE cycle produced: a
smaller, cheaper candidate for the ten standard fields, and a grammar-constrained path
for the two safety-relevant fields. Cost per successful extraction falls by roughly 60%
against the initial large-model pilot, and the safety-relevant fields hold inside their
tighter tolerance on re-measurement. The chosen operating point clears the daily batch
window with headroom. Month-one demand-ledger entries are logged, and the purchase
question is left open for a later, separate decision.

## Chapter trail

[00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) ·
[03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) ·
[08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) ·
[11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md) ·
[GLOSSARY](../GLOSSARY.md)

---

> [Index](../README.md) · [Examples](README.md)
