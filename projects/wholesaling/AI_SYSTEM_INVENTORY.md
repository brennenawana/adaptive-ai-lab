# AI System Inventory — Wholesaling (as operated 2026-08-22)

> Code-verified survey of every AI surface in `~/code/wholesaling`
> (`Thrasher66099/wholesaling`), produced by Opus + Haiku subagent delegations
> under orchestrator review, 2026-08-22. This is the incumbent-evidence record
> the PROJECT_PROFILE's field 20 and the QUICKSTART routing read. Code is
> authority: path:line citations refer to the wholesaling repo at the survey
> date. Method note: the surveying agents read code and committed docs; claims
> below marked (unverified) were not independently confirmed.

## 1. Surface roster

| Surface | Task shape | Model + provider route (actual default) | Trigger path | Decision riding on output | Activation TODAY in prod | Human gate? |
|---|---|---|---|---|---|---|
| **Type-1 offer email** (`generation/llm_email.py:47`) | Generation | Router `generate`: `genserver → claude_sdk → anthropic (claude-opus-5) → codex` | Nightly `generation` stage; per-deal send (`sending/service.py:456`); blast render; UI "Generate with AI" | The literal body + subject read by a real listing agent | **LIVE.** `LLM_EMAIL_GENERATION_ENABLED="true"`, `MESSAGE_GENERATOR_URL` set; kill switch `false`; 46-address allowlist; 29 sent / 17 replied | **No** (regex compliance scan only) |
| **Conversation-panel draft** (`generation/conversation_message.py:72`) | Generation | Same route, same flag | UI only, `POST /outreach/properties/{id}/generate-message` | An editable draft | LIVE (same flag) | **Yes** — operator edits + sends |
| **Crexi income extraction** (`services/listing_income.py:81`) | Extraction | Router `extract`: `codex → claude_sdk → genserver`. **No metered tail** | `crexi_value_route.py:795`, cron `41 1,7,13,19 * * *`, `--apply` on prod | `rent_estimate.monthly_rent` → **CoC solver + gate rent bounds** | **LIVE and uniquely ungated** (no flag, no budget, no kill switch; ambient logins on `cron-mini`) | **No** |
| **CIS interpret** (`services/cis/interpret.py:665`) | Diagnose-and-act | Router `interpret`: `anthropic (opus-5) → genserver → claude_sdk → codex`, 16k tokens | Cron `*/15` (`cis-interpret.yml`); `POST /api/cis/interpret` | Proposes 17 action kinds: property facts, contacts, disposition, lifecycle advance, suppression, reply draft | **LIVE.** `cis_enabled=true`, budget 60/day; 66 proposals, 112 actions | **Yes** — unconditional per-action approve/edit/reject (0 of 112 exercised) |
| **Reply intent triage** (`flows/llm_triage.py:60`) | Classification | Router `classify`: `codex → claude_sdk → genserver → anthropic` | Tier-3 pass over low-confidence regex residue at inbound ingest | `outreach_message.intent`, ACCEPT→agreement / TIMING→callback branch | **Flag-off.** `llm_reply_triage_enabled=False`, unset in prod; every prod row is `intent_source='regex'` | n/a (would be excluded from auto-approval by design) |
| **Deal digest** (`services/deal_digest.py:168`) | Generation | Router `digest`: `genserver → claude_sdk → codex → anthropic`, 300 tokens | UI only | Headline + recommended-action text on an otherwise deterministic briefing | **Flag-off** — requires `llm_api_key`, unset in prod | **Yes** — read-only briefing |
| **Vision condition, xAI lane** (`vision/condition_vision.py`) | Classification | `RoutedVisionProvider` **pins one provider**, no fallback. `grok-4.3` @ `api.x.ai/v1`, 3×3 512px grids, ≤36 photos | `workers/enrichment.py:706`; cron `5,20,35,50 * * * *`; manual "Vet this lead" | Tier → `estimate_rehab` → **offer price**; confidence → **guardrail condition HOLD** | **LIVE, auto-armed.** `cloud_nightly.py:788` sets `vision_enabled=bool(VISION_API_KEY)`; that secret exists. 336 prod properties | **No** |
| **Condition-analysis queue, OpenRouter lane** (`services/condition_analysis.py`) | Extraction + classification (map-reduce; the REDUCE is a text LLM re-reasoning the merge) | OpenRouter `google/gemini-3.1-flash-lite-preview`, `grid_512_3x3`, cap $5/run | Operator only: UI button, CLI drain, `condition-analysis.yml` (**dispatch only, no cron**) | Writes `condition_tier`/`confidence`/repair band onto the property to **clear the HOLD without manual review** | **LIVE, operator-run.** 105 done / 14 failed, all applied, $1.02; `requested_by='local-batch-top50'` (no `OPENROUTER_API_KEY` repo secret exists) | **No** — the only surface with none |
| **Vision bench** (`app/vision/bench/`) | Evaluation | Any OpenRouter model, operator's own key per session | Tools → Image Analysis wizard; `python -m app.vision.bench` | Which model+config the prod queue defaults to; one cell can be applied to the CRM | LIVE, manual, never in CI | **Yes** — operator applies |
| **Bland conversational agent** (`voice/bland.py:114`) | Generation (spoken) | Bland.ai hosted LLM; **we send no model id** except a style preset's `model:"base"`, temp 0.7. **Script is deterministic Jinja2**, not LLM | Operator UI `POST /api/voice/{deal_id}/place` with `confirm_live:true`. No cron dials | Words spoken to a real human; qualification; opt-out | **LIVE.** `VOICE_ENABLED=true`, `VOICE_CONVERSATIONAL_ENABLED=true`, `VOICE_RECORDING_ENABLED=true`, `VOICE_AI_DISCLOSURE_REQUIRED=false`, `VOICE_COMPLIANCE_OVERRIDE=true`, `voice_compliance_lines_enabled=false`. **9 real calls, $1.252** | **Yes** — operator confirm + the unreviewed-call interlock (`voice.py:787`) |
| **Bland post-call analysis** (`generation/voice_discovery.py:207`) | Extraction (19 fields) | Bland-side second LLM pass, bundled in call price | Attached automatically in conversational mode | `disposition`→`CallOutcome`; `opted_out`→**DNC row + consent revoked**; `wrong_number`→suppression; rent/mortgage → underwriting; passed **verbatim as trusted context** into CIS interpret | LIVE on all 9 calls | **No** |
| **Inbound callback agent** (`bland.py:250`) | Generation (spoken) | Same Bland pathway + `voice_inbound.py` overlay | Agent calls back; operator-synced pathway | Same as the outbound agent; **no pre-call gate applies** | Armed-but-idle (no prod inbound rows observed) | No |
| **SF "checkmate" voice agent** (`generation/voice_checkmate.py`) | Generation (spoken) | Same | Would be a voice call type | Seller-finance pitch | **Flag-off, double-fenced.** `voice_sf_enabled=False` **and** absent from prod `allowed_call_types=["pure_buy_inquiry"]` → gate terminal-REJECTs | n/a |
| **Voice auto-improve judge** (`voice/review.py`) | Classification (grading) | Router `voice.grade` but **pinned `route=(OPENAI,)`**, no fallback: `grok-4.3`, 3000 tokens | Webhook enqueues PENDING; graded by operator endpoint or drain | Nothing operational — suggestions never auto-applied (no apply path exists) | **Flag-off.** `voice_autoimprove_enabled=False`; **`voice_call_review` is EMPTY** despite 9 gradable calls | **Yes** — operator reviews/dismisses |
| **Conversation review judge, L1** (`app/review/service.py`) | Classification (grading) | `grok-4.3` via **raw httpx, bypasses the router** | **None — `enqueue_precious_subset`/`drain_pending` have zero callers outside tests** | Propose-only CRM disposition task, never a status change | **Flag-off + unwired.** `review_judge_enabled=False`, sample/dual-grade rates `0.0`; `contact_scorecard` empty in prod **and** dev | **Yes** by construction (propose-only + operator labels) |
| **Layer-2 deep-dive runner** (`research/runner.py:137`) | Diagnose-and-act (agentic) | **Bypasses the router** — Claude Agent SDK subprocess on Claude Max, `claude-opus-4-8`, effort `high`, `max_turns=200`, Crexi MCP toolbelt | Operator UI `POST /deals/{id}/dive`; self-hosted CLI drain (`SKIP LOCKED`). **No workflow references it** | On approval, LLM-authored `target_price`/`concession_cap`/`walk_price` **overwrite the computed baseline** on `deal.strategy_assessment`; render the call task's ask/target/walk | **LIVE.** `DIVE_DISPATCH_ENABLED`/`DIVE_MODELS`/`LAYER2_REVIEW_ENABLED` all set in prod env. **94 dives: 58 approved, 36 pending** (`claude-opus-4-8` ×59, `glm-5.2` ×2) | **Yes** — operator approve/reject (**but `needs_attention` does not block approval**) |
| **Dive skeptic pass** (`research/`) | Diagnose | Same SDK, effort `medium`, tiny toolbelt | Fired by the verdict-delta guard | Tries to refute one load-bearing fact; feeds the runner's guard | LIVE with the dive | Inherits dive gate |
| **Dive evidence-audit pass** | Classification | Same SDK, `dive_runner_audit_effort` | Per-claim, `dive_audit_pass_enabled` **defaults True** | Claim tier corrections feeding the (deterministic) lint | LIVE with the dive | Inherits dive gate |
| **Genserver `/complete`** (`app/genserver/`) | Transport | Local `claude_sdk` or `codex` behind a bearer token | Any router call resolving to `genserver` | None directly | LIVE (`MESSAGE_GENERATOR_URL/TOKEN` set in prod + repo secrets) | n/a |

