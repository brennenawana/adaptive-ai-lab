# SCENARIO-08: Transport Serialization Defect

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) ·
[08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md)

## Situation

A public radio archive is indexing thirty years of tape. A model reads each episode
transcript and emits one structured record per segment: where the segment starts and ends,
who is speaking, what it is about, a couple of quotable lines, a confidence number, and a
one-line summary. The records go into a search index the public will use, so the fields
have to be exactly the shape the index expects — no prose, no missing keys.

The archive got that guarantee by constraining the model as it writes. The model server
takes the JSON schema for the record, compiles it into a grammar, and only allows tokens
that keep the output valid. The model cannot emit a stray sentence, because at every step
the illegal tokens are simply unavailable.

The archive then wanted to put a routing gateway in front of that model server. Not to
route anything yet — the eventual plan was to send hard episodes to a larger model — but to
get the plumbing in place first. They deployed an open-source gateway with exactly one
route configured, of the plainest kind it offers: forward this request to that model
server. No retries. No fallback. No timeout logic on that route type. And on the client
side, the code that builds the outgoing request was the *same function* on both paths. The
request going out should have been byte-for-byte the same whether it went direct or through
the gateway.

The team wrote down a go/no-go rule before testing anything: **keep the gateway only if the
equivalence check passes.**

## Decision faced

A gateway advertised as a transparent passthrough is making a claim: that it is invisible
to everything downstream. If it is invisible, every measurement taken against the direct
model server still holds after the gateway is installed, and routing logic can be built on
top of it.

