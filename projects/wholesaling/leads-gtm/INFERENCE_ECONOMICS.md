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

## 5b. Addendum 2026-08-25b - flash-tier update (operator-supplied leads, verified)

**GLM-5.3-Flash** (z.ai), verified: promo **$0.075 in / $0.015 cached in /
$0.25 out**, promo ends **24:00 2026-09-09 UTC+8**; list reverts to
**$0.15 / $0.03 / $0.50**. Natively multimodal, **1M context**, 131,072 max
completion tokens, 320B params / 18B active on the GLM-5.2 743B MoE base.
Vendor reports approaching Claude Opus 4.8 on coding/agentic benchmarks and an
output-efficiency edge (31.4% at ~50k output tokens/task vs 29.5% at 120k).
Treat vendor benchmark claims as screening signal only.

**IMPORTANT for the operator's stated goal:** *GLM-5.3 weights are not
published yet.* GLM-5.3-Flash is therefore **not currently an open-weight
model** - it is a cheap hosted endpoint. GLM-5.2 (753B MoE) **is** MIT
open-weight. If the motive is purely cost, this does not matter; if the motive
includes self-hosting escape or a version that cannot be withdrawn or silently
updated, 5.3-Flash does not provide it and 5.2 does.

**qwen3.8 tier** (operator-supplied from qwencloud.com/pricing/api; the page
renders its table client-side so it could not be independently fetched -
treat as operator-read, verify at order time): qwen3.8-flash
**$0.16 / $0.47**, implicit cache **$0.016**; qwen3.8-max and
qwen3.8-2.4t-a95b both **$2.00 / $6.00**, implicit cache **$0.25**.
"Implicit" caching is an operational plus: no `cache_control` plumbing to
maintain, same as DeepSeek's automatic cache.

### Modeled cost for the experiment loop

Assumption: 100k input/turn, 90% cache-hit after warm-up, 2k output/turn -
the shape of an agent re-reading a large static codebase each turn.

| Candidate | $/turn | $/1k turns | Breakeven vs an $18/mo flat plan |
|---|---|---|---|
| **GLM-5.3-Flash (promo, to Sep 9)** | $0.0026 | **$2.60** | ~6,900 turns/mo |
| qwen3.8-flash | $0.0040 | $3.98 | ~4,500 turns/mo |
| DeepSeek V4-Flash (off-peak) | $0.0042 | $4.15 | ~4,340 turns/mo |
| GLM-5.3-Flash (list, after Sep 9) | $0.0052 | $5.20 | ~3,460 turns/mo |
| DeepSeek V4-Flash (peak) | $0.0083 | $8.30 | - |
| Qwen3 Coder Next | $0.0136 | $13.60 | - |
| GLM-5.3 full | $0.0462 | $46.20 | - |
| qwen3.8-max | $0.0545 | $54.50 | - |

Two readings that matter:
1. **The promo is the whole story, and it expires in ~2 weeks.** At list price
   GLM-5.3-Flash becomes the *most* expensive of the three flash options.
   Re-run this table on 2026-09-09.
2. **qwen3.8-max is ~21x the flash tier** for the same loop. Reserve max-tier
   models for judgment steps, never for bulk iteration.

### Routing caution - do not let the cheapest model author the evidence

This project's product *is* trustworthy evidence. A weak model that produces
plausible-but-wrong analysis of a pipeline run does not just waste a turn - it
writes a false finding into the lab record, which is the silent-failure class
(P11) the whole instantiation exists to eliminate. Split the lane:

| Work | Model tier |
|---|---|
| Running the harness, diffing outputs, mechanical summarization | flash tier (cheapest that passes) |
| Diagnosis, taxonomy classification, verdicts, anything entering a contract or ledger | strong tier (frontier or max-tier open weight) |

That split is ch. 08's cascade pattern applied to the lab's own workflow, and
it needs the same deterministic gate discipline: a cheap-tier output that will
inform a decision gets escalated, not trusted.

### Vision reuse (Budget B)

