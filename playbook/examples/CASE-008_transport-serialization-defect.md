# CASE-008: Transport Serialization Defect in a Routing Passthrough

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-008 · **Date:** 2026-08-16 · **Cited by:**
[02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) ·
[08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md)

## Situation

The project had built a deterministic weak→strong cascade candidate and needed a
routing gateway to sit between the orchestrator and the locally served,
grammar-constrained specialist model before that gateway could be trusted with
escalation traffic. The chosen gateway, NeMo Switchyard `0.2.0`, was configured as a
single `type: model` passthrough route (`infra/switchyard/routes.yaml`, one route
`fis-local-specialist` → the model server on port 8082) — no retries, no fallback, no
timeout logic on that route type, and the client-side adapter (`SwitchyardAdapter`)
reused the same `build_body` call as the direct path, so the outgoing HTTP request
was expected to be byte-identical on both paths. The go/no-go rule pre-registered
for this step, taken from the routing design guide, was explicit: "Keep Switchyard
if R1 equivalence holds."

## Decision faced

Whether a network hop advertised as a transparent passthrough could be trusted as
semantically invisible to the [execution system](../GLOSSARY.md#execution-system) —
i.e., whether comparisons and cascade decisions made on the direct-served model
would still hold once that model was served through the gateway — before building
any further routing logic on top of it.

## Evidence

Experiment R1 ran a same-session trio of paired dev-split runs (n = 48 each, same
case order, one model-server session, `--prompt cause_action_directed`):
`R1-direct-dev` and `R1-direct2-dev` (two current-adapter direct runs, back-to-back,
establishing the within-session reproducibility floor) and the routed arm
(`R1-switchyard-dev`). A separate, cross-session historical control
(`E6-C-directed-dev`, the pre-refactor adapter, recorded on an earlier server
process the same day) plays no part in the Switchyard comparison itself — which
pairs the same-session `R1-direct2-dev` against `R1-switchyard-dev` — and is used
only to establish that two local runs are comparable case-by-case solely when
produced in one server session: run against the same-session `R1-direct-dev`, that
historical control's output tokens differed on all 48 cases despite identical input
tokens, with 23/48 scored outcomes flipping across the restart alone. Comparison was
made per-scenario with a dedicated route-comparison script (output digest, scored
outcome, tokens, stop reason, latency, routing-metadata coverage) — not by aggregate
pass rate alone.

A byte tap between Switchyard and the model server showed the forwarded request body
was the same length and semantically equal, but **every JSON object's keys had been
re-sorted alphabetically** (the proxy's `serde_json` serializer ran without
`preserve_order`). The response schema's `properties` therefore arrived alphabetical
instead of in their declared order (`case_id, classification, root_cause, facts,
hypotheses, recommended_next_action, escalation_required, uncertainties, summary`).
The model server compiles that JSON schema into a GBNF grammar that enforces
*property order*, so the alphabetically reordered schema forced the model to emit
`facts` before `root_cause`; under greedy decoding, the generated text diverged from
the very first constrained token onward.

## What happened

Every ordinary transport-health signal looked clean or nearly so: response bodies
matched in byte length, `usage`/`timings`/`finish_reason` fields were verbatim, no
`x-switchyard-*` error headers appeared, and token accounting reconciled to the exact
token (117,426 input / 62,627 output on both the routed run's trajectories and
Switchyard's own routing log). Transport overhead — the number an operator would
normally watch — was **+4 ms mean on 12.7 s calls** (p50 132 → 132 ms, mean
138.9 → 142.7 ms, max 244 → 248 ms): negligible, and gateway-reported routing
overhead was under 1.5 ms. None of that surfaced the defect.

Only byte-level output-digest comparison did:

| quantity | direct (control) | via Switchyard | Δ |
|---|---|---|---|
| exact output digest equal | — | **0/48** | every single case differed |
| identical scored outcome | — | **34/48 (70.8%)** | 14/48 cases changed |
| identical token counts | — | 1/48 | |
| strict all-pass | 14 (29.2%) | 11 (22.9%) | −3 |
| root cause correct | 31 (64.6%) | 28 (58.3%) | −3 |
| verifier pass | 37 (77.1%) | 39 (81.2%) | +2 |
| evidence recall (mean) | 0.606 | 0.655 | +0.049 |
| no scoreable output | 5 | 4 | −1 |

The changes ran in **both directions** — root-cause accuracy fell, verifier pass and
evidence recall rose — so the aggregate all-pass rate moved by only 3 cases even
though 14/48 individual outcomes flipped and 0/48 outputs were byte-identical. A
monitor watching only the headline pass rate, or a spot check of a handful of cases,
would have had a real chance of missing this entirely; the defect is visible only in
the 0/48 digest-equality row.

**Root cause, confirmed statically.** Re-sending the direct request with only the
schema keys sorted reproduced the routed run's output byte-for-byte. Using the model
server's own schema-to-grammar compiler: `grammar(sorted(schema)) != grammar(schema)`
— proof the ordering, not any other field, was the causal factor.

**Fix (commit `11ff23f`).** The client-side adapter was changed to rewrite every
object schema in the outgoing request — the response format schema and any tool
parameter schemas — into an `allOf` list, one property per array component, optional
properties wrapped in `anyOf`, `additionalProperties` dropped. The grammar compiler
builds an object rule from `allOf` by appending each component's properties in
*array* order, and arrays are not reordered by the proxy's key-sorting serializer.
Static check: `grammar(sorted(rewritten_schema)) == grammar(plain_schema)`. The
direct path was left untouched — it still sends the plain schema it was baselined
with — and the model's reasoning phase was preserved (see rejected alternative,
below).

**Verification, same session, primed before each arm, nothing else on the model
port:**

| pair | digest equal | outcome equal | tokens equal | all-pass | verifier | model p50 |
|---|---|---|---|---|---|---|
| direct2 → switchyard (unperturbed) | **48/48** | **48/48** | **48/48** | 14 = 14 | 37 = 37 | 12,734 → 12,745 ms (+11) |

Token accounting again reconciled to the exact token on both arms. The routing
gateway's own metadata record was present on every routed call (`selected_backend`
correctly left empty for a passthrough success) and absent on every direct call —
confirming the two paths were otherwise identical in everything the operator could
observe except the one thing that mattered.