**Excluded as verified-deterministic** (no model anywhere): `dossier_lint`,
`services/lifecycle_classify.py` (the stage classifier),
`services/inbound_relevance.py`, `services/sales_engine.py`,
`services/sf_candidate.py`, `flows/classify.py` + `engine.py` + `nodes.py`
(`draft_reply` renders a committed template), `services/qualification.py`,
`services/lead_engagement.py`, `services/negotiation_validator.py`,
`services/draft_auto_approval.py`, `app/manager/` (hand-coded
`Counter`/threshold rules despite its design doc), `app/twin/llm.py` (an
identity function), `app/validation/harness.py`.

## 2. Measurement status — the routing-critical finding

**No AI surface has a trusted, versioned, repeatable evaluation.** Detail:

- **110 test files under `backend/tests/` reference AI/LLM terms; 47 read
  line-by-line: 47/47 plumbing, 0 evals.** They assert route/fallback order,
  refusal-vs-truncation typing, JSON-fence tolerance, prompt substrings,
  compliance gating, kill switches, DB persistence — against stubbed
  transports and canned outputs. The closest thing to a quality assertion is
  adversarial-output containment (`test_llm_triage.py:271`,
  `test_generation.py:320`, `test_honest_positioning.py:528`) — and there the
  bad output is hand-written by the test, never produced by a model.