GLM-5.3-Flash being natively multimodal at $0.075/M input makes it a live
candidate for the **condition-vision** surface as well - potentially one
provider for both budgets. Do not adopt on price: bench it on the existing
harness (`app/vision/bench/`, exact-tier + within-one-tier accuracy + repair
MAPE) against the incumbent flash-lite model, **after** P1 fixes that harness's
own instrument defects. A cheaper vision model that shifts the tier
distribution changes `estimate_rehab`, which changes offers.

## 5c. Addendum 2026-08-27 - z.ai coding plan vs pay-go API

Source: z.ai devpack docs. **Credit formula:**
`credits = (input x in_mult + cached_input x cache_mult + output x out_mult) / 10,000`

| Model | Input | Cached input | Output |
|---|---|---|---|
| GLM-5.3 | 6.9 | 1.7 | 24 |
| GLM-5.3-Flash | 2.3 | 0.56 | 8 |

**Quotas (two ceilings apply simultaneously):**

| Tier | 5-hour credits | Weekly credits | Price |
|---|---|---|---|
| Lite | 2,000 | 10,000 | from $18/mo |
| Pro | 12,000 | 60,000 | ~$72/mo (not in docs) |
| Max | 28,000 | 140,000 | ~$160/mo (not in docs) |

5-hour credits refresh 5h after consumption (a rolling burst bucket); weekly
credits reset every 7 days from activation. **Unused capacity does not roll
over.** Supported tools include Claude Code, Cline, **OpenCode**.

### Converted to the same loop model (100k in / 90% cached / 2k out)

**8.94 credits/turn on Flash · 27.0 credits/turn on GLM-5.3 full.**

| Tier | turns/5h | turns/week | turns/mo | equivalent API @promo | @list | verdict at list price |
|---|---|---|---|---|---|---|
| Lite $18 | 224 | 1,119 | ~4,840 | $12.59 | $25.19 | plan wins (1.4x) |
| Pro ~$72 | 1,342 | 6,711 | ~29,060 | $75.56 | $151.11 | plan wins (2.1x) |
| Max ~$160 | 3,132 | 15,660 | ~67,810 | $176.30 | $352.60 | plan wins (2.2x) |

On **GLM-5.3 full** the same tiers yield only 1,604 / 9,622 / 22,452 turns/mo -
the full model burns 3x the credits of Flash.

### The three findings

1. **During the promo, pay-go API is cheaper than or equal to a plan.** Lite's
   whole monthly quota costs $12.59 at promo API rates - less than the $18
   subscription. Pro is a wash ($75.56 vs ~$72). **After 2026-09-09 the plans
   win by roughly 2x** at every tier, *if the quota is saturated*.
2. **The binding constraint may be the 5-hour bucket, not the weekly one.**
   Lite allows only **224 Flash turns per rolling 5h window**. A burst-shaped
   experiment loop (run a batch, analyze, re-run) can hit that wall while
   weekly credits sit unspent. Pay-go has no burst ceiling. Check the loop's
   shape before buying a tier on weekly math alone.
3. **A plan buys one vendor.** No cross-model bake-off, no fallback if GLM
   degrades, and the selection experiments this project needs (ch. 05 bounded
   candidate sets) require model diversity a single-vendor plan cannot serve.

### Unresolved - verify before committing

- **Pro/Max prices are not in the docs** (~$72/~$160 from third-party
  reporting). Confirm on the billing page.
- **Does the plan endpoint return real token usage?** This is the F-7 question
  again: subscription lanes in this system already return `usage={}`
  unconditionally. The credit formula is token-derived, so the numbers exist
  vendor-side - but if the API response omits them, the lab loses per-call
  accounting exactly where P2 needs it. **Test one call and inspect the
  response before subscribing.**
- MCP credit rule ("calls x output multiplier") is documented for z.ai's own
  MCP servers (Web Search / Web Reader / Zread, 1.2x each). Local file/bash
  tools in Claude Code or opencode should not bill as MCP calls - confirm, as
  this loop is tool-heavy.

### Decision rule (ch. 11 demand-ledger pattern)

Do not buy a tier on an estimated turn count. **Run pay-go through the promo
window** (it is the cheapest option anyway until 2026-09-09), log actual turns,
tokens, cache-hit rate, and burst shape, then apply a **pre-committed
trigger**:

