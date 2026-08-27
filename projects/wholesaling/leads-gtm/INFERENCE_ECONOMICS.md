# Inference Economics & Visibility — Open-Weight Models for the Iteration Loop

> Decision note, 2026-08-25 (playbook ch. 11 economics · ch. 02 execution-system
> identity · ch. 05 runtime regimes). Operator question: use open-weight models
> (Qwen-class) to keep costs down across many iterations — which platform, and
> will visibility be sufficient for the playbook's processes?

## 1. CORRECTED FRAMING (operator, 2026-08-25)

An earlier draft of this note argued that inference cost is not the binding
constraint because the pipeline's dominant error (T+I 5-6.7x) is deterministic.
**That reasoning was wrong about where the cost lands.** The operator's actual
constraint:

> The expensive thing is not the pipeline's internal AI calls. It is **the
> agent that runs and analyzes the experiments** - executing ingest against
> many properties, reading results, tweaking, re-running, and diagnosing which
> part to improve. That loop runs many times per iteration. And because Claude
> Code is the operator's primary daily-work tool, spending it on this loop
> risks exhausting a weekly subscription limit that their income depends on.

Both halves are correct and they compound. The workload to price is an
**agentic coding/analysis loop over a large, mostly-static codebase context**,
not the per-property model calls inside the pipeline. Requirements: strong
tool-calling, long context, sustained repetition, and - critically -
**a supply that is isolated from the Anthropic subscription**.

The deterministic point survives only in a narrow form, recorded because it is
the single largest cost lever available: **most of the experiment loop should
be a script, not an agent turn.** Have the agent write the harness once
(pull -> run -> diff -> summarize), then run the harness repeatedly and hand the
agent only the summary. An agent re-reading raw pipeline output on every
iteration is the expensive pattern; the same loop driven by a committed script
costs near-zero regardless of model. This is the same principle the playbook
applies to grading (deterministic wherever checkable, P11).

## 2. Where spend actually lands (two separate budgets)

