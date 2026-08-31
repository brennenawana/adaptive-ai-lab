# Structure Design: The Consultant Repo

Compiled 2026-08-31, directly after BRIEF.md. This is a lab-internal design document —
internal names (SE-1, FIS, the lab rig) may appear HERE, but never in the product.
The rename table in §8 is the wall between the two.

Read BRIEF.md first. This document answers the four questions the brief left open:
**naming, file tree, interview flow, instrumentation approach per harness.**

---

## 1. Name — DECIDED

**`wikiskills-lab`** — the owner created the repo 2026-08-31:
https://github.com/brennenawana/wikiskills-lab (empty at creation, **private** for
now; flipping it public is the owner's switch, after the release gates in §11).

The name works in our favor: it openly credits the WikiSkill lineage (attribution
is encouraged, and the paper name is public — no internal-reference conflict), and
"lab" honestly frames what §13 adds: the repo ships a reproducible experiment,
not just a method.

## 2. Shape on disk

The user clones the repo **next to** their project, never inside it:

```
~/code/
├── their-project/          # and any other blast-radius repos, as siblings
├── their-other-repo/
└── wikiskills-lab/         # the consultant; agent session opens here
```

Everything generated for this user lands in `agent-coach/workspace/`, which is
gitignored. One rule, stated in the product: **the tool is public; your recordings
never are.** Deleting `workspace/` removes every trace.

## 3. File tree

```
wikiskills-lab/
├── README.md               # for the human: what this is, 3-step quick start, credits
├── START.md                # for the agent: the consultant's entry instructions (router)
├── CREDITS.md              # WikiSkill (arXiv:2608.27454), LLM Wiki gist,
│                           #   karpathy/autoresearch; CC BY 4.0 notice for prompts
├── CLAUDE.md               # one-line shim: "Read START.md and follow it."
├── AGENTS.md               # same shim (Codex CLI and friends)
├── .cursorrules            # same shim (Cursor)
│
├── steps/                  # the method — five numbered folders, run in order
│   ├── 1-interview/
│   │   ├── GUIDE.md        # how to run the interview (stages, override rule)
│   │   └── questions.md    # the question bank
│   ├── 2-observe/
│   │   ├── GUIDE.md        # arm the recorder, watch real tasks
│   │   └── ledger-format.md
│   ├── 3-diagnose/
│   │   ├── GUIDE.md        # findings -> ranked candidates -> user picks focus
│   │   └── scoring.md      # measurability x expected impact x effort
│   ├── 4-measure/
│   │   ├── GUIDE.md        # metric + task suite + baseline + headroom check
│   │   └── contract-template.md   # the generated rules: budgets, run counts,
│   │                              #   stop rules, escalation — approved, not authored
│   └── 5-improve/
│       ├── GUIDE.md        # the gated loop; artifacts = any text-shaped change
│       └── prompts/        # verbatim WikiSkill role prompts, attributed (CC BY 4.0)
│
├── harness/                # specialization notes, loaded AFTER discovery
│   ├── claude-code.md
│   ├── cursor.md
│   ├── codex-cli.md
│   ├── openhands.md
│   ├── custom-pipeline.md  # script/bot that calls a model endpoint (ticket->agent)
│   ├── fallback.md         # any harness we don't know: self-reported ledger
│   └── how-to-add-one.md   # community contributions
│
├── engine/                 # runnable code, Python 3.10+, few dependencies
│   ├── gateway/            # model access: local OpenAI-compatible / CLI / API
│   ├── proxy/              # the recorder-replayer (see §6 — one binary, three jobs)
│   ├── budget/             # fail-closed meter + test-looks log
│   ├── capsule/            # freeze, verify, replay task capsules
│   ├── evolve/             # propose -> gate -> accept/reject loop
│   └── report/             # before/after report generator
│
├── docs/
│   ├── how-it-works.md     # one page for curious humans; not required reading
│   └── glossary.md         # every term of art in one plain sentence (ESL aid)
│
├── workspace/              # ALL user-generated state; gitignored except README.md
│   ├── README.md           # what lands here; "this folder never leaves your machine"
│   ├── profile/            # interview answers, harness id, endpoints, state.json
│   ├── ledgers/            # observation records (durable, outside any conversation)
│   ├── capsules/           # frozen task capsules: fixtures, pinned SHAs, checkouts
│   ├── suite/              # metric definition, task list, scorers, baseline result
│   ├── contract/           # the generated rules the user approved
│   ├── wiki/               # persistent knowledge layer (never rolled back)
│   ├── skills/             # gated, accepted artifacts
│   └── runs/               # spend ledgers, run outputs, verdicts
│
├── examples/
│   └── ticket-bot/         # one fictional team, end to end: filled profile, a ledger,
│                           #   a diagnosis, a capsule manifest, a contract, a
│                           #   before/after report. Clearly labeled as fiction.
│
└── benchmarks/
    └── spreadsheet/        # the real, reproducible experiment (see §13):
                            #   public report, our evolved skills, results, contract,
                            #   suite adapter + fetch scripts. NO upstream data committed.
```