- **Golden-corpus discipline exists in the repo, pointed exclusively at
  deterministic math**: `backend/tests/pricing/corpus_v1.json` (330 cases,
  seed 20260610), `valuation_corpus_v1.json` (139 cases, seed 20260611),
  differential oracle tests in `backend/tests/oracle/` — committed, seeded,
  versioned, weekly-gated. None involves a model. The capability to build and
  gate on corpora demonstrably exists; it has never been applied to an AI
  surface.
- **Exactly one scored harness for AI output exists**: the vision bench
  (`backend/app/vision/bench/` — exact-tier + within-one-tier accuracy +
  repair MAPE; composite `0.7·within-1 + 0.3·(1−normalized cost)`,
  `scoring.py:74,141`). Its trust defects:
  1. Golden labels live only in the `vision_golden_label` DB table
     (`store.py:31`) — nothing committed; the two runs' results (2026-07-16:
     18 models × 3 properties; 2026-07-21: 49 prod properties, ~55% exact /
     ~88% within-1, one-directional optimism bias 0/49-read-worse) exist only
     in a settings docstring and the message of commit `d96a822e`.
  2. Commit `d96a822e` adopted the bench's conclusion (default
     `grid_512_3x3`) **and rewrote the rubric in the same commit**
     (`app/vision/prompt.py`, `bench/extended.py`, `bench/reduce.py`) — the
     numbers were measured on the pre-rewrite prompt.
  3. **No prompt version exists anywhere**: no version constant in any vision
     prompt file, no `prompt_version` column on `condition_analysis_request` —
     pre- and post-rewrite verdicts are indistinguishable in the database.
  4. Never runs in CI; operator pastes a key per session
     (`Docs/IMAGE_ANALYSIS.md:176`); `Docs/IMAGE_ANALYSIS.md` is stale
     (documents `singles_768` as default vs shipped `grid_512_3x3`,
     `settings.py:1732`).