**Budget A - the experiment/analysis agent (the operator's real concern).**
Scales with iteration count and context size. This is the lane to move off the
Anthropic subscription.

**Budget B - the pipeline's own AI calls.** Only two AI values reach an emitted
offer, and one agentic surface dominates:

| Surface | Volume driver | Cost character |
|---|---|---|
| Condition vision | whole book (22k properties) | ~$0.0025/property on a flash-class model => ~$55 book-wide |
| Rent extraction | per Crexi listing | trivial tokens; free-transport-only by design |
| Deep-dive research | per deal, operator-triggered | ~$8/run - 100x everything else per unit |

Budget B is small and already cheap; Budget A is the one to optimize.

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

## 5. Pricing - researched 2026-08-25 (verify at order time)

All figures per million tokens, USD, as-of **2026-08-25**. Prices move; re-check
before committing and record the as-of date in a demand ledger (ch. 11's
standing rule: recorded prices are floors with weeks of shelf life).

**Metered API (agent-driver candidates):**

| Model | Input | Output | Notes |
|---|---|---|---|
| **DeepSeek V4-Flash** | $0.22 off-peak / $0.44 peak | $0.66 / $1.32 | **cache hits $0.007 off-peak** (~97% cut). Peak = 01:00-04:00 & 06:00-10:00 UTC, **Mon-Fri only**; all other hours incl. weekends are off-peak |
| **DeepSeek V4-Pro** | $0.66 cache-miss / $0.022 cache-hit (off-peak) | $1.98 off-peak | peak = 2x; 80.6% SWE-bench Verified, MIT |
| **Qwen3 Coder Next** | $0.12 | $0.80 | cheapest coder-specific option found |
| **Qwen3.5 Flash** | $0.10 | $0.40 | |
| **Qwen3.5 Plus** (1M ctx) | $0.40 | $2.40 | |
| **Qwen3.8 Max** (flagship, rel. 2026-08-03) | $2.00 | $6.00 | the "Qwen 3.8" the operator named |
| **GLM-5.2** (MIT, 753B MoE, 1M ctx) | $1.40 official z.ai / **$0.41 via OpenRouter** | $4.40 / $1.29 | cached input $0.26 |

**Flat-rate coding plans (isolate from the Anthropic limit):**

- **GLM Coding Plan**: ~**$18/mo** entry, rising to ~$72 / ~$160 by tier;
  weekly credits that refresh every 7 days; GLM models only. Marketed for
  Claude Code, Cursor, Cline, **OpenCode**, Kilo, Roo.
- **Kimi**: plan **paused for new signups** - K3 demand exhausted Moonshot's GPU
  capacity within ~48h of launch. Existing tiers Y49-Y699. API still open.
- **DeepSeek**: **no coding plan has ever existed** - pay-as-you-go API only.
  Publishes both OpenAI-format **and Anthropic-format** base URLs.

**Free evaluation quota:** new Alibaba Cloud accounts get **1M tokens per
eligible model** (not shared across models) for 90 days on the International
(Singapore) endpoint - across dozens of Qwen models that is tens of millions of
free tokens, which makes it the cheapest place to run the *selection* bake-off.
The Chinese-Mainland (Beijing) endpoint is 60-70% cheaper than Singapore, with
the obvious data-residency implications for property/owner data.

**Agentic capability, Aug 2026 (for candidate shortlisting, not adoption):**
Kimi K3 leads open weights (88.3 Terminal-Bench 2.1, 81.2 FrontierSWE, 2.8T/104B
active, 1M ctx); GLM-5.2 is the strongest MIT-licensed (62.1% SWE-bench Pro);
DeepSeek-V4-Pro 80.6% SWE-bench Verified; Qwen3.6-27B 77.2%. Treat these as
*screening* signal only - benchmark worship is a named playbook anti-pattern,
and none of these measures your task.

**Empirical confirmation of the aggregator hazard (SS4):** GLM-5.2 on OpenRouter
spans **$0.41 to $3.00 input across 25 provider backends** - a ~7x spread for
one model name. That price spread is itself evidence that the served artifact
differs (quantization, config, context handling). Pin the backend, or the arm's
identity is not frozen.

## 6. Recommendation

**Two lanes, both off the Anthropic subscription.**

1. **Flat-rate daily driver: GLM Coding Plan (~$18/mo) in opencode.** Predictable,
   no per-run metering anxiety, explicitly supports opencode/Claude Code-style
   tools, and completely isolates the experiment loop from the weekly Anthropic
   limit. This is the direct answer to "don't burn my work tokens."
2. **Metered bulk lane: DeepSeek V4-Flash, off-peak, with prompt caching.** The
   experiment loop re-reads a large, mostly-static codebase context on every
   iteration - the ideal cache-hit shape. At **$0.007/M cached input off-peak**,
   and with US working hours falling entirely in off-peak, long repetitive runs
   are close to free. Use this when the flat plan's weekly credits run dry.
3. **Run the selection bake-off on Alibaba's free per-model quota** (1M tokens x
   many models, 90 days) before paying anyone.

**Sequencing that protects the methodology:**

- **Script the harness before scaling the loop.** The largest cost reduction
  available is not a cheaper model; it is not sending raw pipeline output
  through an agent on every iteration.
- **Land P2 (`ai_call` telemetry) alongside the switch**, or the cheap lane is
  as unmeasurable as the subscription lanes are today - `router.complete`
  persists nothing, and the flat-rate providers already return `usage={}`.
- **Pin exact model string + backend + quantization** per arm and record it;
  the 7x GLM spread above shows why a family name is not an identity.
- **Keep the pipeline's deterministic fallback ladders.** A cheaper model raises
  refusal/malformed-output rates; those ladders are what stop that from becoming
  a silent quality drop.
- **Open weights are methodologically better here, independent of price**: a
  pinned open-weight version + fixed seed + temp 0 is a frozen execution-system
  identity that will not be silently updated beneath a running eval, which is
  exactly what ch. 02 requires and what hosted frontier endpoints cannot promise.

**Sources (as-of 2026-08-25):** deepseek.ai/pricing, benchlm.ai (DeepSeek/Qwen
API pricing, agentic leaderboard), pricepertoken.com (Qwen3 Coder Next, GLM-5.2),
openrouter.ai/z-ai/glm-5.2, inferencehub.org (Alibaba free tier/regional),
mindstudio.ai (open-model coding plans), felloai.com (Qwen3.8 Max).
