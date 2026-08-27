# Inference Economics & Visibility — Open-Weight Models for the Iteration Loop

> Decision note, 2026-08-25 (playbook ch. 11 economics · ch. 02 execution-system
> identity · ch. 05 runtime regimes). Operator question: use open-weight models
> (Qwen-class) to keep costs down across many iterations — which platform, and
> will visibility be sufficient for the playbook's processes?

## 1. First, the reframe: the dominant known error has no LLM in it

The largest measured defect in this system — **taxes + insurance understated
5×–6.7× on every FL property** — is produced by `underwriting/area_costs.py`,
committed millage/insurance CSVs, and `taxes.py`. **Zero LLM involvement.** So
are ARV (`valuation/engine.py`, explicitly no LLM anywhere in `app/valuation/`),
comp selection, the rehab formula, rent tiers 2–4, and every solver.

Iterating on those costs **$0 of inference at any model price**. Choosing a
cheaper model does not make that loop cheaper, because that loop has no model
in it. Optimizing inference cost before the deterministic-input work is
optimizing the axis that is already free.

## 2. Where LLM spend actually lands

Only two AI values reach an emitted offer, and one agentic surface dominates
cost:

| Surface | Shape | Volume driver | Cost character |
|---|---|---|---|
| Condition vision | image → tier + confidence | **whole book** (22k properties × photos) | the only genuine volume item; already ~$0.0025/property on a flash-lite class model ⇒ ~$55 for the full book |
| Rent extraction | short prose → JSON | per Crexi listing | trivial tokens; currently free-transport-only by design |
| Deep-dive research | agentic, `max_turns=200` | per deal, operator-triggered | **~$8/run** — 100× everything else combined |
| Any eval judge | grading | per eval item × looks | scales with iteration count, not book size |

**Implication:** at book scale, vision is cheap and dives are expensive. If
cost is the concern, the lever is dive volume and eval-judge volume — not the
per-token price of the vision model.

## 3. Platform — integration cost is already zero

`app/ai/providers/openai_compat.py` is documented as serving "xAI/Grok,
OpenRouter, OpenAI, **any compatible host**", with configurable
`base_url` + key + model per registry id, `supports_images = True`, and images
sent as `image_url` data URIs — "the format every compatible host accepts."

So **any OpenAI-compatible open-weight host drops in by config alone**
(`AI_OPENAI_BASE_URL` / `AI_OPENAI_MODEL` / `AI_OPENAI_API_KEY`, or the
OpenRouter equivalents). No adapter work. That removes platform lock-in from
the decision and makes it purely price × visibility.

**Aggregator (OpenRouter, already wired) vs direct provider:**
- *Aggregator*: one key, many models, trivial A/B across candidates — ideal for
  the **selection** phase, at a markup. **Critical caveat in §4.**
- *Direct provider* (a dedicated open-weight serving host): cheaper per token
  at steady state, one pinned model, usually better determinism controls —
  ideal once a candidate is **chosen** and volume is repetitive.
- *Self-host*: only justified by the demand ledger + a pre-committed purchase
  trigger (ch. 11). Nothing here yet justifies it; the book-wide vision pass is
  a ~$55 job.

## 4. Visibility — the actual crux, ranked

For the playbook's processes you need: real token accounting, a **pinned model
identity that cannot change under you**, reproducibility controls (seed,
temperature, deterministic settings), and retained raw outputs.

| Lane | Token/cost visibility | Identity stability | Reproducibility controls |
|---|---|---|---|
| **Self-hosted open weights** | full | full — you hold the weights + quantization | best: seed, temp, sampler, logprobs |
| **Direct open-weight provider** | real usage per call | good — explicit model string; **verify quantization is disclosed** | usually seed + temp; varies |
| **Aggregator (OpenRouter)** | usage + cost per call | ⚠ **routes one model name across multiple backend providers** | inherits whatever the backend exposes |
| **Subscription lanes (Claude Max SDK / Codex CLI)** | **`usage={}` unconditionally** | ambient login, self-updating CLI/SDK | none exposed |

**The aggregator caveat is a real methodological hazard, not a nitpick.** An
aggregator may serve the same model name from different backend providers at
different quantizations and settings. Under playbook P5 that is an
**unmeasured reproducibility boundary inside a single arm** — two eval runs
"on the same model" can differ because they silently landed on different
backends. If an aggregator is used for anything decision-driving, **pin
provider routing explicitly** and record which backend served each call, or the
arm's identity is not frozen. (CASE-006/CASE-008 in the playbook are exactly
this failure shape.)

**Open weights are methodologically *better* here, independent of price.** A
pinned open-weight version + fixed seed + temperature 0 gives a **frozen
execution-system identity that will not be silently updated beneath you** —
which hosted frontier endpoints do routinely, and which is the reason ch. 02
requires a redeploy probe for managed APIs. Cost is the operator's motive;
reproducibility is the stronger argument.

**Net answer to "will I get the visibility I require": yes — strictly more
than today.** Today's worst-instrumented lanes are the flat-rate subscription
ones (`codex_cli.py:215`, `claude_sdk.py:168` both return `usage={}`
unconditionally). Any metered open-weight endpoint returns real usage, which is
an upgrade. **But visibility still has to be persisted**, and today
`router.complete` persists nothing — which is package **P2**. Switching models
without P2 buys a better *source* of telemetry and still records none of it.

## 5. Pricing — what not to take from me

Public per-token prices move faster than this document's shelf life, and this
session's model knowledge predates today. **No price figure is asserted here.**
Before committing, check current published rates directly for the specific
model *and modality* (vision-capable variants cost materially more than their
text-only siblings), then record them in a demand ledger with an as-of date —
ch. 11's standing rule is that recorded prices are floors with weeks of shelf
life and must be re-verified at order time.

Also pin the **exact** model string and quantization rather than a family name
("Qwen-3-something"): quantization is part of the execution-system identity,
and a q4 vs q8 swap is a different system producing differently-distributed
outputs at the same nominal model name.

## 6. Recommendation

1. **Do not re-platform first.** Fix supply (6/8 markets dead) and the
   deterministic T+I inputs — both cost nothing in inference and hold the
   larger measured error.
2. **Land P2 (`ai_call` telemetry) before or with any model swap.** Otherwise
   the iteration loop still cannot answer "what did that run cost, on which
   model, at which prompt version."
3. **Use the aggregator for the selection bake-off** (breadth, already wired),
   with backend routing pinned and recorded per call; move the winner to a
   direct provider for steady-state volume if per-token cost justifies it.
4. **Bench candidates on the existing harness, not on vibes** — the vision
   bench (`app/vision/bench/`) already computes exact-tier / within-one-tier
   accuracy and repair MAPE, and already ran a multi-model comparison. It is
   the right instrument for a Qwen-vs-incumbent decision, *after* its own
   instrument defects (uncommitted labels, no prompt version) are fixed by P1.
5. **Keep the deterministic fallback ladders.** Both AI inputs currently
   degrade to deterministic tiers on failure; a cheaper model raises failure
   and refusal rates, and those ladders are what stop that from becoming a
   silent quality drop.
