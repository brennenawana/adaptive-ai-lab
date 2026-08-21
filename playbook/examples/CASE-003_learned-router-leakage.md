# CASE-003: Learned-Router Leakage Behind a Class-Identity Ceiling

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-003 · **Date:** 2026-08-18 · **Cited by:**
[03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md)

## Situation

A prior milestone ([CASE-007](CASE-007_deterministic-cascade-gate.md)) had frozen a
deterministic weak→strong [cascade](../GLOSSARY.md#cascade): a local specialist model
(Qwen3-8B Q4_K_M) answered first, and a verifier-signal gate
[escalated](../GLOSSARY.md#escalation) to a frontier model (Claude Opus 5) only on
production-observable structural failure. That gate closed about a quarter of the
quality gap but left the larger share untouched — 47 of 96 test-split cases where the
local model's answer was schema-valid, well-cited, verifier-clean, and simply wrong: a
[silent failure](../GLOSSARY.md#silent-failure) a structural gate cannot see by
construction.

The next milestone (internally "R5") asked whether a learned classifier, trained on
production-observable trajectory and answer-echo features — never on gold labels or
scenario identity — could catch that residual. The benchmark it had to work on is a
12-scenario-class investigation suite (classes named `S01`–`S12`); the project's own
pre-registered contract named the central risk up front: a router could learn *which
template this is* instead of *whether this particular answer is wrong*, and a
naively validated version of that router would still look good.

## Decision faced

Should the deterministic gate from CASE-007 be replaced or augmented by a learned
router over a 58-feature production-observable snapshot (model/runtime, verifier,
tool-trajectory, and answer-echo families), to catch verifier-clean local failures the
structural gate cannot?

The contract was frozen in two commits, both before any candidate was scored on
DEV: a skeleton (feature allowlist, grouping, cross-validation protocol, candidate
families, threshold grid, TEST-unlock mechanics) and a numeric amendment committed
after TRAIN cross-validation but before any DEV replay. A later reconciliation note
was added to the frozen contract's chance-level section after the Qwen DEV replay
and before the Nemotron one, disclosed in place as drawing only on a prior
milestone's already-published DEV numbers, not on this milestone's own candidate
result — a disclosed post-freeze edit, not an undisclosed one, consistent with this
case's own amendment-legitimacy standard. The admissibility bar was
explicit: a candidate earns eligibility only by beating a pre-registered AUC/precision
floor under **leave-one-class-out (LOGO)** cross-validation — the
[leakage audit](../GLOSSARY.md#leakage-audit) protocol chosen precisely because the
feature set could not exclude template identity outright.

## Evidence

**Feature contract.** 58 named features (model/runtime 11, verifier 16, tool
trajectory 8, answer echo 23); an explicit forbidden list barred any gold field,
`split`, `category`, `class`, `seed`, or `scenario_id`; 43 dedicated leak-guard unit
tests plus 64 pipeline tests ran before any DEV replay, plus a five-lens adversarial
audit whose core findings landed pre-DEV (its synthesis and follow-ups continued
into the DEV/TEST window).

**What the audit found anyway.** Under the case's fixed evidence bundle, four features
that are legitimately production-observable — `n_tool_calls`,
`n_webhook_history_calls`, `n_verification_calls`, `input_tokens` — are constant
within a scenario and, by 1-nearest-neighbour, identify the scenario class for 45 of
48 DEV cases; every behavioural feature (output length, reasoning length) also
clusters by template. Nothing in the allowlist *names* the class, but bundle size and
tool-call shape reconstruct it — indirect [leakage](../GLOSSARY.md#leakage).

**[Class-identity ceiling](../GLOSSARY.md#class-identity-ceiling) comparator.** A
model that predicts unsafe/safe from the scenario class alone — no trajectory signal —
scored TRAIN stratified AUC 0.892 (Qwen) and 0.936 (Nemotron). The best *eligible*
learned candidate reached 0.901 (Qwen — 0.01 above the ceiling) and never exceeded it
for Nemotron.

**Primary protocol (leave-one-class-out — the deployment-generalization test):**

| model | `lr_full` | `lr_core` | `tree` | eligibility floor |
|---|---|---|---|---|
| Qwen (pooled OOF AUC) | 0.238 | 0.253 | 0.515 | 0.60 |
| Nemotron (pooled OOF AUC) | 0.201 | 0.244 | 0.224 | 0.60 |

No candidate cleared the floor for either model. Per-fold LOGO AUC on Qwen's mixed
classes (`lr_full`): S02 0.00, S03 0.09, S05 0.60, S06 0.50, S07 0.88, S08 0.56,
S09 0.50, S10 0.00 — mean 0.39. Nothing transferred to a held-out template. Labels
were also class-clustered enough to blunt the test's own power: P(unsafe | class)
spanned 0.09 to 1.0, and the minority label had n ≤ 1 in 8 of 11 mixed Qwen classes.

**Two amendments, both disclosed as moving toward permitting a pass.** After TRAIN
cross-validation and before any DEV replay, the contract was amended twice: (1) a
secondary, deployment-matched (seed-stratified, non-grouped) protocol was registered
because the primary protocol's pooled score is provably null-biased under
class-clustered labels; (2) the a-priori utilization caps were replaced with
TRAIN-derived ones, because 61% of Qwen's verifier-clean subset was unsafe, so even
the top-ranked router needed ~33% escalation at the edge of its threshold grid — the
original caps would have rejected volume, not degeneracy. Both changes are recorded in
the contract as audit-driven amendments, in the direction of a pass, per this
playbook's [amendment legitimacy](../GLOSSARY.md#amendment-legitimacy) rule.

**Under the secondary protocol,** the frozen Qwen router reached TEST strict all-pass
78.1% (vs the deterministic gate's 50.0%) at 57.3% frontier utilization and formally
met its pre-registered TEST reading. But a random escalation of the same size (33
cases) meets the identical reading with hypergeometric p ≈ 0.59 — against a
random/class-prior null the reading has almost no power at this sample size. The
Nemotron router (77.1% vs 71.9%) did **not** meet its own reading. A post-hoc check on
the same opened look: a pure TRAIN class-prior threshold — no trajectory features at
all, just "escalate the historically hard templates" — would have caught 39 of 47
Qwen TEST cases at the same 6 unnecessary escalations, matching or beating the frozen
router using only the class label.

## What happened

The honest read, stated in the milestone's own report: the router learned *which
templates the local model fails on*, a task-difficulty prior expressed through
production-observable proxies, not a reusable signal about any individual answer's
correctness. A thin genuine within-template signal existed for Nemotron
(answer-length and reasoning-share features carried some real information) but not
enough to clear the leave-one-class-out floor. No candidate beat the class-identity
ceiling by a margin the leakage audit would accept, and the deterministic gate from
[CASE-007](CASE-007_deterministic-cascade-gate.md) remained the system's actual
routing mechanism; the milestone's own recommendation for future work was targeted
model specialization on the systematically failing templates, with a
class-difficulty-style router — explicitly described as a task-difficulty prior, not
a validated content router — kept only as an interim gate above the deterministic
one. Even judged purely on cost, the Qwen router cascade was not free: cost per
success rose 56% and median latency 2.4× versus the deterministic gate for the
disputed TEST gain.

## The generic lesson

A learned routing or gating component trained on features correlated with a
clustering unit (template, class, session, document) must clear a
[leakage audit](../GLOSSARY.md#leakage-audit) — leave-one-group-out cross-validation
scored against an explicit class-identity-ceiling comparator — before its measured
performance is believed. Pooled cross-validation under class-clustered labels is
optimistic by construction, and a single held-out "confirmation" can meet a
pre-registered numeric bar with p ≈ 0.6 against a random baseline of the same size
when the true driver is the group prior rather than the
[learned router](../GLOSSARY.md#learned-router) itself. A name-level feature allowlist
(no gold fields, no scenario id) is necessary but not sufficient: other legitimate,
production-observable features can themselves be proxies for the excluded identity,
and only an adversarial feature-provenance review surfaces that. Disclosing amendments
as moving toward a pass, rather than presenting the eventually-frozen protocol as if
it had been the only one considered, is what let the final TEST number be read
correctly — as non-informative — instead of as confirmation. Encodes:
[leakage audit](../GLOSSARY.md#leakage-audit) and
[class-identity ceiling](../GLOSSARY.md#class-identity-ceiling) (chapter 08),
[amendment legitimacy](../GLOSSARY.md#amendment-legitimacy) (chapter 04), the
volume-vs-power limits of clustered evaluation (chapter 03).

## What would NOT have worked

Trusting the deployment-matched (stratified) protocol on its own: it is exactly the
protocol under which every candidate looked strong (TRAIN AUC up to 0.92) and one
reached a formal TEST pass, while the leave-one-class-out protocol — run first, as
originally pre-registered — showed every candidate below the eligibility floor for
both models. Reading the frozen router's TEST result (78.1% vs 50.0%) as evidence
that it works, without computing the random-baseline / class-prior comparison from
the same look, would have missed that the router is statistically indistinguishable
from a router that has simply learned which templates are historically hard.
Relaxing the utilization caps without recording that the change was TRAIN-evidence-
driven, and which direction it moved the eventual verdict, would have hidden the one
fact that made the final result interpretable at all.

## References

- [CASE-007](CASE-007_deterministic-cascade-gate.md) — the deterministic gate this
  router was measured against and that remained in production.
- [EXT-ROUTE-001] FrugalGPT/RouteLLM/AutoMix/Hybrid LLM cascade literature; RouteLLM's
  near-random out-of-distribution result without task-specific augmentation is the
  closest external caution to what this case measured directly.
- Governing chapters: [03](../03_EVALUATION_FOUNDATION.md),
  [08](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md).
- Glossary: [leakage audit](../GLOSSARY.md#leakage-audit),
  [class-identity ceiling](../GLOSSARY.md#class-identity-ceiling),
  [learned router](../GLOSSARY.md#learned-router),
  [amendment legitimacy](../GLOSSARY.md#amendment-legitimacy),
  [silent failure](../GLOSSARY.md#silent-failure).