- **Committed artifacts that score real model output are narrative
  one-shots**: `Docs/deal-evaluation/examples/fl-sample-run-2026-07-08/`
  (n=6 — the system's underwriting was materially wrong on all six: 4
  false-positive deals on mirage inputs, 2 false UNPRICEABLE holds) and
  `Docs/deal-evaluation/VALIDATION_BLIND_TEST.md` (n=1; its named answer key
  is not in the repo).
- Per-surface verdicts: vision condition — **partial** (the only scored
  harness, with the defects above); CIS interpret — none automated but
  **best-instrumented for retroactive scoring** (real approve/edit/reject
  labels accumulating); outreach email generation, reply triage — **none**;
  voice — none automated (script_version/rubric_version exist; grading flags
  OFF); agent research dives — deterministic lint only, no scoring.

## 3. Telemetry — what retroactive measurement is possible

Structural gap: `app.ai.router.complete` (`backend/app/ai/router.py:56`) is
the chokepoint all providers pass through and **persists nothing**;
`Completion.usage` (`app/ai/types.py:136`) is discarded by every caller except
vision; the two flat-rate providers return `usage={}` unconditionally
(`providers/codex_cli.py:215`, `providers/claude_sdk.py:168`).

| Surface | Retroactively measurable? | Notes |
|---|---|---|
| Vision condition | **Yes, fully** | `condition_analysis_request` (`db/models.py:1219-1249`) holds model, image_config, tier, confidence, rationale, repair band, cost, tokens, latency; join `vision_golden_label` on property_id. Gaps: no prompt version, no raw response. |
| CIS interpret | **Yes, for acceptance** | `comm_intake.body` → `intake_proposal` (model/prompt_version/catalog_version/context_fingerprint) → `intake_action.review_status` ∈ proposed/approved/edited/rejected + `edited_params`. Approval/edit rates and confidence calibration queryable by prompt version. Gap: `cost_usd` hardcoded None (`services/cis/interpret.py:711`). |
| Agent dives | **Yes, for content** | `deal_research` keeps raw `dossier_md`, decision/search logs, token_usage, model_id, framework_version + operator `review_status` (ground truth). Gap: `research/accounting.py:112-118` computes cost/duration/stop_reason; `services/deal_research.py:187` drops all three. |
| Voice | Partially | Raw transcript + verbatim provider analysis + cost/latency/script_version stored; the prompt actually sent to Bland never persisted (`voice/bland.py:198`); grading flags default OFF → review tables near-certainly empty in prod. |
| Outreach email | **No — worst gap** | Sent bytes + outcomes stored, but nothing links a body to its generation. `MessageGenerated.model` stamped (`message_generator.py:449`) then discarded; `llm_email.py:157-166` builds the Email with no model/prompt field; `:90-95` silently falls back to the template on any error. **Cannot tell which sent emails were LLM-written.** |
| Reply intent | No | `outreach_message.intent_source` ∈ regex/llm + confidence, but no model id and no corrected label to score against. |