The question was whether that claim is true here — before anything was built on it. In this
playbook's terms, whether the gateway is part of the
[execution system](../GLOSSARY.md#execution-system) in a way that matters, or genuinely
just wire.

## Evidence

**The experiment.** Three runs over the same 50 episodes, in the same order, against one
model-server process that was never restarted:

1. `direct-A` — the current client, straight to the model server.
2. `direct-B` — the same thing again, immediately after.
3. `routed` — the same client, through the gateway.

`direct-A` against `direct-B` measures how much two runs disagree when *nothing* has
changed. That is the floor any comparison has to clear, and here it was perfect: 50 of 50
outputs identical byte for byte. Greedy decoding, one warm server, no drift. So any
difference in the routed arm is the gateway's, not noise.

The team also had an older run of the same 50 episodes from earlier that day, made before
the model server was restarted. It played no part in the gateway comparison, and that is
the point of mentioning it: against `direct-A`, that older run produced different output
tokens on **all 50 episodes** despite identical input tokens, and 19 of 50 scored outcomes
flipped from the restart alone. Runs from different server sessions are not comparable case
by case. Only same-session pairs are. (Measuring that boundary is its own exercise —
[SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md).)

Comparison was per-episode, by a dedicated script: output digest, scored outcome, token
counts, stop reason, latency, gateway metadata. Not by aggregate pass rate.

**Everything an operator watches looked fine.** No error headers. Stop reasons verbatim.
Token accounting reconciled to the exact token between the routed run's own records and the
gateway's routing log — 88,140 in, 41,905 out on both. Transport overhead, the number a
dashboard would show, was **+3 ms mean on 8.9-second calls**: p50 96 → 97 ms, mean
101.4 → 104.2 ms, max 190 → 195 ms. The gateway reported under a millisecond of its own
routing time. None of that surfaced anything.

**The digest comparison did.**

| quantity | direct (control) | via gateway | Δ |
|---|---|---|---|
| output digest identical | — | **0/50** | every episode differed |
| scored outcome identical | — | **36/50 (72%)** | 14 episodes changed |
| token counts identical | — | 2/50 | |
| strict pass | 31 (62.0%) | 29 (58.0%) | −2 |
| topic labels correct | 38 (76.0%) | 34 (68.0%) | −4 |
| speaker attribution pass | 41 (82.0%) | 44 (88.0%) | +3 |
| timestamp citation recall (mean) | 0.712 | 0.749 | +0.037 |
| no parseable record | 3 | 2 | −1 |

Read the shape of that, not just the rows. Fourteen episodes changed outcome, in **both
directions** — topic labelling got worse, speaker attribution and citation recall got
better — so the headline pass rate moved by two episodes out of fifty. A weekly quality
dashboard would have shown nothing. A spot check of five episodes would probably have shown
nothing. The defect is visible in exactly one row: 0/50 identical.

**What was actually happening.** A byte tap between the gateway and the model server showed
the forwarded request was semantically the same and structurally rearranged: **every JSON
object's keys had been sorted alphabetically.** The gateway re-serialized the body with a
JSON library whose default is sorted key order, and nobody had turned that off.

The schema's `properties` object is a JSON object. So the archive's declared field
order —

`episode_id, segment_start, segment_end, speakers, topics, quotes, confidence, summary`

— arrived at the model server as

`confidence, episode_id, quotes, segment_end, segment_start, speakers, summary, topics`.

The server compiles that schema into a grammar that enforces **property order**. So the
model was now required to emit its confidence number first, before it had written a single
thing to be confident about, and to produce quotes before it had settled the segment
boundaries. Under greedy decoding, the output diverged at the first constrained token and
never came back.

**Proved statically, not inferred.** Re-sending the direct request with nothing changed but
the schema keys sorted reproduced the routed run's output byte for byte. And running the
model server's own schema-to-grammar compiler on both:
`grammar(sorted(schema)) != grammar(schema)`. Property order was the cause; no other field
mattered.

## What happened

The fix went in on the client, not the gateway. Every object schema in the outgoing
request — the response schema and any tool parameter schemas — is rewritten into an `allOf`
list: one array element per property, optional properties wrapped in `anyOf`,
`additionalProperties` dropped. The grammar compiler builds an object rule from `allOf` by
appending each element's properties in **array** order, and a key-sorting serializer does
not reorder arrays. Static check before any run:
`grammar(sorted(rewritten_schema)) == grammar(plain_schema)`.

The direct path was left alone, still sending the plain schema it was baselined with.

Verification, same session, both arms primed, nothing else touching the model server:

| pair | digest equal | outcome equal | tokens equal | strict pass | model p50 |
|---|---|---|---|---|---|
| direct → gateway (after fix) | **50/50** | **50/50** | **50/50** | 31 = 31 | 8,910 → 8,921 ms |

The gateway's own metadata record was present on every routed call and absent on every
direct one — confirming the two paths were identical in everything observable *except* the
one marker that says which path it was.

## The generic lesson

**A "transparent" layer is a claim, and claims get tested.** Anything sitting between your
caller and your model — a gateway, a proxy, a sidecar, an SDK upgrade, a serverless shim —
is part of the [execution system](../GLOSSARY.md#execution-system) until you have shown
otherwise. Chapter 02 requires the [comparability claim](../GLOSSARY.md#comparability-claim)
to be re-established whenever any component between caller and model changes, and
"advertised as a passthrough" is not a form of evidence.

**The test has to be equivalence, not health.** Latency, error rate, token reconciliation
and the aggregate pass rate were all clean here, in both the broken and the fixed
configuration. Only paired same-session runs compared by output digest found it. Aggregate
monitoring cannot find a defect that moves individual cases in both directions.

**Byte-level transport fidelity belongs in the tool contract.** This is why
[tool contract](../GLOSSARY.md#tool-contract) in chapter 08 includes wire-level fidelity as
an explicit, versioned dimension, alongside schema and addressing. Correct fields in the
wrong order is still a contract breach when order is load-bearing downstream.

This is a specific instance of a well-named general class: the system that serves is not
computing the same values as the system you measured [EXT-OPS-002]. Chapter 12's
observability discipline is what made it findable at all — per-episode outputs and digests
were retained, not just aggregate metrics, so a targeted replay could be run once the
anomaly was suspected.

**How this lands on your project.** Find every hop between your code and the model, and
count the ones you have actually tested rather than assumed. Then run the cheapest version
of this experiment: the same fixed inputs, twice through the old path back to back to
establish your noise floor, once through the new path, compared by hashing the output — not
by scoring it. If you constrain generation with a schema, a grammar, or a tool definition,
you are especially exposed, because ordering and formatting choices you never think about
become semantically load-bearing. And do this *before* you build on the new layer, not
after a number moves and you go looking for why.

## What would NOT have worked

**Making the two paths agree the easy way.** One tempting fix was to stop sending a schema
and send the compiled grammar as a literal string instead — a string has no keys to sort.
Both paths then agreed exactly. They agreed because the fix had also **removed the model's
reasoning phase**: the server applies a schema-derived grammar lazily, after the model's
internal reasoning block, whereas a raw grammar string is enforced from the very first
token. The outputs matched because they were now a different, shorter behavior — about 240
tokens, no reasoning — that diverged from the frozen baseline in a new way. It restored
transport equivalence by breaking behavioral equivalence. It was rejected because the same
digest check that caught the gateway caught this too: the standard is byte-identical
*output*, not byte-identical wire format.

**Watching the infrastructure dashboard.** Transport overhead stayed at +3 ms mean
throughout — before the defect, during it, and after the fix. It was never going to say
anything. Neither was the pass rate, which moved by two episodes while every single output
had changed.

## References

- [EXT-OPS-002] Breck et al., ML Test Score rubric — training/serving skew, the general
  defect class this scenario is one instance of.
- [SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md) — why only same-session
  runs were comparable case by case, and how that boundary is measured.
- Governing chapters: [02](../02_EXECUTION_SYSTEM_MODEL.md),
  [08](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md),
  [12](../12_OBSERVABILITY_LEARNING_AND_PROMOTION.md).
- Glossary: [tool contract](../GLOSSARY.md#tool-contract),
  [execution system](../GLOSSARY.md#execution-system),
  [comparability claim](../GLOSSARY.md#comparability-claim),
  [frozen identity](../GLOSSARY.md#frozen-identity),
  [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control).

---

> [Index](../README.md) · [Examples](README.md)
