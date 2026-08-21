# 03. Evaluation Foundation

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](02_EXECUTION_SYSTEM_MODEL.md) · [Index](README.md) · [Next →](04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
> **Reading time:** ~32 min. **Prerequisites:** [00](00_PRINCIPLES_AND_SCOPE.md),
> [01](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md), [02](02_EXECUTION_SYSTEM_MODEL.md).

## 1. Purpose and when to read this

This chapter builds the instrument every later decision depends on.
[P1 — evaluate first](00_PRINCIPLES_AND_SCOPE.md) says no selection, optimization, or
training decision is made without a trusted evaluation; this is how you make one
trustworthy. Read it before selecting a model (05), before optimizing anything (07),
and before any claim that a system "got better."

Everything downstream treats the eval suite as ground truth for whether an
intervention worked. An untrusted eval does not fail loudly — it silently redirects
the project toward fixing the wrong thing while producing plausible-looking scores.
Re-read §5.9 every time a suite changes, and §5.7 before adopting any LLM-judge
grader.

## 2. Inputs required

- A stated business decision (chapter 01) and the evidence claim it must produce.
- Real failure evidence — traces, tickets, logs, transcripts from the actual task
  population — not a specification written from imagination (§5.1).
- The project's [stakes tier](GLOSSARY.md#stakes-tier) (00 §6), sizing how much
  instrument-validation investment §6 requires.
- A [frozen execution-system identity](GLOSSARY.md#frozen-identity) (chapter 02) for
  anything scored against this instrument — an eval is meaningless without knowing
  what produced the outputs it grades.
- Whatever ground truth already exists (human annotations, a code-driven generator,
  an authoritative outcome log) and its access constraints.

## 3. Decisions this chapter supports

- Whether an evaluation result can be trusted at all before it drives any other
  decision (P2, the instrument-outranks-the-score gate).
- The shape of the task ontology for *this* task shape — which of the symptom,
  root-cause, sanctioned-action, and forbidden-claim layers apply, and what replaces
  the ones that do not (§5.1).
- Deterministic vs. LLM-judge grading, and whether a judge's scores mean anything
  yet (§5.6–§5.7).
- When a suite must be versioned rather than edited in place, and when it must be
  refreshed (§5.9).
- How much curation vs. volume a corpus needs, and what to do when curation and
  statistical power pull in opposite directions (§6).

## 4. Normative principles

**[PRINCIPLE] Symptom and diagnosis are different objects.** (inference —
first-principles; corroborated by external error-analysis-first practice
[EXT-EVAL-003])
A task ontology needs two layers that must never collapse into one: the presenting
**symptom** and the **root cause**. See
[symptom vs root cause](GLOSSARY.md#symptom-vs-root-cause). Score and stratify by
root cause; let symptom categories be many-to-many with causes on purpose (§5.1). A
system that has only learned symptom→remedy as a lookup looks competent until it
hits a symptom the lookup cannot disambiguate — exactly the case a good instrument
contains.

**[PRINCIPLE] Deterministic grading is the default wherever output is objectively
verifiable.** (strong-evidence [EXT-JUDGE-002] for the discrimination finding;
inference — first-principles for the trivially-checkable cases)
JudgeBench measures pairwise discrimination between a correct and an incorrect
response on hard knowledge/reasoning/math/coding items; a frontier judge scored
~56.6% against a 50% pairwise-chance baseline [EXT-JUDGE-002]. Read the number for
what it is: a **forced-choice** figure showing judges are unreliable at
*discriminating correctness on hard items*. It is not a measure of absolute grading
accuracy, and the study did not measure schema conformance, exact/fuzzy match, or
execution-result grading. The conclusion stands on two legs, not one: where
correctness is hard to discriminate, the judge is measurably weak; where output is
trivially checkable (schema, exact match, execution result), the deterministic check
wins on determinism, cost, and auditability without borrowing JudgeBench's number at
all. Wherever a deterministic check exists it MUST be preferred; a judge is licensed
only for open-ended output, behind the calibration protocol of §5.7. Operationalizes
[P11](00_PRINCIPLES_AND_SCOPE.md).

**[PRINCIPLE] The instrument's ceiling is measured before its score is believed.**
(strong-evidence [EXT-EVAL-005], [EXT-EVAL-008]; case-study [CASE: CASE-004])
A stratum's [reachability ceiling](GLOSSARY.md#reachability-ceiling) is an empirical
property of the instrument, not an assumption. Human-reviewing a widely used
benchmark down from 1,699 to 500 tasks moved the measured solve rate on the *same
models* from 16% on the full set to 33.2% on the curated subset [EXT-EVAL-005] — a
delta that mixes removal of invalid items with a change in the item population, and
that no published analysis decomposes. It therefore MUST NOT be reported as "17
points of instrument noise"; §9's cross-version-subtraction rejection binds this
playbook's own citations too. What the episode does establish is the point that
matters here: **a large share of a measured score can be a property of the corpus
rather than the model.** For the decomposed, same-corpus version of that lesson see
[CASE: CASE-004], where seven flagged forbidden claims were all detector artifacts
and the corrected all-pass rate moved from 91.7% to 99.0% with no change to the
systems under test. A low score on an unvalidated stratum measures the defect, not
the model (P2). The sequel makes the deeper point: the same benchmark's publisher
later reported that even the *curated* subset carried flawed test cases rejecting
functionally correct submissions, and retired it for frontier claims
[EXT-EVAL-008] — instrument validation is a standing activity, not a one-time gate.

**[PRINCIPLE] Gold labels score outcomes; they never choose anything.**
(strong-evidence; mechanics in [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
structural isolation in [13](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md))
[Gold labels](GLOSSARY.md#gold-labels) may score outcomes and fit pre-registered
calibration on the iterate split. They MUST NOT be readable by the system under test
at inference time, and MUST NOT select, route, or tune anything on a held-out split
— anything the system can read at inference time is not held out, and anything a
selection decision can see is not blind. Corroborated by a structural-leakage
finding: item-identity-encoding features defeated this boundary silently until an
explicit audit caught it [CASE: CASE-003].

**[PRINCIPLE] Criteria drift is real; the response is versioning, never silent
edits.** (strong-evidence [EXT-EVAL-004]; case-study [CASE: CASE-009])
Evaluation criteria cannot be fully specified before seeing outputs — a grader's
criteria and the ground truth it applies co-evolve as real outputs are seen. This is
an empirical finding about how people write rubrics, not a discipline failure
[EXT-EVAL-004]. The response is a versioned [suite release](GLOSSARY.md#suite-release)
(§5.9), never an in-place mutation.

**[PRINCIPLE] Leakage is measured and blocked structurally, never assumed absent.**
(strong-evidence [EXT-EVAL-006], [EXT-EVAL-007])
Contamination measurably moves scores: one study found up to an 8-percentage-point
drop when models were re-tested on a freshly collected, decontaminated version of a
benchmark they may have seen. Split isolation, private held-out sets, and
[canary strings](GLOSSARY.md#canary-string) on anything published [EXT-EVAL-007] are
the response; §5.8.

**[PRINCIPLE] A rubric changes only for an independently identified instrument
defect, never in response to a system's answer.** (consensus — the same
pre-registration norm as chapter 00's P7 [EXT-STOPPING-002]; case-study
corroboration [CASE: CASE-009])
Widening a rubric because a system disagreed with it, or narrowing it because a
system now agrees, is the instrument adapting to the thing it measures. Investigate
whether the disagreement reproduces under a controlled re-check; change the rubric
only when a separate, independently identified defect explains it (§9).

**[DEFAULT] Ontology changes are breaking changes to the suite.** (consensus)
Any change to the root-cause/label set, the action set, or the cause→action mapping
— or to whichever of §5.1's shape-equivalent layers your task actually has — bumps
the suite version and is logged with rationale (§5.9). Silent renumbering
invalidates every prior score's comparability.

## 5. Default procedure

### 5.1 Deriving a task ontology from a requirement (G1)

1. **Error-analysis-first.** Read real traces, tickets, or transcripts from the
   actual task population before writing a category; take open-ended failure notes,
   don't start from an imagined taxonomy [EXT-EVAL-003].
2. **Synthesize a closed category set, with an explicit symptom/root-cause split
   where the task shape has one** (see the shape map below — on a pure labeling
   task the two layers are the same object). Every item gets a presenting category
   and a root cause. Some categories should map to more than one cause on purpose
   (below).
3. **Stratify by root-cause class, not symptom.** Sampling, ceiling measurement, and
   power (chapter 04) all key on root cause; symptom is a display grouping.
4. **Define per-category evidence requirements.** For every root cause, state which
   facts a correct answer requires and where they live. This feeds reachability
   measurement (§5.5).
5. **Expect criteria drift; version, don't mutate.** The first pass will be wrong in
   places once real outputs are seen (P6); route corrections through a suite
   release (§5.9), never a live edit.

For a **diagnose-and-act** task the output is a four-layer closed vocabulary,
versioned as one unit:

| Layer | Answers | Scored by | Changes via |
|---|---|---|---|
| Symptom category | What does the operator see? | Not scored directly — a display grouping | Low-risk to add |
| Root cause | What is actually wrong? | Exact match against the closed set | §5.9 checklist — breaking change |
| Sanctioned action | What response does this cause license? | Membership in that cause's [cause-to-action table](GLOSSARY.md#cause-to-action-table) | §5.9 checklist — breaking change |
| Forbidden claim | What must never be asserted, regardless of other correctness? | Presence/absence, harm-weighted | §5.9 checklist — breaking change |

**The layer set is conditional on task shape; only the forbidden-claim layer is
close to universal.** The sanctioned-action layer applies only where the system
selects an action, and the symptom/root-cause split applies only where a presenting
signal is genuinely distinct from what is wrong. Place your task on this map before
building anything — over-building a diagnostic ontology for a labeling task is a
common and expensive mistake:

| Task shape | Ontology layers to build | What changes |
|---|---|---|
| Diagnose-and-act (triage, incident routing, remediation) | All four layers above | The canonical case; §8.2's lookup-ceiling arithmetic applies as written |
| Classification / labeling (topic tags, intent, priority) | Root cause **≈ the label itself**; symptom layer collapses into it; sanctioned-action layer **N/A**; forbidden-claim layer often N/A — mark it so explicitly rather than inventing one | Stratify by label and by the confusion pairs that carry cost; §8.2 applies only if two labels share a presenting surface |
| Extraction to schema (fields from documents, structured capture) | Field set · field-criticality strata · forbidden **fabrication** classes (a value asserted with no source in the input) | Scored per field, then aggregated; the forbidden layer becomes "never invent this field" |
| Generation / summarization (drafts, summaries, explanations) | Required-fact set (and its omission classes) · rubric dimensions · forbidden claims · stratification dimensions | No action set; the forbidden-claim layer carries most of the harm weight, and rubric dimensions are the judge-mediated part (§5.6–§5.7) |

Whichever shape applies, the vocabulary that *is* present is closed, versioned as one
unit, and changed only through §5.9's checklist.

**[DEFAULT] Deliberately ambiguous symptoms.** (heuristic; applies to shapes with a
symptom/root-cause split) Design a subset of
symptom categories to map to two or more root causes at comparable base rates, so a
symptom→remedy lookup is capped near the majority cause's base rate, not near
ceiling; genuine evidence-reading is not capped (§8.2 has the arithmetic). This is a
measurable name-anchoring-vs-reasoning probe, not decoration.

*Illustrative example, carried through this chapter:* an IT-helpdesk triage
assistant. Symptom `cannot log in` maps to two root causes at comparable base
rates — `expired credential` and `identity-provider outage` — disambiguated only by
reading account and provider logs. Symptom `application crashes on launch` maps to
one root cause, `corrupted local cache`, plus one absence case,
`no defect — could not reproduce`.

### 5.2 The canonical failure taxonomy

§5.1's root-cause set is **project-specific**. The
[canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy) below is one
level up: every project-specific root cause — and every instrument or system defect
producing a wrong answer for reasons unrelated to the task domain — classifies into
exactly one of these twelve generic classes at a time. A task-ontology root cause
answers "what specifically was wrong"; an RC class answers "what kind of fix does
this call for." This is the single generic taxonomy this playbook uses wherever a
root cause needs naming — chapters 07 and 14 and the templates consume it unchanged.
Two honesty notes govern how the table is read, both stated under it: RC-1 and RC-7
are separated by *whose* verifier is broken, and RC-10/11/12 are provisional-residual
classes rather than ex-ante diagnoses.

**Symptom categories are what an operator sees; every diagnosis lands in exactly one
of these root-cause classes:**

| # | Root-cause class | One-line meaning | Primary intervention rung |
|---|---|---|---|
| RC-1 | **Evaluation-instrument defect** | The *measuring instrument* is wrong: the eval harness, corpus, gold answers, or the **evaluation** grader (unreachable required evidence, wrong gold, grader polarity, a threshold at or above the measured ceiling) | Rung 0 — fix the instrument; no other result is interpretable |
| RC-2 | Infrastructure/runtime defect | Serving stack, transport, configuration, or environment corrupts execution | Rung 1 |
| RC-3 | Missing/unreachable evidence | Facts the task needs are absent from context and unreachable via retrieval/tools | Rung 2 |
| RC-4 | Tool/API contract defect | Schema, addressing, ordering, or permission mismatch between system and tools | Rung 3 |
| RC-5 | Output/format enforcement gap | Correct content lost to parsing/structure/grammar failures | Rung 3 |
| RC-6 | Task-specification gap | The system was never told (instructions, decomposition, workflow, examples) | Rung 4 |
| RC-7 | **In-system verification gap** | The system's *own* verifier, guard, or self-check passes failures silently at inference time | Rung 4 |
| RC-8 | Capacity/budget exhaustion | Context window, reasoning/generation budget, or truncation bounds the outcome | Rung 5 |
| RC-9 | Routing/escalation mismatch | Work sent to the wrong tier, or escalation policy mis-set | Rung 6 |
| RC-10 | Capability gap — learnable *(provisional-residual)* | The model lacks task-specific skill that demonstrably exists in obtainable training data | Rung 7 |
| RC-11 | Capability gap — fundamental *(provisional-residual)* | The model class cannot do it at any budget | Rung 8 |
| RC-12 | Architecture mismatch *(provisional-residual)* | The system topology is wrong for the task shape | Rung 9 |

**RC-1 vs. RC-7 — the disambiguating rule.** Both classes contain the words
"verifier" and "grader", and they route to opposite ends of the ladder, so decide
deliberately: *if the defective component is part of the execution system under
test, it is RC-7 (rung 4); if it is part of the measuring instrument, it is RC-1
(rung 0).* When in doubt, treat it as RC-1 — the cost of an unnecessary instrument
check is bounded; the cost of trusting a broken instrument is not.

RC-1 always ranks first: an unvalidated instrument makes every other class
unverifiable. §5.5 is how you validate it before trusting a diagnosis into any other
class. The full intervention ladder is chapter 07's operational form; the short
normative form is chapter 00 §4 (P3).

**RC-10, RC-11, and RC-12 are provisional-residual classes.** They are assigned only
after RC-1…RC-9 have been excluded, and they are distinguished from each other not
by an ex-ante test but by the *outcome of the rung they select*. The operating rule
is: attempt RC-10 first because it is the cheaper hypothesis, and treat a rung-7
INCONCLUSIVE or null as the evidence that reclassifies to RC-11; treat a staged
one-variable-at-a-time ladder replay whose residual gap tracks the topology rather
than any single component as the evidence for RC-12 (chapter 07 §5.1 carries the
rung-8 and rung-9 evidence bars; chapter 09 §7 carries the post-ablation
reclassification back to 07). Record the provisional class *and* the evidence that
would reclassify it, so the record does not read as a firmer diagnosis than it is.

**Stochastic reliability is a cross-cutting property, not a thirteenth class.** A
system that has the capability but not the *repeatability* — high pass@1 collapsing
at [pass^k](GLOSSARY.md#pass-at-k-vs-pass-to-the-k) on identical tasks at the same
configuration [EXT-AGENT-001] — is not diagnosed by a new RC row. It is diagnosed by
*measuring* pass^k at a pre-registered *k* (chapter 04) and then asking which class
the residual belongs to. Where it maps:

- **Rung 1 / RC-2** if the spread is nondeterminism the execution system was not
  supposed to have (batching, reduction order, an unpinned config) — check this
  first, because it is a defect, not a policy choice (chapter 02).
- **Rung 5 / RC-8** if the fix is generation-time configuration — decoding and
  sampling policy, self-consistency, or a budget that is too tight to be reliably
  sufficient. Name the sub-reason (sampling policy vs. budget) in the record; the
  rung is the same, the fix is not.
- **Rung 6 / RC-9** if the fix is a retry, latching, or escalation policy — the
  system needs a second attempt or a stronger tier, not a different sampler.

If none of those reduces the spread, the capability itself is in question and the
provisional-residual rule above applies. A reliability claim is always stated at a
pre-registered *k*; a pass@1 number is not a reliability claim.

**Non-ML and legacy incumbents map onto the same classes.** The taxonomy names
*kinds of fix*, not model internals, so a rule-based, scripted, or human-process
incumbent classifies without inventing new rows: an incomplete or stale rule set is
RC-6 (the system was never told); a rule set that fires on the wrong evidence
because the data it needs is not available to it is RC-3; a broken integration or
mis-parsed payload is RC-2 or RC-4; a workflow that silently accepts an unverified
result is RC-7; work routed to the wrong queue or never escalated to a human is
RC-9; and "no rule set could express this" is the legacy analogue of RC-11/RC-12.
Diagnose the incumbent with the same instrument you will later use on the
replacement — that is the only way the comparison means anything (chapter 01).

### 5.3 Corpus design

- **[DEFAULT] Representative sampling / stratification.** (consensus) Sample
  proportional to (or deliberately oversampled relative to) real-world frequency per
  §5.1's strata; state which and why.
- **[DEFAULT] [Distractor](GLOSSARY.md#distractor) design.** (inference —
  first-principles: an option that is never correct cannot be scored right by
  name-matching) Keep at least one action or label valid for no item in the corpus,
  to measure name-anchoring. Helpdesk example: a `reissue hardware token` action
  sanctioned for no current root cause.
- **[DEFAULT] [Absence case](GLOSSARY.md#absence-case) design.** (inference —
  first-principles) Items whose correct answer is "nothing is wrong" — prices
  confabulation directly; a corpus without them rewards systems that always find
  something.
- **[DEFAULT] [Forbidden claim](GLOSSARY.md#forbidden-claim) design.** (consensus)
  Enumerate assertion classes that would trigger a costly or harmful real-world
  action if believed, and score them as automatic case failure. Helpdesk example:
  `confirmed the user violated security policy` — never derivable from login
  evidence alone.
- **[DEFAULT] Per-instance consistency, not just the modal case.** (case-study
  [CASE: CASE-004]) Every generated instance — not only the typical one — must be
  checked against the forbidden hypotheses it is supposed to rule out; a generator
  right on average but wrong on a subset silently hands the model a data-consistent
  forbidden claim.
- **[DEFAULT] Background content through the real pipeline.** (case-study
  [CASE: CASE-004]; mechanism is first-principles) Filler/background content SHOULD
  be produced by the same generation path as primary content. A direct-write
  shortcut carries whatever the real pipeline would have normalized — an ID format,
  a timestamp pattern, a field-ordering difference — and any such artifact that
  correlates with a stratum is a model-visible shortcut unrelated to the intended
  signal. Where a bypass is unavoidable, an explicit artifact check MUST run before
  the corpus is trusted (can a trivial classifier separate bypassed from
  pipeline-produced items?), and a positive result is a structural-leakage finding
  under §5.8.

**Shape-dependence of these bullets.** The distractor bullet's *action* form and
everything keyed to a [cause-to-action table](GLOSSARY.md#cause-to-action-table)
apply only to task shapes that have an action set (§5.1's map). On classification,
extraction, and generation shapes the distractor becomes a label, field, or claim
valid for no item; the absence case becomes the "no finding / nothing to report"
item; and the forbidden-claim layer becomes forbidden *fabrication* on extraction
shapes. Representative stratification, per-instance consistency, and the
real-pipeline rule apply on every shape that uses a generator at all (for
human-annotated corpora, see §6's non-generator procedure).

### 5.4 Ground-truth design

| Source | Fits when | Does not give you | Governed by |
|---|---|---|---|
| Generator-derived | Closed, deterministic domains with code-computable ground truth | A free pass on reachability — still verified, not argued | §5.5 |
| Human-annotated | No code-derivable ground truth exists | A determinism guarantee; needs dual labelling, adjudication, and reported inter-rater agreement | §6's non-generator procedure (a counterpart for every §5.5 check) |
| Judge-mediated | Open-ended/preference-shaped output only | Anything, until calibrated | §5.7 |

The industry-consensus loop — objective → dataset → metrics → run → iterate, with
the explicit instruction to validate model-graders against humans before trusting
them — is broad practice [EXT-EVAL-001], [EXT-EVAL-002] (methodology citable; the
hosted platform behind [EXT-EVAL-002] sunsets 2026-11 per its own notice). §5.7's
protocol is that validation, made explicit.

**Gold-label boundary (restated from §4).** Gold labels score outcomes and may fit
pre-registered calibration on the iterate split; they are never readable by the
system under test, and never select/route/tune anything on qualify/confirm splits.
Enforcement mechanics live in chapter 13; split-statistics mechanics in chapter 04.
This is [G16](GLOSSARY.md#gold-labels)'s boundary rule; §7's gate enforces it
operationally.

### 5.5 Instrument validation

The methods below are written for a **code-driven generator** — reachability is
replayed, determinism is checked by regenerating, gold answers are recomputed. If
your ground truth is human-annotated instead, do not skip this section: read the
*Catches* column as the checklist you still owe, and run §6's non-generator
procedure, which supplies a counterpart for every row.

| Check | Catches | Method |
|---|---|---|
| Reachability ceiling | Unwinnable strata read as model weakness | Replay the evidence plan against the built corpus per stratum, through the real tool surface (§8.1) |
| **Threshold-below-ceiling check** | A stratum made unwinnable by construction | Compare each stratum's declared passing threshold against its measured ceiling; **any stratum with threshold ≥ ceiling fails the release** (§6, §8.4) |
| Weak-beats-strong [inversion check](GLOSSARY.md#inversion-check) | Guessable/broken stratum | A weaker system outscoring a stronger one — investigate the instrument first |
| Cross-arm disagreement review | Scorer/harness defects | Manually review every case where arms disagree before crediting or blaming either |
| Gold-answer gate | Corrupted/unreachable answer keys | Replay the gold answers through the scorer; must score at ceiling |
| Determinism check | Nondeterministic corpus generation | Regenerate the full corpus independently; compare a canonical content digest |
| [Frontier-saturation check](GLOSSARY.md#frontier-saturation-check) | Suite ceiling below the strongest system's true ceiling | Run the strongest available system; a suite it can't approach its own ceiling on is suspect |

[Static integrity gates](GLOSSARY.md#static-integrity-gates) run all of the above on
the full corpus, as executable commands, and MUST be protected from subsetting —
they are the instruments that catch instrument defects. [CASE: CASE-004] found
thirteen harness/scenario defects this way, every one initially indistinguishable
from model weakness.

### 5.6 Deterministic graders vs. LLM judges

| Task shape | Grader | Why |
|---|---|---|
| Objectively verifiable (execution result, schema, exact/fuzzy match) | Deterministic — MUST | The check is exact, cheap, and auditable; and where correctness is hard to discriminate, judges are measurably weak (~56.6% vs a 50% pairwise-chance baseline on forced-choice items [EXT-JUDGE-002] — see §4 for what that figure does and does not cover) |
| Open-ended / preference-shaped | Calibrated LLM judge | No deterministic check exists; calibration mandatory (§5.7) |
| Mixed | Deterministic on the checkable part + judge on the rest, reported separately | Conflating them hides which part changed |

Grader design is chosen by task shape, not convenience [EXT-EVAL-001]. A
deterministic verifier checks objectively-checkable properties — citations resolve,
IDs valid, values in-range, action codes sanctioned, schema conformance — and should
not judge reasoning nuance; that boundary is exactly where a calibrated judge, not a
stricter deterministic rule, belongs.

### 5.7 The judge-calibration protocol

*status: doctrine — not yet exercised (see §7's judge-trust gate for what validation
would look like: a scored anchor set, κ with a CI read against a pre-registered bar,
and a completed bias-audit report)*

A judge score MUST NOT drive any decision until all eight of the following are
complete and reported:

1. **Sampling design and anchor-set reliability.** Stratified sample against a
   human-anchor set — labels the judge is compared to, not trained on. The anchor
   set MUST be **dual-labeled independently**, with disagreements adjudicated by a
   documented rule (third annotator, or a written tie-break procedure), and the
   **human–human** chance-corrected agreement MUST be reported alongside
   κ(judge, anchor). State which label form κ is computed against — individual
   annotator labels or the adjudicated consensus — because it changes the number.
   κ(judge, anchor) is bounded above by the anchors' own reliability, so it is
   interpreted *relative to that ceiling*: κ = 0.55 against anchors whose human–human
   κ is 0.60 is a different claim from κ = 0.55 against adjudicated anchors at 0.90.
   An anchor set whose own agreement is below the pre-registered judge bar (step 8)
   cannot license any gate outcome — fix the annotation guideline first.
2. **Chance-corrected agreement, not raw percent.** The reason is arithmetic, not
   empirical: κ subtracts the agreement expected from the raters' marginals, so
   whenever labels are unbalanced raw agreement exceeds κ *by construction* (§8.3's
   formula makes this visible). Report the right estimator: **Cohen's κ** for two
   raters with nominal categories; **weighted κ** (linear or quadratic — state
   which) for two raters with **ordinal** categories; **Fleiss' κ** for three or more
   raters. Corroboration, not warrant: a single recent multi-judge study
   (`contested`, REFERENCE — treat as illustration, not law) reports 33–41
   percentage-point deflations between raw agreement and κ [EXT-JUDGE-003].
3. **Bias audits — each a measured quantity with a pre-registered tolerance.** A
   named bias with no number and no consequence is not a control (P7). Before
   scoring, declare each applicable audit's metric, its tolerance, and the
   consequence of a breach, as a
   [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance):

   | Audit | Measured as | Applies to | On breach |
   |---|---|---|---|
   | Position bias | Verdict-flip rate under order swap on a paired subsample (same two responses, both orders) | Pairwise judges only — N/A for single-output scoring, mark it so | Judge not usable until the prompt/protocol is changed and re-audited |
   | Length/verbosity preference | Correlation (or regression slope) of judge score against output length across items of equal anchor-rated quality | All judges | As above; a nonzero slope within tolerance is reported as a declared ceiling on the judge's scores |
   | Self-preference | Score differential on outputs from the judge's own model family vs. others, matched on anchor-rated quality | Any judge scoring output from its own family | Exclude same-family arms from judge-graded comparison, or change judge |
   | Style bias | Score differential across pre-registered surface-style variants of identical content | All judges | As position bias |

   **Arm blinding is mandatory and separate from the audits.** The judge's input MUST
   NOT identify which arm produced an output. Any identifying artifact — formatting,
   IDs, headers, a model's self-reference — is a structural-leakage finding under
   §5.8, not a style quirk.
4. **Rubric stability across paraphrase.** Measured as the **verdict-flip rate over
   *k* pre-registered paraphrases** of the same answer (state *k* and how the
   paraphrases were produced, before scoring), against a pre-registered maximum
   flip rate. Exceeding it means the rubric is under-specified: fix the rubric, then
   re-run steps 1–4. It is not a licence to pick the paraphrase the judge likes.
5. **Domain-transfer check before reuse.** A judge calibrated on one domain does not
   carry its agreement rate to another; strong published agreement (~80% on
   open-ended chat preference [EXT-JUDGE-001]) is not evidence for a domain with
   objectively verifiable answers — that domain belongs to §5.6's deterministic
   default.
6. **Drift monitoring and recalibration triggers.** Recalibrate on a pre-registered
   trigger, not suspicion.
7. **Report κ with a confidence interval, every time** — never raw agreement alone.
   CI construction and anchor-set sizing for a target CI half-width are in
   [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) §13; §8.3
   has the point-estimate formula and a worked example.
8. **Pre-registered κ bar and CI-width ceiling — written before step 1 is
   executed.** Ordered last in this list because it governs how the other seven are
   *read*, but it MUST be committed before any anchor item is scored: state the
   minimum κ and the maximum acceptable CI width that license each of §7's three gate
   outcomes, as a [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance)
   with the consequence named (§6 has the parameter and tier-scaled guidance). A bar
   chosen after seeing κ is not a bar; it is a description.

A useful calibration-reference pattern: build a pool of known-good/known-bad
judgments with expected scores (a "calibration bag"), and score any new judge
configuration by its deviation (z-score) from that baseline rather than an absolute
pass/fail line [ADAPT: NV-GARAK-001] — documented for security-probe regression
baselines and generalizes directly to judge calibration.

### 5.8 Leakage and contamination protection

- **[PRINCIPLE] Split isolation.** (consensus) Disjoint generation seeds/sources
  between iterate/qualify/confirm splits (mechanics: chapter 04).
- **[DEFAULT] Private held-out sets.** (consensus) Never publish qualify/confirm
  content in full.
- **[DEFAULT] Canary strings.** (strong-evidence [EXT-EVAL-007]) A unique marker plus
  a do-not-train statement in any published excerpt, so verbatim reproduction is
  detectable leakage.
- **[DEFAULT] Contamination checks.** (strong-evidence [EXT-EVAL-006]) Periodically
  re-test against a freshly collected, decontaminated slice; a material score drop is
  prior exposure, not regression.
- **[PRINCIPLE] Train/eval separation.** (consensus) Training data MUST never touch
  qualify/confirm content (mechanics: chapter 09; enforcement: chapter 13).
- **[PRINCIPLE] Structural leakage.** (case-study [CASE: CASE-003]) A feature letting
  a learned or judge-mediated component
  infer which stratum an item belongs to — not the signal it's meant to learn — is a
  leakage vector even with no gold field in sight. The audit that catches a router
  encoding item identity ([leakage audit](GLOSSARY.md#leakage-audit),
  [class-identity ceiling](GLOSSARY.md#class-identity-ceiling); [CASE: CASE-003])
  applies to any grading or gating component.

### 5.9 Suite versioning and release contracts

A [suite release](GLOSSARY.md#suite-release) is a pre-registered document — written
and frozen before any implementation or scoring against the new version — with a
fixed skeleton:

| Section | Contents |
|---|---|
| Purpose | What kind of release this is (a benchmark revision, not a model/prompt/routing experiment) and what it is not |
| Exact changelist | Per defect: the prior defect (with evidence it's real), the change, the invariant/test enforcing it, the model-facing effect |
| What is not changing | An explicit stability list |
| Release gates | Gate/check/tooling table — reachability per stratum, **threshold-below-ceiling check (any stratum with threshold ≥ ceiling fails the release)**, determinism match, gold-answer gate, disagreement review closed, frontier-saturation check |
| Versioning behavior | Version identifiers recorded per run; tooling refuses to mix versions without an explicit override ([cross-suite refusal](GLOSSARY.md#cross-suite-refusal)) |
| Baseline procedure | Fixed order of operations to re-establish baselines |
| Split policy | Confirm split untouched until freeze; one run per frozen arm after |
| Method rules carried forward | No results-driven changes; investigate disagreement before crediting/blaming |
| Known limitations left unfixed | Recorded explicitly, not silently lived with |

Template: [templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md).
[CASE: CASE-009] used this skeleton to make criteria drift explicit and auditable
instead of silent, keeping old-version results as labeled history — never
subtracted from new-version results.

**A raw score delta across two instrument versions is not a capability
measurement.** Decompose it: removed false-failures, removed defensible-but-wrong
readings, genuinely different evidence presented. None alone is "the model changed"
(§9).

**Refresh triggers.** A suite is due for review when the
[look ledger](GLOSSARY.md#look-ledger) (chapter 04) crosses a pre-registered
exposure threshold, a static integrity gate fails, or criteria drift is confirmed
(not merely suspected). Refresh follows the same release-contract discipline as any
version bump.

**Changing the closed vocabulary (checklist).** Any change to the root-cause set,
action set, or cause→action mapping:

1. Bump the suite/ontology version.
2. Update every synchronized copy — model-facing (if taught in-context) and the
   scorer's — with an automated equality test, not documentation discipline alone.
3. Re-check reachability for every new/changed class against the built corpus.
4. Record the change and its rationale.
5. Never compare results across versions without saying so.
6. Never change a mapping in response to one system's answers.

### 5.10 Regression suites vs. capability suites

| | [Regression suite](GLOSSARY.md#regression-suite-vs-capability-suite) | Capability suite |
|---|---|---|
| Question | Did anything that used to work break? | Can the system do X? |
| Breadth | Broad, stable | Targeted |
| Run frequency | Often (every change) | At decisions |
| Cost per run | Low, by design | Can be high; curated |

Conflating the two produces a suite too expensive to run often and too noisy to
decide with. A fine-tune or intervention gate (chapters 07, 09) runs the full
regression suite, never just the target slice — a slice-only gate cannot see
forgetting elsewhere.

### 5.11 The smoke tier

The [smoke tier](GLOSSARY.md#smoke-tier) is a third thing, below both suites in the
table above, and it exists for one purpose: catching harness, schema, and
tool-contract breakage *before* real spend.

| Property | Requirement |
|---|---|
| Composition | A **fixed** stratified mini-suite — the same items every run, one or two per stratum, chosen to exercise every tool path and every scorer branch |
| Wall-clock | Minutes, not hours. If it stops being cheap it stops being run, and an unrun smoke suite is worse than none |
| Where it runs | Inside the fail-closed record as chapter 04's non-promotable **[diagnostic run kind](GLOSSARY.md#diagnostic-run-kind)** — ledgered, hash-chained, cryptographically non-promotable (04 §4, §7) |
| What it can decide | Whether to spend on a real run; whether an integrity gate or tool contract broke |
| What it can never decide | Adoption, elimination, promotion, or any reported quality number — its MDE is enormous by design |

**[DEFAULT] Run the smoke tier before every scored run, and never quote it.**
(inference — first-principles; the run-kind mechanics are chapter 04's)
A smoke pass is evidence that the *instrument executed*, not evidence about the
system. Quoting a smoke number in a comparison is a sub-MDE promotion (chapter 04's
INCONCLUSIVE rule) and an unrecorded-path defect at once. A smoke **failure**,
however, is fully actionable: it is an RC-1 or RC-2 finding and it stops the run.

At Tier 1 a smoke-scale suite MAY stand in for full static integrity gates for
direction-finding only (§6's tier table); it never stands in for them at Tier 2+,
and never for an adoption claim at any tier.

## 6. Project adaptation parameters

### Non-generator instruments (G3)

*status: doctrine — not yet exercised (see §5.5 for the generator-derived analog
these protocols stand in for)*

Most of §5.5's machinery assumes a code-driven generator: reachability is *replayed*,
determinism is checked by *regenerating* the corpus, the gold-answer gate *re-runs*
computed answers. On a corpus of real, human-annotated material — the normal
condition for regulated work, and for every project that arrives without a trusted
eval — none of that is executable. This subsection is the substitute procedure, and
it is a procedure, not a caveat: run it in order and every check in §5.5 has a
counterpart.

1. **Annotation protocol and reliability.** Dual-label every item independently;
   adjudicate disagreements with a third annotator or a documented tie-break rule;
   report chance-corrected inter-rater agreement (§8.3's κ, with a CI —
   [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) §13)
   alongside the label set, and state whether downstream scoring uses individual or
   adjudicated labels. The reported human–human κ is the corpus's own reliability
   ceiling: no judge, model, or scorer can be credited with agreement above it
   (§5.7 step 1).
2. **Sampled-audit ceiling, sized to the precision the threshold needs.**
   Reachability cannot be replayed against a nonexistent generator, but *solvability*
   can be audited: a domain expert attempts each sampled item using only the evidence
   the system would have, and the fraction solvable is the stratum's ceiling proxy.
   Size the audit by the precision the decision needs, not by convenience — the
   ceiling has to be resolvable *apart from* the stratum's passing threshold, so the
   audit's margin of error MUST be smaller than the declared threshold-to-ceiling
   margin (§8.4). Use the binomial margin-of-error table in
   [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) §11 to pick
   *n*, and report the ceiling as an interval, never a point.
3. **Auditor independence.** The expert auditing solvability for a stratum MUST NOT
   be one of the annotators whose labels are that stratum's gold — an annotator
   re-attempting their own item measures recall of their own decision, not
   solvability. Where the expert pool is too small to separate them fully, declare
   the overlap and treat the ceiling as an upper bound.
4. **Gold-answer gate, non-generator form.** Replay the *adjudicated gold answers*
   through the scorer exactly as §5.5 requires; they MUST score at ceiling. This one
   check transfers unchanged and is the cheapest defense against grader-polarity and
   parsing defects, so run it first each release.
5. **Determinism analog: double-annotation drift.** There is no corpus digest to
   compare, so measure the human equivalent: re-annotate a fixed, pre-registered
   subsample under the current guideline and compare against its stored labels.
   Material drift is [criteria drift](GLOSSARY.md#criteria-drift) (P6) and triggers
   a suite release (§5.9), not a quiet relabel. Digest what *can* be digested — the
   annotation-guideline version, the annotator roster, and the adjudication rule —
   and record it in the release contract
   ([templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md)),
   so a score is always attributable to a guideline version.
6. **Cross-arm disagreement review, non-generator form.** Unchanged in intent:
   every item where arms disagree is reviewed by a human before either arm is
   credited or blamed. Route the review to an adjudicator, not to whoever proposed
   the arm under review.
7. **Judge-mediated ground truth.** Licensed only behind the full protocol of §5.7;
   an uncalibrated judge is an opinion in a confidence-inspiring format, not
   evidence. On a human-annotated corpus the judge is calibrated against the
   *adjudicated* labels, and its κ is read against the human–human κ from step 1.

### Contradiction: volume vs. curation (G20)

Two positions, both externally sourced:

- **Position A — volume.** Prefer a larger corpus at slightly lower per-item signal
  quality over a small curated one; more items give more power and catch more
  failure modes even if some are noisy [EXT-EVAL-001].
- **Position B — curation.** A large, uncurated corpus can undermeasure a system by
  mixing broken items with real ones. Hand-reviewing a widely used benchmark down to
  a fraction of its size moved the measured solve rate of the *same models* from 16%
  on the full set to 33.2% on the curated subset [EXT-EVAL-005] — a delta that mixes
  invalid-item removal with a change in the item population and is not decomposed by
  any published analysis (§4). It shows that corpus composition can dominate a score;
  it does not quantify how much of a given score is instrument defect.

**Decision rule.** Neither position wins unconditionally, and there is no formula
here — the honest form is a two-factor grid you place your corpus on.

*Axis 1 — how items are graded.* Deterministically gradable at low marginal cost
(generator-derived, schema/exact-match/execution-checked) → **volume**: more items
buy power and failure-mode coverage, and a few noisy items are diluted. Judge-mediated
or expensive to verify (human adjudication, clinical or legal review) → **curation**:
a bad item in a small judged set costs proportionally more, and judge noise compounds
instrument noise.

*Axis 2 — stakes tier.* Tier 1 and Tier 2 follow axis 1. **Tier 3 curates regardless
of grading cost** — an unreliable instrument is itself the risk being managed.

| | Deterministic, cheap to grade | Judge-mediated / expensive to verify |
|---|---|---|
| **Tier 1–2** | Volume | Curation |
| **Tier 3** | Curation (with volume added only after the curated core passes every §5.5 check) | Curation |

*The binding quantitative constraint, whichever direction you choose:* the smallest
stratum must still resolve the MDE its decision needs (the corpus-size parameter
below, chapter 04's machinery). That is the floor on shrinking a corpus, and it is
what makes "curate harder" a bounded instruction rather than an open licence.

**Precedence when curation and power collide (Tier 3).** "Curate regardless" reduces
N; chapter 04's guidance to tighten α or power at Tier 3 increases the required
N_eff; clustering (by annotator, site, document, or session) inflates DEFF on top.
These pull in opposite directions and the MDE-sizing rule cannot arbitrate on its own,
because at cold start you do not yet have the ICC and discordance it needs (chapter
04's freeze rule permits a declared prior ICC plus a pre-registered re-estimation
procedure — use it). When they collide, exactly three moves are licensed, and each
one is written into the contract:

1. **Widen the MDE and say so** — declare the larger effect the study can resolve and
   accept INCONCLUSIVE below it.
2. **Reduce the number of arms** — fewer comparisons on the same labels.
3. **Narrow the population** — a smaller, well-defined stratum resolved properly beats
   a broad one resolved not at all.

Silently keeping a tightened α/power on a corpus that cannot support it is **not**
licensed; it produces a study that is under-powered and *labeled* rigorous, which is
worse than an honest wide interval.

**[DEFAULT] Run a label-budget feasibility probe before the labeling spend, not
after.** (inference — first-principles) Before committing annotator time, compute
whether *any* affordable corpus resolves the effect the decision needs: take the
achievable annotation throughput, a plausible ICC range for your clustering unit, and
the effect size the decision turns on, and run chapter 04's MDE arithmetic backwards
to the required N. If no affordable N resolves it, that is a kill-criteria event
under [01 §5.3](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) — surface it *before* the
spend, when the licensed responses (re-scope the claim, change the decision, buy a
cheaper label source) are all still available.

### Instrument-validation investment by stakes tier

| Tier | Static integrity gates | Reachability | Judge calibration | Release discipline |
|---|---|---|---|---|
| 1 — Exploratory | Optional, smoke-scale (§5.11) | Argued at intake; measured before any adoption claim | **None required, and none licensed for decisions:** no judge score may enter a comparison, an adoption or elimination decision, or any reported number. Uncalibrated judge output is admissible only as unrecorded triage for choosing what to look at next | Lightweight, notes-grade |
| 2 — Consequential | Mandatory, full-corpus, every release | Measured per stratum before any score is trusted | Full protocol before any judge-graded decision | Versioned, frozen |
| 3 — High-stakes | Mandatory + periodic re-audit | Measured + independently re-verified | Full protocol + domain-transfer check + drift monitoring | Versioned + externally reviewable |

### Parameters

**[PARAMETER] Passing/recall threshold per stratum.** Set the threshold **below** the
stratum's measured ceiling with margin, never at or above it — the ceiling must
exceed the threshold by at least the declared margin (illustrative:
ceiling ≥ threshold + 0.05; §8.1, §8.4). Calibrate per stratum, not globally — a
shared global threshold silently caps whichever stratum has the lowest ceiling. This
is enforced mechanically, not by careful reading: §5.5's threshold-below-ceiling
check is a static integrity gate, and **any stratum whose declared threshold is ≥ its
measured ceiling fails the release** (§5.9's release gates, §7's stop condition).

**[PARAMETER] Corpus size and stratification depth.** Size the smallest stratum to
the MDE it needs to resolve (chapter 04), not a fixed item count. A scalable-
estimator shortcut on a small item set can produce unreliable item- or
ranking-level inferences [EXT-TESTBED-003] — check what a smaller corpus costs the
ceiling and MDE before shrinking it to save run time.

**[PARAMETER] Refresh-trigger exposure threshold.** Set from the project's own
expected look rate on the look ledger (chapter 04), not copied from another project.

**[PARAMETER] Judge calibration sample size.** Size the human-anchor set to resolve
the κ confidence interval the decision needs — target CI half-width at a plausible κ
and marginal distribution, per
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) §13 — not a
round number picked for convenience. The bar in the parameter below is what "the CI
the decision needs" means concretely: the anchor set is big enough when κ's lower
bound can land on the correct side of the bar.

**[PARAMETER] Minimum κ bar and CI-width ceiling for judge trust.** Declared per
project and per gate outcome, before the anchor set is scored (§5.7 step 8), as a
consequence-bearing tolerance. There is no universal number, and a κ bar copied from
a paper is not a bar. Choose it from what a judge error *costs* in this project, and
scale it by tier: **Tier 1** — no bar, because no judge score may drive a decision at
all (tier table above); **Tier 2** — a bar the project can defend in writing, with
the judge's κ lower bound above it before any judge-graded comparison; **Tier 3** —
the Tier-2 bar plus a maximum CI width (a wide interval around an acceptable point
estimate is not evidence), plus the requirement that the anchor set's own human–human
κ (§5.7 step 1) exceeds the judge bar, since the judge cannot be credited above its
anchors' reliability. Record the bar, the measured κ with CI, and the resulting gate
outcome together — a bar without its measurement is not auditable.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Suite release gate.** *Inputs:* the release-gate table (§5.9).
*Rule:* every gate passes, on the full corpus, before the new version is tagged and
comparisons switch to it. *Outcomes:* GO (tag, freeze, cross-suite refusal switches
over) / NO-GO (fix; no partial promotion).

**[DECISION GATE] Grader-choice gate.** *Inputs:* task shape. *Rule:* §5.6's table.
*Outcomes:* deterministic grader / calibrated judge / split-and-report-separately.

**[DECISION GATE] Judge-trust gate.** *Inputs:* the pre-registered κ bar and CI-width
ceiling (§5.7 step 8, §6); measured κ with its confidence interval against the anchor
set; the anchor set's own human–human κ; bias-audit results against their declared
tolerances; the domain-transfer check.
*Rule:* all eight steps of §5.7 complete and reported, **and** every bias-audit
tolerance met, **and** the anchor set's human–human κ above the bar — then read the
outcome off κ's confidence bound, not its point estimate:

| Condition | Outcome |
|---|---|
| κ's **lower** confidence bound ≥ the pre-registered bar, CI width within the declared ceiling | **Trusted-for-decision** |
| κ point estimate ≥ bar, but the lower bound falls below it (or the CI is wider than the ceiling) | **Directional-only** — may inform what to investigate; may not enter a comparison, an adoption/elimination decision, or a reported number |
| κ point estimate below the bar, any step incomplete, or any bias tolerance breached | **Not usable yet** — fix and re-calibrate; the anchor set spent on this attempt is spent (chapter 04's exposure accounting) |

*Note the asymmetry:* trust keys on the lower bound so that a small, noisy anchor set
cannot buy trust it did not earn — the cure for "the CI is too wide" is more anchor
items (§6's sizing parameter), never a lower bar.

*The one carve-out, stated identically in §6's tier table:* an uncalibrated judge may
be used as **unrecorded triage** — deciding which outputs a human looks at next. It
may not enter a comparison, an adoption or elimination decision, or any reported
number, at any tier. "What should I read next" is not a decision this gate governs;
everything downstream of it is.

**[STOP CONDITION] A stratum's measured ceiling is below its passing threshold.**
(= chapter 00 tripwire #2) Fix the instrument before reading any score from that
stratum. The release gate is stricter than the tripwire and stops the same defect one
step earlier: §5.5's threshold-below-ceiling check fails the release when
threshold **≥** ceiling, because equality demands a perfect run on a stratum with no
headroom (§8.4's margin requirement).

**[STOP CONDITION] Cross-arm disagreement observed and not yet reviewed.** Do not
credit or blame either arm until reviewed (§5.5).

**[STOP CONDITION] Held-out exposure crosses the pre-registered refresh threshold.**
Trigger the suite-refresh review (§5.9); exposure accounting is chapter 04's.

**[STOP CONDITION] A rubric change is proposed with no independently identified
instrument defect behind it.** Do not make the change; log the disagreement instead
(§5.9 checklist step 4).

## 8. Metrics and formulas

### 8.1 Reachability ceiling

```
ceiling(s) = reachable(s) / N(s)
```

`reachable(s)` counts items in stratum `s` whose full required-evidence set was
actually recovered when the evidence plan was replayed against the built corpus
through the real tool surface — never argued from the generator. `N(s)` is the
stratum's item count.

*Worked example (illustrative).* A stratum has 40 items; replaying the evidence plan
recovers the full required set for 36. `ceiling = 36/40 = 0.90`. If the stratum's
passing threshold is also 0.90, this is a fragile pass — set the threshold
comfortably below the ceiling (e.g., ceiling ≥ threshold + 0.05).

### 8.2 Lookup/shortcut ceiling for ambiguous categories

For a symptom category mapping to `k` root causes with corpus base rates
`p_1 … p_k` (Σp_i = 1), an uninformed symptom→cause lookup that always guesses the
modal cause achieves accuracy `max(p_i)` on that category.

*Worked example.* §5.1's helpdesk category `cannot log in` splits evenly between
`expired credential` and `identity-provider outage`: lookup accuracy caps at
`max(0.50, 0.50) = 0.50`. A system scoring meaningfully above 50% here is reading
evidence, not guessing the modal label.

### 8.3 Chance-corrected judge agreement (κ)

```
κ = (p_o − p_e) / (1 − p_e)
```

`p_o` = observed proportion of agreement between judge and human-anchor labels.
`p_e` = proportion of agreement expected by chance given each rater's marginal label
distribution.

*Worked example (illustrative).* 100 anchor items; judge and human agree on 82
(`p_o = 0.82`); marginal distributions imply expected chance agreement `p_e = 0.55`;
`κ = (0.82 − 0.55) / (1 − 0.55) ≈ 0.60`. Report κ with a confidence interval — the
CI machinery and the sample size needed for a target CI half-width are in
[references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) §13 — never
`p_o` alone. 0.82 looks strong, 0.60 is only moderate, and the 22-point gap between
them is not a surprise: it is what the formula does. Because `p_e` is subtracted and
the remainder rescaled by `1 − p_e`, raw agreement exceeds κ by construction whenever
labels are unbalanced, and the gap widens as the marginals skew. A single recent
multi-judge study (`contested`, REFERENCE — corroboration, not warrant) reports
deflations of 33–41 points in practice [EXT-JUDGE-003].

Read the number against two references, never in isolation: the pre-registered bar
(§5.7 step 8) and the anchor set's own human–human κ (§5.7 step 1), which is the
ceiling this κ is measured against.

### 8.4 Recall and passing bar

```
recall(item) = |evidence cited that matches required_evidence| / |required_evidence|
```

A stratum's passing threshold is a chosen bar (illustrative: 0.90) applied per item,
then aggregated. The stratum's reachability ceiling (§8.1) MUST exceed this bar with
margin, or the bar is unreachable regardless of system quality.

**Assumptions box; when these break.** All four formulas assume the evidence
requirements and root-cause labels are correct (§5.3's per-instance check) and that
corpus construction is stable — verified by §5.5's determinism check on a generated
corpus, or by §6's double-annotation drift check on a human-annotated one. They
measure the instrument's reachability and the judge's fidelity, not the model — an
unvalidated evidence requirement inflates a ceiling that isn't real, and a
non-representative or unadjudicated anchor set inflates a κ that won't transfer
(which is why §5.7 step 1 requires the anchor set's own reliability to be measured
and reported). On a human-annotated corpus, §8.1's `ceiling` is a **sampled estimate
with a confidence interval** (§6 step 2), not an exact count: compare the threshold
against the interval's lower bound, not its midpoint.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Ceiling-blind scoring**: reporting per-stratum accuracy without first computing
  that stratum's reachability ceiling — an unwinnable stratum reads as a weak model
  until someone checks [CASE: CASE-004].
- **Score-driven harness changes**: modifying a scorer, verifier, or rubric because
  of what a specific system's score looks like, not a proven, independently
  justified defect (§5.9 checklist step 6).
- **Rubric drift from results**: widening a rubric because a system disagreed with
  it, or narrowing it because it now agrees, absent an independently identified
  defect [CASE: CASE-009].
- **Cross-version score subtraction**: diffing raw pass rates between two instrument
  versions and reporting the delta as a capability change (§5.9).
- **Silent instrument-version mixing**: comparing run rows against manifests from a
  different suite version without an explicit override — exactly what
  [cross-suite refusal](GLOSSARY.md#cross-suite-refusal) exists to block.
- **LLM judge on verifiable output, uncalibrated**: substituting a judge for a
  deterministic check where one exists, or trusting an uncalibrated judge's score
  for any decision. The deterministic check wins on determinism, cost, and
  auditability; and where correctness is genuinely hard to discriminate, a frontier
  judge measured ~56.6% against a 50% pairwise-chance baseline on forced-choice
  correct-vs-incorrect items [EXT-JUDGE-002] (§4 states what that figure covers).
- **Judge trust read off a point estimate**: declaring a judge trusted because κ's
  point estimate cleared the bar while its lower confidence bound did not, or
  choosing the bar after seeing κ (§5.7 step 8, §7).
- **A bias "audit" with no number**: listing position, length, self-preference, or
  style bias as checked without a measured quantity, a pre-registered tolerance, and
  a named consequence — a detection without a consequence is not a control (§5.7
  step 3).
- **Smoke-tier results quoted as evidence**: using a minutes-scale mini-suite's
  numbers in a comparison, an adoption or elimination decision, or a reported metric.
  It is a diagnostic run kind by construction and its MDE is enormous (§5.11).
- **Pipeline-bypass content generation**: writing background/distractor content
  directly into corpus state instead of through the same generation path, leaving a
  model-visible artifact unrelated to the intended signal (§5.3).

## 10. Vendor recipes

| Verdict | Source | What it gives this chapter | As-of |
|---|---|---|---|
| [FOLLOW: EXT-TESTBED-001] | Karpathy sanity-gate recipe | Correctness-only sanity gates before scaling; formalizes §5.5 | 2026-08-20 |
| [FOLLOW: NV-EVALSDK-001] | NeMo Evaluator SDK compare/gate tooling | GO/NO-GO gate behind §7; stats mechanics are chapter 04's | 2026-08-21 (no pinned doc path — cite this date) |
| [ADAPT: NV-AGENTICBLOGS-001] | NVIDIA agentic-technique blogs | Evaluate-first framing corroborating this chapter's ordering | 2026-08-21 |
| [ADAPT: NV-TOOLCALLTUTORIAL-001] | NeMo tool-calling eval tutorial | One worked instance of §6's volume position on a deterministically gradable task family (~85/15 synthesis/independent split; 500+ samples to ~93% on a held-out golden set). **The split ratio and the independent-golden-set pattern transfer; the sample count does not** — it is a property of that tool surface (09 §6 states the same boundary) | 2026-08-20 |
| [ADAPT: NV-GARAK-001] | garak security-probing tool | Calibration-bag/z-score pattern reused for judge calibration (§5.7) | 2026-08-20 |
| [REFERENCE: EXT-TESTBED-003] | Efficient-eval / small-N reliability literature | Scalable estimators can be unreliable at small N — informs §6's corpus-size parameter | 2026-08-21 |

## 11. Worked examples

- **The helpdesk-triage running example** (§5.1, §5.3, §8.2) — a fully synthetic
  illustration of the four-layer ontology on a diagnose-and-act task: a deliberately
  ambiguous category, a distractor action, an absence case, and a forbidden claim,
  with the lookup-ceiling arithmetic worked through. §5.1's shape map says what to
  build instead when the task is classification, extraction, or generation.
- [CASE-004](examples/CASE-004_harness-defects.md) — thirteen harness/scenario
  defects, initially indistinguishable from model weakness, found by reachability
  ceilings, weak-beats-strong inversions, and cross-arm disagreement review.
- [CASE-009](examples/CASE-009_suite-versioning-criteria-drift.md) — criteria drift
  made explicit and auditable through a versioned release contract instead of
  silent in-place edits.
- [CASE-003](examples/CASE-003_learned-router-leakage.md) — structural leakage
  (class-identity ceiling) caught by leave-one-group-out validation; the same audit
  generalizes to any learned or judge-mediated grading component (§5.8).
- [SYNTH-08](examples/SYNTH-08_high-stakes-audited-deployment.md) — the
  human-annotated, judge-mediated path on a Tier-3 project: agreement measured
  against human reviewers before the judge was trusted, and a pass^k collapse
  reported instead of the flattering pass^1 number (§5.2's stochastic-reliability
  note, §5.7, §6's non-generator procedure).
- [WALKTHROUGH](examples/WALKTHROUGH_rag-document-qa.md) — the full lifecycle,
  including instrument construction, on a synthetic non-trivial project.

## 12. Outputs and artifacts

- The task ontology itself: a closed, versioned vocabulary carrying whichever of
  §5.1's layers the task shape requires, version-controlled with the suite, with the
  shape and any N/A layers stated explicitly.
- [templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md)
  — one per suite version, frozen before implementation.
- Static integrity gate results (reachability per stratum, threshold-below-ceiling
  check, determinism digest or annotation-drift check, gold-answer gate,
  frontier-saturation check) — persisted per release, not just per run.
- Canary strings embedded in any published excerpt (§5.8).
- A judge calibration report, if any judge is used: the **pre-registered κ bar and
  CI-width ceiling** (declared before scoring), measured κ + CI, the anchor set's
  human–human κ, the bias-audit table with each tolerance and its result, and the
  domain-transfer check — feeds the
  [prediction ledger](GLOSSARY.md#prediction-ledger) and the promotion gates of
  chapters 04 and 10.
- For human-annotated corpora: the annotation guideline version, annotator roster,
  adjudication rule, and inter-rater agreement — the non-generator analogue of a
  corpus digest (§6).
- Input to chapter 05 (candidate selection needs a trusted eval first) and chapter
  04 (splits, statistics, and stopping rules operate on the instrument built here).

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-EVAL-001] | Explicit criteria, grader-by-task-shape; volume position in the volume-vs-curation contradiction |
| [EXT-EVAL-002] | objective→dataset→metric→run→iterate loop; validate judges against humans (methodology citable; hosted platform sunsets 2026-11 per its own notice) |
| [EXT-EVAL-003] | Error-analysis-first ontology derivation (§5.1) |
| [EXT-EVAL-004] | Criteria drift — basis for versioned, never-mutated instruments |
| [EXT-EVAL-005] | Curation position in the contradiction; ceiling-measurement principle. Cite for the historical curation figures only — the 16%→33.2% delta is *not* decomposed into instrument defect vs. item-population change (§4), and the benchmark itself is superseded for frontier claims (see EXT-EVAL-008) |
| [EXT-EVAL-008] | The curated benchmark's own later walkback — instrument validation never ends; benchmark verdicts age |
| [EXT-EVAL-006] | Contamination effect size — leakage protection rationale |
| [EXT-EVAL-007] | Canary-string convention |
| [EXT-JUDGE-001] | MT-Bench domain caveat for judge calibration |
| [EXT-JUDGE-002] | JudgeBench — pairwise discrimination of correct vs. incorrect responses on hard items; ~56.6% against a 50% pairwise-chance baseline. A forced-choice figure; does not measure schema, exact-match, or execution-result grading (§4) |
| [EXT-JUDGE-003] | **REFERENCE (contested, new — 2026, unreplicated)** — corroborating illustration only for κ deflation vs. raw agreement; the rule itself follows from the κ formula (§8.3) |
| [EXT-AGENT-001] | pass^k reliability collapse on identical tasks — basis for §5.2's stochastic-reliability note |
| [NV-EVALSDK-001] | GO/NO-GO gate concept behind §7's release gate |
| [NV-AGENTICBLOGS-001] | Evaluate-first framing corroboration |
| [NV-TOOLCALLTUTORIAL-001] | Volume-with-independent-check worked recipe (§10); ratio and pattern transfer, sample count does not |
| [NV-GARAK-001] | Calibration-bag/z-score pattern adapted for judge calibration |
| [EXT-TESTBED-001] | Sanity-gate recipe behind static integrity gates |
| [EXT-TESTBED-003] | Small-N reliability caution for corpus-size parameter |
| [INT-CASE-003], [INT-CASE-004], [INT-CASE-009] | Case evidence — leakage, instrument defects, suite versioning |

**Gap dispositions in this chapter:**

- **G1** (task-ontology derivation from a requirement): **COVERED** — §5.1.
- **G3** (non-generator instruments): **COVERED-AS-DOCTRINE-NOT-YET-EXERCISED** —
  §6's seven-step procedure gives every §5.5 check a non-generator counterpart
  (annotation reliability, sampled-audit ceiling with a sizing rule, auditor
  independence, gold-answer gate, double-annotation drift, disagreement review,
  judge-mediated ground truth), but the procedure carries no internal execution
  record.
- **G16** (gold-label usage boundary): **COVERED** — §4, §5.4 state the boundary
  rule; enforcement mechanics are chapter 04's, structural isolation chapter 13's.
- **G19** (tool-contract design): **COVERED** for its instrument-validation half
  only — §5.5, §8.1 (reachability ceilings, evidence-requirement invariants); the
  tool-contract/schema/addressing half is primary in chapter 08, by design.
- **G20** (volume-vs-curation contradiction): **COVERED** — §6.

---

> [← Previous](02_EXECUTION_SYSTEM_MODEL.md) · [Index](README.md) · [Next →](04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