Design notes:

- **README.md vs START.md** — two readers, two files. The README never tries to
  instruct an agent; START.md never tries to sell a human. The quick start is
  three lines: clone next to your project; open your agent here; say
  "read START.md and follow it."
- **Numbered steps** — the order is visible in `ls` output. No step's GUIDE assumes
  you read any document outside its folder (no reading assignments).
- **Shims** — CLAUDE.md / AGENTS.md / .cursorrules make arrival automatic in the
  harnesses that auto-read those files. For everything else, the spoken one-liner
  works. This is the whole "harness-agnostic on arrival" mechanism: one canonical
  entry, many one-line doors.

## 4. START.md is a router (compaction-safe by design)

START.md logic, in plain words:

1. If `workspace/profile/state.json` exists, read it and resume at the recorded
   step — greet the user with where they left off.
2. Otherwise begin step 1 (interview).
3. Every step writes its outputs to `workspace/` **as they happen**, not at the end,
   and updates `state.json` on step completion.

The consultant never forgets where you were, no matter how many sessions or
context compactions happen between visits. (This is our own compaction lesson,
built into the product as a feature.)

## 5. Interview flow (step 1)

Five stages. At every question the agent gives a recommendation with one sentence
of reasoning; the user can override anything or say "you pick" and get the
recommendation. Answers stream into `workspace/profile/` as they are given.

- **Stage 0 — consent.** Plain-words explanation: what will happen, roughly how
  long, what gets recorded, where it is stored (this machine only), how to delete
  it. Ask permission to write into `workspace/`.
- **Stage 1 — the project map.** "Point me at your project. List every repo that
  belongs to it. What outside services does a normal task touch — ticket tracker,
  CI, cloud, anything the agent reads or writes?" Output: the blast-radius list.
  This comes first so recording can be armed for everything from day one.
- **Stage 2 — how you work.** Harness, models (names, where they run), cost
  reality (local GPU / subscription / API), one typical task narrated start to
  finish, and what already bothers them. The cost answer later selects the
  optimizer tier and sizes every budget in the generated contract.
- **Stage 3 — harness lock-in.** Identify the harness from stage-2 answers plus
  simple probes (which rules files exist, which CLIs are on PATH). Load
  `harness/<name>.md`. Tell the user honestly what can be observed automatically
  in their world and what needs a manual step (see the telescope table, §6).
- **Stage 4 — pick the first observed task.** A real ticket coming up soon, not a
  toy. Arm the recorder for it. The observed task is also the first capsule —
  observation doubles as the capsule factory.

Degrades gracefully: a user who answers only stage 1 and says "just pick for me"
still gets a working, sensible setup.

## 6. Instrumentation: the three telescopes

The per-harness problem generalizes to one doctrine: **three telescopes, use the
strongest one available, and record which one produced each ledger.**

| Grade | Telescope | What it is | Ground truth? |
|---|---|---|---|
| A | Harness-native | Hooks, transcripts, event logs the harness itself emits | Yes |
| A | Endpoint proxy | Our pass-through in front of the model endpoint (and tracker API) records every request, response, token count, latency | Yes |
| C | Self-reported ledger | The harness rules file instructs the working agent to append one line per significant action | No — self-reported, labeled as such |

Every diagnosis finding shows its evidence grade. A grade-C finding is presented
as "the agent says it did X" — never as measured fact.

**The proxy is one binary with three jobs** (this is the design's load-bearing
piece): the same `engine/proxy/` process that (1) records live sessions in step 2
also (2) records the third-party data sources for capsules and (3) replays frozen
fixtures hermetically in step 5 — record mode vs replay mode. In replay mode any
request that misses the fixture set fails closed. Auth headers and tokens are
scrubbed at write time, never stored. It speaks OpenAI-compatible
`/v1/chat/completions` and Anthropic `/v1/messages` pass-through, plus a generic
HTTP front for tracker APIs, plus a stub MCP server serving frozen fixtures
(snapshot the data source, not the exchange — agents rephrase queries, so strict
request-matching misses; a frozen fixture set behind a stub answers any
reasonable query).