Two dead assets: `VariantVersionORM` (`db/models.py:2435`) is a fully-built
prompt registry (content hash, approval binding) referenced only inside
`app/experiments/registry.py` — nothing in the send path stamps it; the
experiments framework is statistically serious (Wilson display intervals,
Beta-Binomial expected-loss stopping rule in `verdicts.py`) but its arms are
deterministic templates, not LLM variants. `Docs/outreach_health/state.json`
committed empty since 2026-06-28.

**Single highest-leverage fix identified by the survey** (a candidate first
intervention, subject to the playbook's ladder discipline): an `ai_call` row
written inside `router.complete` (kind, provider, model served, prompt hash +
version, tokens, cost, latency, error, caller ref) — would make outreach
generation attributable, fill the voice/CIS cost holes, and make vision
prompt-version-aware without touching any lane.

## 4. Human gates currently substituting for evaluation

| Gate | Location | What it does |
|---|---|---|
| Reply-draft approval queue | `app/api/routes/flows.py:220-234` | Every AI reply draft waits for a human; auto-approval default OFF, only ever narrows the queue; dollar-amount drafts stay human. |
| CIS triage queue | `app/api/routes/cis.py:1065+,1164` | Per-action approve/**edit**/reject with `edited_params` preserved — the richest accumulating ground-truth signal in the tree. |
| Voice review interlock | `app/api/routes/voice.py:787-797,1182-1191` | No new live call while a prior live call is unreviewed — the only outbound surface with any interlock (contained the 2026-08-12 incident in 18 seconds). Email has no equivalent. |
| Dossier integrity lint | `app/services/dossier_lint.py` | Strongest automated check on real model output: 4 mechanical rules distilled from 3 operator-caught hallucinations; `block` → needs_attention + human triage. Gates, never aggregates a metric. |
| Compliance scrubber | `app/generation/compliance.py:25` | 23 prohibited patterns (46 raw fragments) over generated copy; one retry with the violation fed back, then deterministic template fallback. Safety filter, not a quality measure. |
| Review judge + operator calibration | `app/review/service.py`, `app/review/calibration.py` | Rubric v2, server-recomputed totals, operator dispositions as ground truth, judge↔operator agreement as the live metric. Architecturally right — and `review_judge_enabled` defaults False, so near-certainly producing no rows. |
| Vision bench apply | `POST …/vision-bench/properties/{id}/apply` | Operator applies a winning model's verdict (`condition_source = "vision_bench:<model>"`). |

**The one AI surface with no human gate:** condition-analysis
(`app/api/routes/condition_analysis.py:5`) exists to clear the guardrail
condition-HOLD "without manual review" — `apply_condition_verdict`
(`app/services/condition_analysis.py:446-470`) writes `condition_tier`,
`condition_confidence`, and the repair band straight onto the property; only
provenance and confidence-overwrite guards apply. An unmeasured-in-any-trusted-
sense model output feeds underwriting directly.

## 5. System spine and where AI plugs in

`app/orchestration/pipeline.py:run_nightly` runs six stages over SQLAlchemy
workers, offline-capable end to end. **Source** is key-free scraping and open
data (Redfin gis-csv, county ArcGIS/Socrata, BS&A) plus the paid Crexi API,
sharded across self-hosted runners with a Postgres coordination plane.
**Enrich** attaches parcel, owner, mortgage-estimate, HOA, and photo data —
and this is where the **xAI vision lane** fires, unattended, every 15 minutes.
**Value** is a comps model with a weekly leave-one-out accuracy gate; the
**Crexi rent extraction** feeds it here. **Route** is a deterministic solver
picking a strategy and price from that rent and from `estimate_rehab`, which
the **vision tier** sets. **Generate** drafts copy, where the **LLM email**
replaces the spintax template. **Guardrail** (`app/guardrails/gate.py`) is the
last hard stop: kill switch, per-lead STOP, the 23 prohibited-claim patterns,
offer sanity bounds, freshness, contact validation, calling window, consent —
and the **condition HOLD**, which only an AI vision verdict realistically
clears. Past the gate, sends are one-per-recipient throttled and
allowlist-gated; **Bland** dials from the operator's UI. Returning replies and
transcripts enter **CIS interpret**, which proposes state changes a human must
approve, and the **Layer-2 dive** runs off to the side, writing negotiation
numbers onto approved deals. Five joints total: two AI inputs to the
deterministic math (rent, condition), one AI output to humans (email, voice),
one AI reading of inbound, one advisory agent.

## 6. Observed failures (the error-analysis seed corpus)

- **FL sample run, n=6** (`Docs/deal-evaluation/examples/fl-sample-run-2026-07-08/00-README.md`):
  underwriting **materially wrong on all six** — 4 false-positive deals built
  on mirage inputs, 2 false UNPRICEABLE holds. The only committed head-to-head
  of pipeline output against independent desk research; narrative README, no
  harness.
- **Dive hallucinations** (`services/dossier_lint.py:1-30`): three
  operator-caught fabrications drove the lint's four rules — a phantom
  "50%-down carry" tell that rode **three** dossiers with no quote, date, or
  URL; an echo-built $650k→$549k→$429.9k "34% cut" ladder with one attested
  rung; a stale $650k echo from the same cache. Live trip rate: **19 of 61
  model-stamped prod dives (31%) carry `needs_attention`** — and approval does
  not check it.
- **Dive output-contract failure**
  (`docs-pending/call-batch-2026-08-12/20-SYSTEM-FINDINGS.md` §4): **7 of 20
  completed dives (35%)** ended in prose instead of the required trailing
  ```json block, so `assessment` never parsed and 12k characters of research
  never reached the phone. Same doc §8: `_OVERWRITABLE_KINDS` omitted
  `router_baseline`, so dive approvals had **silently stopped writing
  assessments entirely** — 33 approved rows vs 15 dossier assessments.
- **Voice incident 2026-08-12** (`…/60-INCIDENT-2026-08-12-live-call.md`): a
  real call at **04:19 callee-local**, recording on, no AI disclosure, into
  all-party-consent PA. Root cause: a **fail-open** posture check reading
  three keys the settings endpoint never exposed — `None` is falsy, so it
  printed `dev posture: SAFE` one line above the API's own `⚠ COMPLIANCE
  OVERRIDE ACTIVE`. Halted at +18s by the unreviewed-call interlock. A second
  incident (2026-08-13) dialed at 19:12 local against a 09:00–18:00 window,
  waived by the same override.
- **Voice compliance posture still open in prod**: the most recent live call
  (2026-08-18) logged the override bypassing the recording-consent notice in
  an all-party-consent state; and per §14 of the findings doc the opt-out
  line and callback number are **never actually spoken** in conversational
  mode — the gate validates `rendered_text` while Bland receives
  `conversational_task`.
- **Live CIS failure, unresolved**: 3 voice intakes stuck at 5–6 attempts on
  `genserver HTTP 401: invalid or missing bearer token`; no
  `ANTHROPIC_API_KEY` repo secret exists, so the `interpret` route's metered
  head is unconfigured on that runner — failing silently for days at
  one-attempt-per-UTC-day.

## 7. Overall verdict (feeds QUICKSTART routing)

- An incumbent, automated, multi-surface AI system **exists and acts on the
  world** (or is armed to): outreach copy, voice calls, reply interpretation,
  condition verdicts feeding underwriting, research dossiers feeding pursue
  decisions.
- **No trusted measurement of any AI surface's quality exists** — the only
  scored harness fails basic instrument-integrity requirements (uncommitted
  labels, no versioning, rubric rewritten in the adopting commit), and every
  other surface is unmeasured or measured only by accumulating-but-unscored
  human dispositions.
- Business decisions currently riding on unmeasured AI output: which
  properties clear the condition HOLD into pursue-eligibility (no human
  gate); what the operator reads in dossiers when deciding pursue/pass
  (n=6 sample: materially wrong 6/6); what outreach says to real
  counterparties (human-gated per message, but aggregate quality untracked and
  generation unattributable).
- QUICKSTART node 2 therefore fires on both clauses: the incumbent has **no
  established quality bar**, and **no trusted measurement of the gap exists**.