## The generic lesson

**Portable rule: a "transparent" hop in front of a schema/grammar-constrained model
must be verified byte-identical end to end before it is trusted, and that
verification cannot be aggregate-accuracy monitoring — it must be an explicit
equivalence check (byte tap, output-digest comparison) run against the real
constrained decoding path.** Latency, error rate, and even the pass-rate mean can all
look healthy while a serialization-order change silently reroutes individual case
outcomes in both directions. This is the training/serving-skew class of defect named
by ML Test Score's Monitor-3 ("training and serving compute the same values")
[EXT-OPS-002]; the transport-serialization instance here — a proxy's default JSON
key-sorting behavior interacting with an order-sensitive grammar compiler — is a
previously unpublished specific case of that general class.

This case is why [tool contract](../GLOSSARY.md#tool-contract) is defined in this
playbook to include *byte-level transport fidelity* as an explicit, versioned
dimension (chapter 08) — schema and addressing correctness are not enough if
key/property order is load-bearing downstream. It is also why chapter 02 treats a
network hop as a component of the [execution system](../GLOSSARY.md#execution-system)
and requires a [comparability claim](../GLOSSARY.md#comparability-claim) to be
re-verified, not assumed, whenever any component between the caller and the model
changes — including one advertised as "just a proxy." Chapter 12's observability
discipline is why the defect was findable at all: per-case outputs and digests were
retained, not just aggregate metrics, so a targeted equivalence replay could be run
after the anomaly was suspected.

## What would NOT have worked

A client-side alternative was tried and rejected: sending a literal GBNF grammar
string (rather than a JSON schema) made the direct and routed paths agree exactly on
output — but only because it also **removed the model's reasoning phase**. The model
server applies a `response_format`-derived grammar lazily, after the model's internal
reasoning block; a raw `grammar` string is instead applied from the first generated
token, so the fix "worked" by producing a different, shorter (287-token, no
reasoning) execution behavior that silently diverged from the frozen baseline in a
new way. It restored transport equivalence while breaking behavioral equivalence —
trading one undetected divergence for another. It was not adopted precisely because
the verification standard this case establishes (byte-identical output, not merely
byte-identical wire format) caught it too.

Relying on the transport-overhead or latency numbers alone — the metrics an
infrastructure dashboard would normally surface — would also not have worked: both
looked negligible (+4 ms mean) throughout, in both the broken and the fixed
configuration.

## References

- [EXT-OPS-002] Breck et al., ML Test Score rubric (Monitor-3: training/serving skew
  — the general defect class this case instantiates).
- Governing chapters: [02](../02_EXECUTION_SYSTEM_MODEL.md),
  [08](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md).
- Glossary: [tool contract](../GLOSSARY.md#tool-contract),
  [execution system](../GLOSSARY.md#execution-system),
  [comparability claim](../GLOSSARY.md#comparability-claim),
  [frozen identity](../GLOSSARY.md#frozen-identity).