Per-harness application:

| Harness | Discovery signal | Telescope plan |
|---|---|---|
| Claude Code | CLAUDE.md honored; `claude` on PATH | Native hooks write JSONL ledgers per tool call; session transcripts give token spend. Grade A without a proxy. |
| Cursor / Windsurf | .cursorrules honored | No public hook API. Models reached over API -> proxy in front where configurable; else self-report. Grade A/C mix, said honestly. |
| Codex CLI | AGENTS.md; `codex` on PATH | Base-URL config -> proxy. Grade A. |
| OpenHands | its config files | Event log (native) + proxy. Grade A. |
| Custom pipeline (ticket->agent script) | User says so in interview | The pipeline already calls an endpoint -> point it at the proxy; put the tracker API behind the generic front. Grade A. **This is the first recipient's exact case.** |
| Unknown harness | fallback | Rules-file self-reported ledger. Grade C, labeled. |

## 7. First-mile acceptance test

The repo is not done until this exact path works end to end, because it is the
first recipient's world: self-hosted Qwen-class ~27B behind an OpenAI-compatible
endpoint (vLLM/Ollama-class), a ticket->agent pipeline, no existing eval process.
That path exercises: shim-less arrival (spoken one-liner), custom-pipeline
harness notes, proxy telescope, tracker stubbing, the **local-only optimizer
tier**, and generated governance sized to a GPU-hours cost reality instead of
dollars.

Local-tier honesty (from evidence, cited publicly only via the WikiSkill paper):
self-evolution with a small local model works but is less reliable run to run, so
the generated contract for local tier prescribes more seeds and more conservative
stop rules. The product says this plainly at tier-selection time.

## 8. Engine: what generalizes from the lab, and the rename wall

| Lab (never in product) | Product | What changes |
|---|---|---|
| `rig/gateway.py` (subscription CLI pattern) | `engine/gateway/` | Becomes pluggable: OpenAI-compatible local endpoint FIRST, then CLI, then API — chosen by interview |
| `rig/budget.py` + max-of-accountings lesson | `engine/budget/` | Same fail-closed meter; unit can be dollars, tokens, or GPU-hours per interview |
| look ledger | `workspace/runs/looks.jsonl` — "test-looks log" | Same rule: pay before you look; continuation rule kept |
| SE-1 contract (hand-frozen) | `workspace/contract/` generated from `steps/4-measure/contract-template.md` | Approved, not authored |
| `rig/orchestrator.py` + `rig/proposer.py` | `engine/evolve/` | Same 3-layer / 4-role loop, strict-improvement gate; verbatim paper prompts move to `steps/5-improve/prompts/` with attribution |
| eval checkpointing, `.replace()`-not-`.format()`, retry-on-transport-only | carried into `engine/` as-is | Hard-won; keep |
| session telescope (internal phrase) | "the recorder", step 2 | |
| RUNBOOK incident table + never-decide-alone rules | folded into each step GUIDE | No separate runbook to read |
| machine-sizing lesson (~12–15 concurrent processes / 16 GB) | pre-launch RAM check in `engine/evolve/` + one line in step-5 GUIDE | |
| FIS, SE-1, wholesaling, millwork, battery, playbook | — | Do not exist in the product. `grep -ri` for each is a release gate. |

## 9. Worked example (`examples/ticket-bot/`)

