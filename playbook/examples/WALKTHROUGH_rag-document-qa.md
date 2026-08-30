# WALKTHROUGH: A RAG Document-QA Assistant Through the Navigator

> [Index](../README.md) · [Examples](README.md)

**Synthetic worked example — all names and numbers invented.** This
walkthrough exists to prove the navigator runs without any source-project
knowledge: every fact below is invented for "Calderwood & Voss," a fictional
mid-size law firm, and nothing here depends on any project that built this
playbook.

---

## The arrival state

The firm's operations director sends two engineers a message, and it is
typical of how these projects actually start:

> "Can we get something that lets paralegals ask questions about our
> contracts instead of digging through the document system by hand — like a
> chat tool, but it has to point to where the answer came from."

Read that again for what it does not contain. No volume estimate. No named
quality bar. No list of question types. No statement of who checks the
answers before they reach anyone. No model preference. Not even a deadline —
the director hasn't set one yet either. What it contains is a
plausible-sounding capability and an instruction to "look into it," addressed
to two engineers with no dedicated ML staff to lean on.

## Step 1 — Filling the PROJECT_PROFILE

[QUICKSTART](../QUICKSTART.md) Step 1 is unambiguous about what happens to a
message like that: it becomes a filled
[project profile](../GLOSSARY.md#project-profile)
([templates/PROJECT_PROFILE.md](../templates/PROJECT_PROFILE.md)) before
anyone touches a model.

The engineers spend a morning turning the director's two sentences, plus one
follow-up conversation, into the 21 fields.

| # | Field | Value |
|---|---|---|
| 1 | Business outcome | Cut paralegal research time per contract/policy question and hand back a citation an attorney can verify without re-searching; target: median research time from ~15 min (manual document-system search) to <4 min for lookup/extraction-shaped questions |
| 2 | Task population & volume | ~2,000 queries/day over ~40,000 contracts and internal policy documents; question shapes: clause lookup, obligation/deadline extraction, cross-document comparison (e.g. across an amendment chain), definition lookup, precedent/similar-clause search, presence/absence checks, counterparty identification |
| 3 | Criticality / failure cost | A wrong or uncited answer is embarrassing and wastes review time, but every answer is checked by a paralegal or attorney before it reaches a client or a filing — no autonomous drafting, filing, or client communication at launch |
| 4 | Quality/reliability target | Every answer must carry a citation that actually supports the claim (deterministically checkable); overall helpfulness/correctness judged against a human-reviewed bar; single-shot use, no pass^k claim needed — the tool is re-askable |
| 5 | Latency/throughput/SLA | Interactive; p95 < 8s; ~2,000 queries/day, concentrated in business hours |
| 6 | Privacy/security/data residency | Documents and query content must never leave the firm's cloud tenancy; managed model APIs acceptable only through in-tenant/VPC-scoped endpoints with no vendor training retention |
| 7 | Data & knowledge availability | ~40,000 documents in the firm's document management system, mixed formats, inconsistent metadata; ~6 months of legacy keyword-search query logs; no existing question/answer pairs |
| 8 | Tool/action permissions | Read-only document search and passage retrieval; no drafting, filing, or outbound-communication actions |
| 9 | Model candidates | Two tiers from the firm's existing-contract vendor (mid-tier, frontier); one mid-tier model from a second vendor under a contract pending legal sign-off; no open-weights/self-hosted candidates — no staff to run them |
| 10 | Owned compute | None |
| 11 | Rentable compute | None anticipated — API-only design |
| 12 | Managed APIs | Two vendors, each with an in-tenant/VPC-scoped option; existing contract with vendor 1, new contract with vendor 2 in legal review |
| 13 | Capex budget | None pre-approved |
| 14 | Recurring budget | <$4,000/month, inference + retrieval infrastructure at launch scale |
| 15 | Utilization/growth expectations | Flat at ~2,000 queries/day for two quarters; a second-office rollout under discussion could roughly double volume if the pilot succeeds |
| 16 | Staffing/time | Two engineers, ~60% combined time, 10-week runway to first release (this walkthrough covers Sprint 1, the first two weeks) |
| 17 | Deployment environment | Internal web tool behind firm SSO, hosted in the firm's cloud tenancy |
| 18 | Observability constraints | May log queries, retrieved passages, and citations; no client-identifying matter detail beyond an internal matter ID; 90-day retention |
| 19 | Regulatory/compliance | No sector regulator forcing this deployment; ordinary attorney work-product/confidentiality obligations, handled by field 6's tenancy constraint, not by an audit mandate |
| 20 | Existing evidence | None — no prior eval, no incumbent automated QA system; only the legacy search logs and paralegal interviews as raw signal |
| 21 | Stakes/consequence tolerance | Tier 2 — business-consequential, reversible, human-reviewed (fields 3, 4); full tier walk in Step 2 |

## Step 2 — The rigor tier

The [never-skippable floor](../GLOSSARY.md#never-skippable-floor) applies
whatever field 21 turns out to say, so it is satisfied first. The decision
(field 1) and the claim it needs evidence for are already written down. The
eval/ground-truth boundary gets defined before any quality claim — that is
Sprint 1's whole middle section. Provenance, consequence predeclaration, and
held-out accounting are designed into the eval build from move 4 onward,
rather than bolted on afterward.

Field 21 itself is read off the [stakes tier](../GLOSSARY.md#stakes-tier)
table in [00 §6](../00_PRINCIPLES_AND_SCOPE.md):

| Tier | Signature | Does the firm match? |
|---|---|---|
| 1 — Exploratory | Internal, reversible, low blast radius | No — a real business outcome (field 1) rides on paralegal-visible behavior |
| **2 — Consequential** | Business decisions, customer-visible behavior | **Yes** — fields 1, 3, 4: a real metric and visible answers, but reviewed before use and reversible |
| 3 — High-stakes/regulated | Safety, money movement, compliance, audit | No — field 19: no regulator forces this deployment; failures are embarrassing and reviewable, not safety- or audit-critical |

**Landing: Tier 2.** Mandatory artifacts beyond the floor: frozen
[experiment contracts](../GLOSSARY.md#experiment-contract), versioned suites
with [static integrity gates](../GLOSSARY.md#static-integrity-gates),
MDE/effective-N statements with a first-class
[INCONCLUSIVE](../GLOSSARY.md#inconclusive) verdict, a
[look ledger](../GLOSSARY.md#look-ledger), and a
[prediction ledger](../GLOSSARY.md#prediction-ledger).

**The one decision that would escalate.** Fields 8 and 3 keep every tool
read-only and a human in the loop before anything reaches a client. There is
a single decision that would go past that: auto-populating a client-facing
document, or sending output straight to a client with no review. That is
irreversible and client-facing, so under the
[rigor dial](../GLOSSARY.md#rigor-dial)'s rule of proportion it escalates
*that decision* to Tier-3 artifacts — 13's threat-model review,
human-approval gates — the day it is proposed. The rest of the project does
not move with it.

## Step 3 — The archetype route

QUICKSTART Step 3 routes a profile to an
[archetype](../GLOSSARY.md#archetype) by walking a tree from the top and
taking the first branch whose condition is true.

| # | Condition | The firm's fact | Answer |
|---|---|---|---|
| 1 | Trusted eval for this task exists? | Field 20: none | **No** — this one never ends the walk. It adds a prerequisite that carries forward whichever letter fires: chapter 03 comes before optimization and selection either way |
| 2 | Incumbent AI/automated system exists AND is failing its own quality bar — or the gap has no trusted measurement? | Legacy keyword search is not an AI system with diagnosable failures — there is nothing to diagnose, only something to replace | **No** |
| 3 | Goal = cost reduction of a working system with an established, MEASURED quality bar? | No existing measured system to reduce the cost of | **No** |
| 4 | Regulatory / audit / reliability obligations dominate the requirements? | Field 19: no regulator forces this deployment | **No** |
| 5 | Privacy / residency / IP constraints mandate a deployment that NO managed API can satisfy — not even an in-tenant/VPC-scoped, no-retention one? | Field 6 is real and binding, but an in-tenant/VPC-scoped managed API satisfies it. So it constrains *which execution surfaces are admissible* (chapter 05); it does not decide that the model must run self-hosted | **No — partially real, doesn't fire** |
| 6 | Deliverable is the eval/experimentation capability itself? | Deliverable is a product, not a lab | **No** |
| 7 | — | — | **A — Greenfield, API-models-only** |

The order of nodes 4 and 5 is deliberate, not alphabetical. A regulated
project often answers yes to both, and the high-stakes route's governance set
already contains everything the local-mandate route would have asked for.

Two cross-cutting modifiers apply on top of the letter.

- **Judge-graded modifier — fires partially.** Field 4 splits cleanly in two.
  Whether a cited passage exists and supports the claim is objectively
  checkable by code. Whether the synthesized answer correctly represents that
  passage is genuinely open-ended. QUICKSTART's rule for this split is that
  "deterministic verification stays the default wherever any part of the
  output is checkable" — so citation-checking stays deterministic, and only
  the answer-quality dimension picks up the judge-calibration protocol
  ([03 §5.7](../03_EVALUATION_FOUNDATION.md),
  [doctrine — not yet exercised](../GLOSSARY.md#doctrine-not-yet-exercised))
  before any quality claim is made on that dimension.
- **Cross-provider modifier — fires.** Field 9 already commits Sprint 1 to
  comparing candidates across two vendors and two tiers. QUICKSTART's second
  modifier covers exactly that — any comparison planned across machines,
  sessions, or providers — and its instruction is to read chapter 02 *now*,
  before trusting any number the comparison produces. That pulls
  [02](../02_EXECUTION_SYSTEM_MODEL.md) into archetype A's entry path
  (01→03→04), because a provider-side redeploy of any candidate silently
  creates a new [execution system](../GLOSSARY.md#execution-system) and
  breaks the [comparability claim](../GLOSSARY.md#comparability-claim)
  between arms. This is the sense in which the route is "A, with B's early
  chapter 2": the archetype stays A — only archetype B puts 02 in its
  *default* path — but A borrows the same early read when its own facts
  demand it.

**Route table entry (A):** entry path 01→03→04 (with 02 pulled forward);
typically skippable at start: 06, 09, 11-hardware (11's API-economics content
stays in play); mandatory templates at Tier 2: PROJECT_PROFILE,
EXPERIMENT_CONTRACT, TEST_LOOK_LEDGER, PREDICTION_LEDGER.

## Sprint 1, day by day

Ten business days, compressed to the moves that mattered.

1. **Day 1 — Fill the profile; name the decisions.** The table in Step 1 gets
   written down, with each field tagged to the decision it feeds. This is
   archetype A's first action, taken literally rather than as a formality.
2. **Day 1–2 — Read chapter 02 early.** Per the cross-provider modifier, the
   engineers write down what a
   [frozen identity](../GLOSSARY.md#frozen-identity) means here: model
   artifact, provider model-version string, retrieval-index version,
   chunking, prompt template, and citation verifier — one row per candidate.
   The [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) is
   declared same-session-only until proven otherwise. A provider redeploy is
   assumed to void comparability, rather than assumed safe.
3. **Day 2–4 — Derive the task ontology from real evidence.** Error-analysis
   first, per archetype A's second action. Roughly 70,000 logged legacy
   keyword searches from the trailing six months, plus structured interviews
   with five paralegals across two practice groups, cluster into a
   [task ontology](../GLOSSARY.md#task-ontology) of seven classes: clause
   lookup, obligation/deadline extraction, cross-document comparison
   (amendment chains), definition lookup, precedent/similar-clause search,
   presence/absence checks, and counterparty identification. That
   presence/absence class is a deliberate
   [absence case](../GLOSSARY.md#absence-case) — "does this MSA contain an
   indemnification cap?" is a question whose right answer is sometimes "no,"
   and a suite without such items never finds out what the system does with
   them.
4. **Day 4–6 — Build the first eval set.** Iterate split: 260 items.
   Qualification split: 540, stratified across the seven classes. Gold is the
   cited passage ID(s) plus a short reference answer, produced by two
   paralegals working independently and adjudicated where they disagreed. It
   is stored where the retrieval and generation path structurally cannot read
   it — [ground-truth isolation](../GLOSSARY.md#ground-truth-isolation) by
   permission separation, not by convention.
5. **Day 6–7 — Measure reachability; don't assume it.** Static integrity
   gates replay every item's evidence requirement through the real retrieval
   pipeline, against an 85%-per-stratum passing threshold:

   | Stratum | Reachability ceiling |
   |---|---|
   | Clause lookup | 96% |
   | Obligation/deadline extraction | 91% |
   | Cross-document comparison (amendment chains) | **58%** |
   | Definition lookup | 94% |
   | Precedent/similar-clause search | 88% |
   | Presence/absence check | 90% |
   | Counterparty identification | 97% |

6. **Day 7 — [STOP CONDITION] fires.** Global tripwire #2: a stratum's
   measured ceiling is below its passing threshold — the instrument is
   broken; scores on it are meaningless. The diagnosis is RC-1
   (measurement/instrument defect) in the
   [canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy).
   The chunker splits an amendment's clause text away from the parent
   contract it amends, so a gold answer's evidence can never co-occur in the
   same top-k retrieval. No candidate model is compared on any stratum until
   the instrument is fixed. "The instrument outranks the score," applied
   literally.
7. **Day 7–8 — Fix the corpus and tooling, not the model.** This is a rung-2
   fix — evidence, retrieval, context. Amendment documents are linked to
   their parent contract by document-family metadata, and the two retrieve
   jointly. The gates re-run clean: the stratum's ceiling moves to 89%,
   clearing 85%. Only now does a model comparison become admissible at all.
8. **Day 8–9 — Judge calibration, round 1, fails.** The answer-helpfulness
   dimension — the open-ended half of field 4 — is checked against a 50-item
   paralegal-labeled anchor set. Chance-corrected agreement comes in under
   the pre-registered bar, because the rubric had conflated "cites the right
   passage" with "reads well." Split into two dimensions, round 2 clears
   κ = 0.71. This is the gate the judge-graded modifier exists to force.
9. **Day 8–9 — Choose the candidates.** Three configurations, one factor: the
   incumbent vendor's mid-tier model as baseline, its frontier model, and the
   second vendor's mid-tier model. Retrieval, chunking, prompt, and verifier
   are held identical across all three — archetype A's "2–4 candidate models,
   one factor" line, taken as written.
10. **Day 9–10 — Freeze the first EXPERIMENT_CONTRACT.** Condensed below; the
    full document fills every section of
    [templates/EXPERIMENT_CONTRACT.md](../templates/EXPERIMENT_CONTRACT.md).

**§1 Question/decision:** Does the incumbent vendor's frontier model raise
citation-verified answer accuracy over its own mid-tier model by enough to
justify its per-query cost premium, holding retrieval, chunking, prompt, and
verifier fixed? Decision: adopt the frontier tier only if accuracy rises
≥5pp; otherwise ship the mid-tier model and evaluate the second vendor
separately. Prediction: +4pp, interval [+1pp, +8pp].
**§2 Baseline:** Suite `calderwood-docqa-eval v1`. Verifier: deterministic
citation-match scorer v1, plus the calibrated judge (κ=0.71) for helpfulness.
Incumbent: mid-tier model, frozen for the run.
**§5 Manipulated variable:** model artifact (3 levels) — the ONE factor, per
[EXPERIMENT_CONTRACT](../templates/EXPERIMENT_CONTRACT.md)'s rule.
Controlled: retrieval, chunking, prompt, verifier, generation budget.
**§6 Split protocol:** iterate=260, qualify=540 (stratum-interleaved across
the 7 classes), confirm=540, one look.
**§7 Calibration:** citation-failure rate on the iterate split; a
[consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance)
of ≤3 in 50; breach → RECALIBRATE (retune the verifier threshold) once, else
ABORT.
**§10 Statistics:** [clustering unit](../GLOSSARY.md#clustering-unit) =
class × document family. [ICC](../GLOSSARY.md#icc) = 0.15
(iterate-estimated). m≈9 → DEFF≈2.2 →
[N_eff](../GLOSSARY.md#effective-n)≈245 on N=540.
[MDE](../GLOSSARY.md#mde) at α=.05/power=.80 ≈ 5.1pp. Primary:
cluster-robust paired t-test. Secondary: McNemar exact (anti-conservative).
**§12 Qualification gate:** every stratum's reachability ceiling ≥85%
(measured, move 7), or the stratum is excluded from scoring.
**Freeze checklist:** all eight items checked before qualification-split
execution began.

## What the navigator prevented

- **A premature vector-DB bakeoff.** Week zero's first instinct was to A/B
  five retrieval backends before any eval existed. The no-trusted-eval branch
  (Step 3, condition 1) put that behind the eval build instead of ahead of it.
- **Premature fine-tuning talk.** An engineer floated fine-tuning a small
  open-weights model to "get citations right." It was blocked twice over: no
  RC-10 evidence yet justifies descending to rung 7, and field 9 already
  rules out open-weights and self-hosted candidates on staffing grounds.
- **An untrusted-eval model comparison.** After move 3, someone ran the three
  candidates against 15 questions typed up in an afternoon and wanted to call
  a winner. Global tripwire #1 — a quality claim about to be made with no
  trusted eval behind it — stopped it cold.
- **A judge without calibration.** The first plan for grading "citation
  quality" was to ask one candidate model to judge the others: no anchor set,
  no κ threshold. The judge-graded modifier's calibration requirement blocked
  it, and move 8 ran the real protocol instead.

## Where Sprint 1 ended

Sprint 1 ends exactly where Tier 2+ always ends: a frozen
[EXPERIMENT_CONTRACT](../templates/EXPERIMENT_CONTRACT.md) for the first real
experiment, committed before the qualification split is touched.

Sprint 2 is conditional on that contract's confirmation-split read.

- **If the frontier tier's margin clears the ≥5pp decision threshold** and
  sits outside the design's ≈5.1pp MDE — Sprint 2 opens with economics
  (chapter 11: cost per resolved query against the frontier tier's premium)
  and a shadow-period design for launch (chapter 10).
- **If the margin lands inside the MDE band** — which is plausible, since the
  decision threshold of 5pp sits almost exactly on top of the design's own
  5.1pp MDE — the verdict is written as
  [INCONCLUSIVE](../GLOSSARY.md#inconclusive) and never rounded to "no
  difference." What happens next is governed by the contract's pre-registered
  sub-MDE handling, chosen at freeze — defer to the confirmation split — and
  not by an ad hoc call made after seeing the number.
- **Either way**, the second vendor's mid-tier candidate gets its own read
  from the same frozen run. It was deliberately scoped as a third arm inside
  the same one-factor comparison rather than as a second contract, so no
  additional look is spent to evaluate it.

## Chapter trail

- [QUICKSTART](../QUICKSTART.md) — the navigator this walkthrough exercises
- [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) — floor, rigor dial, evaluate-first, instrument-before-score, ladder ordering
- [01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) — the profile itself
- [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) — frozen identity, reproducibility boundary, read early per the cross-provider modifier
- [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) — task ontology derivation, reachability ceilings, judge calibration
- [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) — the frozen contract, MDE/effective-N, INCONCLUSIVE
- [08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) — the document-family retrieval fix
- [11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md) — where Sprint 2's cost read enters
- [GLOSSARY](../GLOSSARY.md) ·
  [templates/PROJECT_PROFILE.md](../templates/PROJECT_PROFILE.md) ·
  [templates/EXPERIMENT_CONTRACT.md](../templates/EXPERIMENT_CONTRACT.md) ·
  [templates/TEST_LOOK_LEDGER.md](../templates/TEST_LOOK_LEDGER.md) ·
  [templates/PREDICTION_LEDGER.md](../templates/PREDICTION_LEDGER.md)

---

> [Index](../README.md) · [Examples](README.md)
