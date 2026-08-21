# SYNTH-03: High-Throughput Manifest Extraction

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

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

The routing facts: a closed, objectively verifiable schema, extreme volume, no
owned hardware at start, and elastic rentable compute as the natural execution
surface. This is a high-volume, deterministic-grading extraction project where
**cost per successful task**, not raw model capability, is the central design
variable — the QUICKSTART route that enters chapter 11's economics machinery
early and repeatedly, rather than once at the end.

Stakes tier is **Tier 2 (Consequential)** overall. Per the rule of proportion
(00 §6), the two safety-relevant fields do not escalate the whole project to
Tier 3 — only their own consequence-bearing tolerance inherits stricter
handling (curtailed exact counting with a hard consequence), because that is
where the decision's actual consequence concentrates.

## The decisive moves

1. **Deterministic grading from day one.** Every field is objectively checkable
   against the historical manually-keyed corpus, so chapter 03's decision rule
   applies directly: deterministic exact-match grading, no judge, no
   judge-calibration protocol needed anywhere in this project.
2. **Consequence-bearing tolerance split by field criticality.** The 12-field
   schema is stratified (chapter 04) into a *standard* group and a
   *safety-relevant* group (hazmat class, over-weight flag), each with its own
   pre-registered tolerance:

   | Field group | Tolerance | Consequence on breach | Projected cost if PROCEED |
   |---|---|---|---|
   | Standard (10 fields) | ≤ 3 errors per 500-item sample | RECALIBRATE prompt/parsing | Re-run sample, ~2 platform-hours |
   | Safety-relevant (2 fields) | ≤ 1 error per 2,000-item sample | ABORT the candidate for this field group | Candidate not shipped for these fields until fixed |

3. **[STOP CONDITION] The safety-relevant tolerance is breached mid-sweep.**
   During a candidate-downsizing sweep (moving from the large pilot model toward
   a cheaper one to hit a cost target), [curtailed exact counting](../GLOSSARY.md#curtailed-exact-counting)
   halts the safety-relevant-field sample at its second violation — the
   pre-registered tolerance is breached. The team's first instinct is to note
   the miss and ship anyway, since the standard fields still look strong: this
   is exactly the unpriced-escape-hatch anti-pattern named in
   [00 §9](../00_PRINCIPLES_AND_SCOPE.md). Instead, the pre-registered
   consequence fires as written: the smaller candidate is **not** shipped for
   the two safety-relevant fields. The resolution is a mixed operating point —
   the smaller candidate handles the ten standard fields, while the two
   safety-relevant fields route through a grammar-constrained output path
   (ladder rung 3, output enforcement) re-measured against the same tolerance
   before it is trusted.
4. **Operating-point selection against the batch window, not raw throughput.**
   Chapter 06's [operating point](../GLOSSARY.md#operating-point) is chosen from
   a concurrency sweep at the batch scale the daily window actually needs,
   using [goodput](../GLOSSARY.md#goodput) (throughput that clears the schema's
   quality gates) rather than peak raw throughput — a candidate that is fastest
   on paper but pushes more items into RECALIBRATE cycles is not the winner.
5. **Cost per successful task drives the size decision, after quality gates
   pass, never before.** Chapter 11's expected-cost-per-solve — cost divided by
   the measured pass rate at the chosen operating point — is computed only
   after both tolerance groups clear their gates. It is this number, not the
   sticker per-token price, that justifies moving off the large pilot model.
6. **Demand ledger opened before any purchase conversation.** The mixed
   operating point's steady, large, and highly predictable GPU-hour draw is
   logged in the [demand ledger](../GLOSSARY.md#demand-ledger)
   (chapter 11) for a full month before hardware ownership is even discussed —
   the purchase question is deliberately deferred, not decided here.

## What was skipped and why

- **Judge-calibration protocol (chapter 03):** not applicable — the domain is
  fully deterministic.
- **A learned or deterministic routing cascade (chapter 08):** considered at
  design time, not built at launch. An [oracle analysis](../GLOSSARY.md#oracle-analysis)
  showed the achievable gain from a two-tier cascade was small relative to the
  gate's own cost, given how the schema's difficulty is actually distributed —
  a single frozen operating point (plus the mixed path from move 3) ships
  first; a cascade stays a documented option, not a premature build.
- **Fine-tuning (chapter 09):** the standard-field error rate already clears
  its gate with prompting and grammar constraints (ladder rungs 3–4); there is
  no [RC-10](../GLOSSARY.md#canonical-failure-taxonomy) evidence to justify
  descending further.
- **Full Tier-3 machinery:** not adopted project-wide; only the safety-relevant
  field group inherits the stricter tolerance and consequence discipline, per
  the rule of proportion.

## Outcome

The final configuration pairs a smaller, cheaper candidate for the ten standard
fields with a grammar-constrained path for the two safety-relevant fields,
after the RECALIBRATE cycle triggered by move 3. Cost per successful extraction
drops by roughly 60% versus the initial large-model pilot, while the
safety-relevant fields hold inside their tighter tolerance on re-measurement.
The chosen operating point clears the daily batch window with headroom; the
month-one demand-ledger entries are logged, and the purchase question is left
open for a later, separate decision.

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