A fictional two-person team with a fictional tracker. Every artifact the journey
produces appears filled in: profile, one observation ledger, a diagnosis with
ranked candidates (one is the classic "linked tickets pulled in whole, ~100K
tokens" process finding — genericized), a capsule manifest with fake fixtures, a
generated contract, and a before/after report. Labeled fiction on every page.
Purpose: the user sees the destination in five minutes of scrolling, before
answering a single question.

## 10. Attribution (no license file — owner decision 2026-08-31)

- **No LICENSE file.** The owner declined one: the repo is private, and a
  license only grants rights to other people. Implication recorded for the
  future public flip: with no license, default copyright applies — visitors can
  read and fork on GitHub but have no legal right to reuse the code. That is a
  valid choice, revisitable later or never; nothing in the build depends on it.
- `steps/5-improve/prompts/`: WikiSkill's prompts are CC BY 4.0 — that is the
  paper authors' license condition for carrying their text, not our choice, so
  that directory keeps its own NOTICE regardless, and CREDITS.md repeats it.
- CREDITS.md also cites the LLM Wiki gist and karpathy/autoresearch as lineage.
- Our own experiment numbers appear only in the §13 case study.

## 11. Build order

1. **M1 — skeleton + arrival.** Tree, README, START router, shims, interview step,
   workspace contract, glossary. Usable on day one (interview alone has value).
   Pushes to the (private) GitHub repo from the start.
   **DONE 2026-08-31 — pushed as the repo's root commit `65bd4d5` on `main`**
   (32 files, incl. the §13 case study, harness notes for stage-3 lock-in, and
   honest stubs for steps 2–5). The build clone lived in session scratch space;
   GitHub is canonical — clone fresh to continue. Release-gate grep (internal
   names + the never-written word) passed before the push.
2. **M2 — the recorder.** Proxy (record mode), Claude Code hooks pack, ledger
   formats, step-2 GUIDE. First real observation possible.
3. **M3 — diagnosis + measuring stick.** Step-3 scoring, step-4 suite builder,
   contract generation, baseline runner (gateway + budget land here).
4. **M4 — capsules + the loop + the benchmark.** Freeze/replay (proxy replay
   mode), evolve engine, gate, report generator. The spreadsheet benchmark (§13)
   ports here — it is the engine's integration test, so it lands with the engine.
5. **M5 — worked example + release gate.** ticket-bot example, internal-name grep
   gate, first-mile path test (§7), redistribution check (§13), polish pass in
   ESL plain language. Only after M5 passes does the repo flip to public.

## 12. Open decisions for the owner

1. ~~Repo name~~ — decided: `wikiskills-lab` (§1).
2. ~~GitHub account~~ — decided: github.com/brennenawana/wikiskills-lab.
3. ~~Code license~~ — decided: none (§10).
4. When to flip the repo from private to public — recommendation: after M5.

## 13. The spreadsheet benchmark (owner-approved public case study)

Owner decision 2026-08-31: the lab's spreadsheet experiment ships in the public
repo. This supersedes the brief's "our numbers only via a future public write-up"
line — this IS that write-up. It lives at `benchmarks/spreadsheet/` and doubles
as the engine's integration test: anyone can re-run the loop and check that the
machinery works before trusting it on their own project.

**What ships (already ours, already done):**

- `REPORT.md` — a public rewrite of the frozen lab report: self-contained,
  internal names stripped, plain language. The story it tells: a cheap executor
  went 36% → 76% (frontier-guided) / 63% (self-evolved) on 100 held-out
  spreadsheet tasks, p < 0.001, at ~3× lower inference cost per solved task;
  frontier optimization bought run-to-run reliability. Cites the WikiSkill paper
  as the method source.
- `skills/` — the evolved skill texts we authored, including the winning one
  (write values, not formulas; use the workbook's own worked example as the
  oracle). These are the best possible advertisement: a reader sees exactly what
  the loop produces.
- `results/` — verdict JSON, per-arm and per-seed numbers, spend summary, the
  pre-registered stats as run.
- `CONTRACT.md` — the frozen pre-registration, adapted for public reading
  (internal file names stripped, content otherwise faithful). Shows what
  "generated governance" looks like when filled in for real.
- `adapter/` — the suite adapter wiring `engine/` to the benchmark's task format
  and checker, plus the run scripts.

**What must NOT ship (hard rule):** the upstream benchmark has **no license
file**, so we never commit or redistribute its task data (workbooks,
instructions) or its checker code. Instead: `fetch_data.py` downloads the data
from the upstream source and the checker at a **pinned upstream commit**, verifies
checksums, and stores everything under gitignored `benchmarks/spreadsheet/data/`.
The README there explains this in one plain sentence ("we point at their work; we
do not copy it") and credits the benchmark's authors. The M5 release gate
includes a redistribution check: no upstream-authored file in git history.

**Rewrite cost (the honest "not quite free" part):** the report and contract need
one adaptation pass — strip lab references, make every concept resolve inside the
repo, ESL polish. The code port was already planned as `engine/` (§8); the
adapter is the only new code, and it exists in the lab rig today.

**Status: the adaptation pass is DONE (2026-08-31).** The finished public content
is staged at `projects/agent-consultant/staging/benchmarks/spreadsheet/`:
README, REPORT.md, public CONTRACT.md (with a stop-code legend added), the
winning skill verbatim plus a provenance README, and sanitized results (the
internal contract codename in VERDICT.json / test_looks.jsonl was renamed to
`spreadsheet-v1`; every number unchanged). The internal-reference grep passes
over the whole folder. It moves into the repo as `benchmarks/spreadsheet/` —
only `adapter/` and `fetch_data.py` remain, landing with the M4 engine port.
