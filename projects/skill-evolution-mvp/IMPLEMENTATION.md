# Skill-Evolution MVP — Implementation Story

This document tells how the plan became a working experiment, in time order, at a
high level. It is the companion to `PLAN.md` (what we intended) and to the run
ledgers (what the machine recorded).

Writing rule: new events are added as new sections; old sections are not rewritten,
except for language fixes. **Language standard (set by the owner on 2026-08-30):**
every document written for humans must use plain English that a technically minded
16-year-old ESL student can understand. No idioms. This document was revised once to
meet that standard on the day the standard was set.

---

## 2026-08-30 — Phase 0 begins

The owner said go. Phase 0 scope, from PLAN §5: build the rig, download and verify
the task suite, prove that the budget meter stops spending when a cap is reached,
and run a small end-to-end test (the "smoke test"). Hard limits: at most $5 of API
spend, at most 3 build sessions.

Order of work: this story file first, then the credential and data checks, then the
rig components in dependency order (budget meter → model gateway → scorer → executor
→ maintainer → proposer → orchestrator), then the free tests, and the paid smoke
test last. Cheapest useful step first — the same rule the plan uses for Phase 1.

Open items at start:
- OI-1: does the benchmark run the model once per task, or once per test case?
  (Each task can have up to 3 test cases; the answer changes cost by up to 3×.)
- OI-2: does this machine have API credentials at all?

### The credential change (mid-build)

OI-2 had a surprising answer. There was no API key, no `ant` command, and no stored
login profile — and then the owner wrote in: he does not use API keys at all, only a
Claude Max subscription. The lab had already solved this exact problem once. The FIS
project drives the Claude Code command line (`claude -p`) as its model gateway,
using the subscription login. FIS measured the right flags: a plain `claude -p` call
loads the whole Claude Code agent setup (about 33,600 extra input tokens), but with
`--safe-mode` and `--system-prompt` the model sees exactly the prompt we give it and
nothing else. One warning from FIS applies here too: never use `--bare`, because it
turns off subscription login completely.

The rig's gateway is a rewrite of that FIS pattern. The executor gets `--tools Bash`,
the proposer gets `--tools Read`, and the maintainer gets no tools plus a
`--json-schema` flag that forces its output into the correct JSON shape.

Money consequence: under a subscription, each call costs $0 extra. The budget meter
still enforces every cap, but in "list-price-equivalent" dollars — the dollars the
same tokens would cost at public API prices. This keeps consumption visible and
bounded, because the real limited resource is now the subscription's usage quota.

### The dataset was different from its documentation

Three surprises from upstream, each caught by a free test before any model spend:

1. **One test case per task, not three.** The benchmark's evaluation code expects 3
   input/answer file pairs per task. The Verified-400 download actually contains
   **one** pair per task (for 395 of 400 tasks; 5 have non-standard file names), and
   the files are named `_init`/`_golden`, not `_input`/`_answer`. The rig now detects
   which test cases exist. Result: rollout cost is about 3× lower than planned.
2. **Some tasks are broken for our purpose.** A free self-test found a task whose
   input file already equals its answer file — a model that does nothing would score
   a point on it. The suite draw now filters every candidate task: the answer file
   must match itself, and the input file must NOT match the answer. 4 of 152 scanned
   tasks were excluded.
3. **The published splits exist and match our download exactly.** The public
   microsoft/SkillOpt repository contains the exact train/val/test split (80/40/280)
   that the WikiSkill paper says it used — built from the same 400-task file we
   downloaded. Our smaller 30/15/100 suite is now drawn from inside those published
   splits (our train from their train, and so on). This keeps our results comparable
   to the published ones at lower cost. Suite manifest hash: `2f3a4d71…`,
   random seed 20260830.

### Free tests, all passed

- Forced budget overrun: the meter stopped at the Phase-0 cap on the check that runs
  *before* each call, and the ledger file stayed complete.
- The scorer was verified against the upstream checker code at pinned commit
  `49b73a94…`. The upstream code and data have no license file, so they are
  downloaded into a cache at run time and never copied into this repository.
- The task suite was drawn and its manifest hashed. The `claude` command is present
  (Claude Code 2.1.251).