> If sustained usage exceeds ~4,800 Flash-equivalent turns/month AND the peak
> 5-hour burst stays under the tier's bucket, buy that tier at the next renewal.
> Otherwise stay on pay-go.

This is the purchase-trigger discipline chapter 11 requires for hardware,
applied to a subscription: the ledger decides, not the anticipation.

## 5d. CORRECTION 2026-08-27 - the plan comparison in SS5c was wrong

SS5c priced plans at **standard credit rates and monthly billing** and concluded
pay-go beats them during the API promo. Both inputs were wrong, and the
conclusion inverts.

**Two distinct discounts exist; do not conflate them:**

1. **The GLM-5.3-Flash 50% API promo** (to 2026-09-09) - halves *pay-as-you-go
   list prices*. Does **not** discount the subscription fee.
2. **The off-peak 50% credit discount** - *"During off-peak hours, model usage
   is charged at 50% of the standard credit rate,"* and z.ai's docs state this
   **applies to plan credit usage**, not only to pay-go. This effectively
   **doubles a plan's capacity**.

**There is no percentage discount on the plan's sticker price** - but billing
cadence discounts apply: ~10% monthly, 20% quarterly, **30% yearly**, giving
effective monthly rates of **Lite $12.60 · Pro $50.40 · Max $112.00**.

**Off-peak window: peak is Mon-Fri 14:00-18:00 UTC+8 = 06:00-10:00 UTC only.**
Everything else - including all weekend - is off-peak. That is 02:00-06:00 US
Eastern; **effectively the entire US working day bills at half credits.**

### Corrected table (Flash, off-peak = 4.47 credits/turn, yearly billing)

| Tier | $/mo (yearly) | turns/5h | turns/week | turns/mo | API @promo | @list | Plan advantage |
|---|---|---|---|---|---|---|---|
| Lite | $12.60 | 447 | 2,237 | ~9,690 | $25.19 | $50.37 | **2.0x promo · 4.0x list** |
| Pro | $50.40 | 2,685 | 13,423 | ~58,120 | $151.11 | $302.23 | **3.0x · 6.0x** |
| Max | $112.00 | 6,264 | 31,320 | ~135,615 | $352.60 | $705.20 | **3.1x · 6.3x** |

**The plan wins decisively, even during the API promo** - 2x at Lite, 3x at
Pro/Max, doubling again once the API promo lapses. SS5c's "run pay-go through
the promo" recommendation is withdrawn.

The 5-hour burst concern also softens: off-peak Lite allows **447 Flash
turns per 5h window** (not 224), and Pro allows 2,685.

### Still verify before buying

- **Does the off-peak 50% apply to GLM-5.3/5.3-Flash, or only to GLM-5.2 and
  GLM-5-Turbo?** The general statement reads model-agnostic, but one secondary
  source describes it in terms of 5.2/Turbo, and a separate September promo
  (5.2 and 5-Turbo consuming 1x quota off-peak) is definitely model-specific.
  If 5.3-Flash is excluded, the multipliers double and Lite's advantage at
  promo API rates disappears.
- **Off-peak promotion itself expires September 2026** - re-price then.
- Whether the plan endpoint returns real token usage (the F-7 question from
  SS5c) is unchanged and still gates P2's accounting.
- Single-vendor lock-in (SS5c finding 3) is unchanged: a plan cannot serve the
  cross-model selection experiments ch. 05 requires.

### Revised decision

**Buy Lite yearly ($12.60/mo) now**, schedule heavy batches outside 06:00-10:00
UTC, and keep a small pay-go balance for (a) the cross-model bake-off a plan
cannot serve and (b) burst overflow past the 5-hour bucket. Escalate to Pro
only when the logged demand ledger shows sustained usage above ~9,700
Flash-turns/month - the trigger discipline still applies, it just starts from a
cheaper floor.

## 5e. 2026-08-27 - GLM plan purchased; should a Qwen plan be added?