Rig shape as built: 11 Python modules, about 1,100 lines. Each run gets three
directories — `raw/` (never changed after writing), `wiki/` (grows, never rolled
back), `skills/` (gated, rolled back on rejection) — and every model call goes
through one gateway function that checks the budget before spending.

One declared difference from the paper, recorded for the contract as D4: the
proposer's `read_file` and `finish` tools are replaced by the CLI's Read tool and a
schema-forced final JSON answer. A `traces/` link inside the workspace keeps the
paper's file paths working as written.

### The smoke test found three defects and cost $1.02

**Attempt 1** ran one executor conversation and stopped early, for a correct but
unhelpful reason: the no-skill model solved the single validation task (score 1.0),
which triggered the paper's own rule "stop when validation reaches 100%". Two changes
followed for smoke mode only: keep all traces for review, and add a flag that makes
the smoke test run the full loop anyway (a REJECTED gate decision still tests the
gate).

Attempt 1 also revealed the most serious defect of the day. Our meter recorded
$0.0014 for a call that the CLI itself priced at $0.042 — about 30× too low. We
caught it only because each ledger row stores the CLI's own cost figure next to ours
(a habit copied from FIS). The cause: the CLI's usage report can contain several
entries per call (one per model name variant, plus side models), and our code read
only the first one. The meter now bills the highest of three numbers — the sum of
all entries, the CLI's own total, and our own computation — so it can never
undercount again.

**Attempt 2** crashed before the proposer's first call. Cause: Python's
`str.format()` was applied to the paper's word-for-word prompt, which contains
literal JSON braces. Fixed by using plain text replacement everywhere. As a side
effect, this gave the checkpoint-and-resume code its first real test: the rerun
continued from the saved state.

**Attempt 3** ran the full loop cleanly for $1.02 list-equivalent, with every role
on the ledger:

- baseline (Haiku, 4 turns, a real 1.0 — confirmed by reading the kept trace),
- training rollout (one task passed, one failed — score 0.5),
- maintainer (Opus — wrote 5 pattern pages, the index, and the log),
- proposer (Opus, 13 reasoning turns — created the skill
  `excel_write_values_and_verify`, whose PURPOSE.md names the 4 wiki patterns that
  motivated it),
- gate (validation 1.0 vs best 1.0 → correctly REJECTED, with the full diff saved
  in `skill-impact.md`).

Two wiki findings are worth recording:

- The maintainer found, on its own, the **cached-formula-values problem**: formulas
  written by the openpyxl library carry no stored result values, so the value-based
  checker reads empty cells and scores 0. This is a real property of the benchmark
  that the eventual skills must handle.
- It also found a **defect in our own rig**: our Python environment had installed a
  newer pandas than upstream uses, which needs openpyxl 3.1.5 or newer, while we pin
  3.1.3 to match the checker. The executor then tried pip upgrades that could never
  work. This is exactly the failure class the lab already warns about — a harness
  bug that looks like model weakness — found here by the system under test. Fixed by
  pinning `pandas==2.2.0`, the same version upstream pins.
- A second maintainer pass added the pattern `fake-verification-hardcoded-
  expectations`: the failing agent had "verified" its work by printing the values it
  expected, instead of reading the actual cells. That one pattern is a good argument
  for the wiki layer by itself.

**Phase 0 exit gates:** end-to-end smoke test passed with no harness errors on the
final attempt (the two defects found on the way are what a smoke test is for) ·
checker verified against upstream at a pinned commit · forced budget overrun stops
cleanly · suite drawn, filtered, hashed, and nested inside the published splits.
Not yet tested by a real event: the S1 turn-limit rule and the S9 crash-rate rule —
the code exists, but no run has triggered them. Noted for the pilot.

Phase 0 spend: about $1.07 list-equivalent, against the $5 cap. One build session.

Next: resolve the contract's open values, make the first commit (the freeze rule
requires the contract to be committed before any training inference), then Phase 1
in the pre-registered order — the no-skill baseline and the S6 headroom check come
before any evolution spend.

---

## 2026-08-30 (night) → 2026-08-31 — Freeze, the first halt, and the parallel night

The owner set a second standard mid-day: all human-facing documents must be plain
English that a technical ESL reader can follow, and this file was revised once to meet
it. The contract froze at commit `2da2ff9` with the language standard applied.