**Qwen Coding Plan** (Alibaba Cloud Model Studio / QwenCloud) exists: **~$10/mo
Lite, ~$50/mo Pro**, Pro carrying **90,000 requests/month**; works with Claude
Code, Cursor, Cline, Codex, Qwen Code; **both OpenAI- and Anthropic-compatible
endpoints**. (The qwencloud pricing table renders client-side and could not be
fetched directly; tier figures are from vendor announcement and secondary
reporting - confirm at checkout.)

### The two plans bill on different axes - that is the whole analysis

| | z.ai GLM plan | Qwen Coding Plan |
|---|---|---|
| Unit | **credits** (token-derived: input/cached/output multipliers) | **requests** (token-blind) |
| Consequence | a token-heavy turn costs more | a token-heavy request costs **the same as a tiny one** |
| Caching | materially cheaper (0.56 vs 2.3 multiplier) | irrelevant to billing |
| Burst limit | 5-hour rolling bucket | per-month request pool (verify burst rules) |

**This matters specifically for this workload.** The experiment loop re-reads a
large, mostly-static codebase on every turn - very high tokens-per-request.
**Request-based billing is structurally favorable to that shape**, because the
biggest cost driver under z.ai's credit model (input volume) is free under
Qwen's. That is a real argument for the Qwen plan, independent of model quality.

But the units do not convert without measurement: vendor guidance says a
coding *task* consumes ~5-10 requests (simple) to 30+ (complex), so 90k
requests is roughly 3k-18k tasks/month depending on shape. **Which plan is
cheaper for this loop is an empirical question about its tokens-per-request and
requests-per-iteration ratios - both currently unmeasured.**

### Recommendation: not yet, and for a dated reason

1. **Zero usage data exists.** The GLM plan was purchased today. Buying a
   second before knowing whether the first saturates is anticipation over
   ledger - the exact pattern SS5c/SS5d already set a trigger against.
2. **The evaluation use case is already free.** Alibaba gives new accounts
   **1M tokens per eligible model** for 90 days (per-model, not shared). That
   funds the cross-model bake-off - "is Qwen better than GLM for my task" - at
   **$0**, and answers it empirically rather than by subscription.
3. **The redundancy argument is real but premature.** A second vendor protects
   against a quota wall or degradation mid-experiment, and the Kimi
   capacity-pause precedent shows this is not hypothetical. At $10/mo it is
   also nearly free. **Judgment call, stated openly:** the disciplined answer is
   measure-first; a defensible exception is that $10 sits below the threshold
   where a demand ledger meaningfully binds, and mid-experiment blockage has
   asymmetric cost. If the loop is about to run hard for two weeks straight,
   buying Qwen Lite as a fallback is reasonable - just record it as a
   redundancy purchase, not a capacity one, so it is not mistaken for measured
   demand later.

### The trigger to revisit (two weeks from 2026-08-27)

Log from the GLM plan: weekly credits consumed, peak 5-hour usage, tokens per
request, requests per experiment iteration. Then:

- **GLM Lite never saturates** -> buy nothing. Keep a small pay-go balance.
- **Weekly credits exhausted, bursts fine** -> the choice is GLM Pro ($50.40)
  vs Qwen Pro ($50). At equal price, **prefer adding Qwen** - same spend buys
  capacity *plus* vendor redundancy *plus* the second arm ch. 05 selection
  wants, instead of more of one vendor.
- **5-hour bucket is the wall, weekly credits unspent** -> a second plan fixes
  this better than an upgrade, because it adds a parallel bucket. Qwen's
  request pool (verify its burst rules) may have no equivalent 5h ceiling.
- **Tokens-per-request measured very high** -> Qwen's token-blind billing wins
  on structure; weight the choice toward Qwen regardless of tier math.

### Verify at purchase (either vendor)

- Whether the plan endpoint **returns real token usage** in responses - still
  the open F-7 question, and it gates P2's per-call accounting on both lanes.
- Any **per-request context/token ceiling** on Qwen's plan; token-blind billing
  usually comes with a cap somewhere.
- Whether z.ai's **off-peak 50% applies to GLM-5.3/5.3-Flash** (SS5d open item)
  - it materially changes the GLM side of every comparison above.

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