**Phase 1 began and the stop system fired on its first real outing.** The no-skill
baseline scored 33.3% on the validation split — inside the S6 headroom band, so the
experiment was allowed to proceed. Then a routine status check showed the 100-task
TEST evaluation pacing at $0.057 per task, 1.9× the projection the $5 arm-A cap was
sized from. The run was stopped before the cap could kill it mid-flight, because a
budget halt at that moment would have lost all paid work: the evaluation step, unlike
the evolution loop, had no per-task checkpoint. Three fixes followed: evaluations now
save every finished task; an interrupted TEST look may continue as the same look (no
result was ever seen, so the no-peeking rule stays intact); and the owner raised the
caps through the contract's own amendment path (Amendment 1) with the reason on the
record. A detail worth keeping: the deepest run of the night later spent $46.15 —
$1.15 more than the original cap. Without the amendment it would have been cut off
before its best skill existed.

**Then the owner opened the throttle.** With his usage window fresh, he authorized
parallel execution (Amendment 2) after asking the right question first — are runs
truly isolated? They are, by construction: every model call is a fresh CLI process
with no session persistence, no memories, a fully replaced system prompt, and only
its own run's files. Five flows ran at once. Two more lessons came out of that:

- **The machine, not the provider, was the first limit.** At ~31 concurrent CLI
  processes, the 16 GB build host went deep into memory swap (9 GB used, 15-minute
  load 17) and the owner's other work slowed to a crawl. The concurrency sizing was
  the operator's error, not the owner's: he said 20, the flows totaled 31. Standing
  rule now in the config: check RAM and count TOTAL concurrent processes before any
  parallel launch; ~12–15 is this machine's limit when it is shared.
- **Zero rate-limit retries all night.** The provider never pushed back at this
  scale; the transport-retry code went unused.

**Results.** All six evolution runs accepted at least one skill. Every run's TEST
score landed 8–14 points below its VAL peak — the small validation split flatters,
which is exactly why the contract scores arms on TEST only. The verdict, computed by
the pre-registered statistics (`runs/VERDICT.json`):

| Arm | TEST mean (n=100) | Per-seed | Evolution cost |
|---|---|---|---|
| A — no skill | 36.0% | — | $0.72 |
| B — Haiku self-evolved | 62.7% | 81 / 59 / 48 | $40.11 |
| C — Opus-guided | **75.7%** | 80 / 77 / 70 | $86.51 |

- **Primary (C vs A): +39.7 points, 95% interval [+30.0, +49.3], p < 0.001 →
  CONFIRMED** (the pre-registered floor was +5).
- **Secondary (C vs B): +13.0 points, interval [+6.0, +20.0]** — the frontier
  optimizer beats cheap self-evolution. Look at the seed spreads: B ranged 48–81
  (one seed found the key insight fully, one partially, one missed it); C landed
  70–80 (every seed found it). Frontier discovery bought reliability more than peak.
- **Economics:** at inference time, cost per solved task fell from $0.225 (no skill)
  to ~$0.07 (either skill arm) — skills make the executor both better AND cheaper
  per attempt, because it stops wasting turns on failing approaches. The discovery
  bill ($40–87 for three seeds) is paid once.
- **Prediction register: badly under-called.** The drafted estimate for C−A was +8
  points with interval [0, +16]; reality was +39.7. Recorded for calibration — the
  next contract's estimate should weight "one dominant failure cause" scenarios
  higher.

**Qualitative review of the winning skill** (C-s1's `spreadsheet_values_and_oracle`,
200 lines, created at iteration 1 and refined twice through the gate): two ideas
carry it. First, the rule every strong seed found: compute results in Python and
write literal values — formulas written by openpyxl carry no computed values, so the
grader reads them as empty. Second, an idea only the Opus-guided runs found: many
workbooks contain their own answer key — a sheet named like "Manual Result" or a
column of already-completed rows — and the skill teaches the executor to check its
work against that built-in example before saving. Classification: general procedures
for this task family (one line names the benchmark; a client version would name the
client's file conventions instead).

**Program totals, reconciled from the ledgers:** $166.77 list-equivalent, against the
$1,000 ceiling. Six evolution runs, seven TEST looks, zero crashes, zero rate-limit
events, one operator-caused memory incident, every halt clean.

Next: the dated follow-up report in `research/` (the artifact eligible for
EVIDENCE_MAP adjudication), and the owner's Phase 3 decision — the gate to it is now
formally open.
