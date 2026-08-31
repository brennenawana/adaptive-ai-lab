# Design Brief: The Consultant Repo (working name TBD)

Compiled 2026-08-31, before repo-structure design begins. This file is the durable
record of the design conversation — written so that any session, before or after
context compaction, can resume the work from this file alone. Lab language standard
applies (plain English, ESL-readable).

## What we are building

A **standalone public repo** a developer drops next to their existing project and
opens an agent session in. It behaves like a consultant arriving on-scene: blank
slate, assumes nothing about tools, harness, subscriptions, or process. Through an
interview-driven, fully automated onboarding it discovers the environment, then
adapts to it, and guides the developer into a **measured improvement loop** for
their AI workflows ("playbook-lite": skills-focused, generated governance, no
reading assignments).

**Meta-instruction, never to be written into the product itself:** the repo's true
high-level goal is to delight the user. It shapes everything (informed defaults,
early visible wins, help-not-audit tone) but must not appear anywhere in the
product's text.

First recipient (also the lab's first external client-motion test): the owner's
colleague — self-hosted Qwen-class 27B for dev work, ChatGPT for daily tasks, no
eval process (judges by feel), workflow = "take the JIRA ticket, throw it at the
agent." His words: the system "could use some improvement."

## Hard requirements (owner-stated)

1. Harness-agnostic on arrival, harness-specialized after discovery.
2. Support both frontier-model and fully-local optimizer tiers (evidence says
   fully-local self-evolution works; frontier optimizer adds reliability).
3. Public repo. Attributions and references encouraged — cite WikiSkill
   (arXiv:2608.27454; its prompts are CC BY 4.0, attribution required), the
   LLM-Wiki gist, karpathy/autoresearch.
4. **Zero internal references.** Nothing named FIS, SE-1, wholesaling, or any lab
   file may appear. Concepts must stand alone or be reorganized until every
   reference resolves inside the new repo.
5. Very user friendly. The engineer steers as much as they want, or accepts
   informed recommendations at every step.

## The user journey (aligned, confirmed)

1. **Arrival & interview.** "Point me at your project. List the repos that belong
   to it. How do you work?" Discovers harness, models, tools, integrations —
   and maps the **blast radius** (all repos + external services a task touches)
   before anything else, so recording can be armed from the start.
2. **Observe (the session telescope).** Instrument one or more real tasks run the
   normal way. Capture everything: what the JIRA/tracker integration pulled and
   how (MCP vs API; comments; linked tickets; full vs partial), codebase
   orientation behavior (greps vs full-file reads vs instruction files),
   dependency-repo reach, token spend per step, timeline, every human
   intervention. All records go to **durable ledger files outside the
   conversation** so context compactions cannot erase them.
3. **Diagnose & choose focus.** Consolidate observations into findings. If the
   user knows what to improve, that wins; otherwise present ranked candidates
   (measurability × expected impact × effort), each with reasoning. Two worked
   examples from the owner: (a) tracker integration indiscriminately ingesting
   ~100K tokens of linked-ticket detail — process fix, measurable, pays back on
   every future ticket; (b) functions repeatedly written with fabricated/incorrect
   parameters — countable metric: functions-wrong-on-first-write.
4. **Build the measuring stick.** Handcraft the eval with the user: metric
   definition, small task suite from their real work, scorers as deterministic as
   possible (counts, token ledgers, tests-pass; rubric/judge only when nothing
   harder exists, with the judge model + prompt pinned), baseline measurement,
   headroom check. Governance is **generated, not read**: budgets sized to their
   cost reality, run counts, stop rules, escalation rules — approved, not authored.
5. **Improve, prove, adopt.** Evolution loop with a strict gate. Improvement
   artifacts are **any text-shaped intervention** — skills first, but also
   instruction-file changes, tool-use policies, context policies, config changes.
   All diffable, gated on the pre-agreed metric, rolled back if they lose. Output:
   a before/after number the user helped define, artifacts installed into daily
   work, lightweight ongoing monitoring.

## Task capsules (repeatability — owner-required, design confirmed)

Real work moves on (PRs merge, boards change) while evals must replay. Each eval
task is a frozen capsule:

- **Repo state pinned:** commit SHAs for every blast-radius repo; rollouts run in
  disposable checkouts, never the developer's live working tree.
- **Third-party state snapshotted:** external interactions recorded during the
  observed session; evals run **hermetic** — recorded data served locally, live
  calls blocked, fail closed.
- **Agent-specific insight:** snapshot the *data source*, not the exchange.
  Agents rephrase queries, so strict request-matching (VCR-style) misses; default
  is a frozen fixture set (the ticket, comments, linked tickets, GitHub objects)
  served by a local stub (stub MCP server / API shim) answering any reasonable
  query. Strict cassettes are the fallback.
- **Ground truth bound to the frozen state:** merged PR diff as reference; tests
  at the pinned commit as checker; token-ledger thresholds for process metrics.
- **Environment identity recorded per capsule:** harness/tool/model versions.
- **Hygiene:** capsule stores are local-only and ignored by the tool's repo;
  tokens/auth scrubbed at record time. The tool is public; captured worlds never
  are.
- **Staleness:** capsules and suites are versioned; comparisons valid only within
  a suite version; periodically propose re-drawing capsules from fresh work.
- The observation phase doubles as the **capsule factory** — the instrumented
  ticket yields both the diagnosis and the first frozen eval task.

## Machinery to generalize from the lab (concepts travel; names do not)

- The evolution loop: three layers (immutable traces / persistent knowledge,
  never rolled back / gated skills), four roles, accept only on strict validation
  improvement, plateau and val-100 early stops.
- Fail-closed budget meter (check before every call; projections measured, not
  estimated; caps with named consequences), look ledger for held-out evaluations,
  checkpoint/resume everywhere, per-task eval checkpointing.
- Runbook pattern: commands, standard sequences, incident table
  (symptom → action), never-decide-alone escalation rules.
- Tier delegation by reversibility and novelty (frontier creates rules and
  artifacts; strong tier orchestrates written rules; cheap tier executes
  gate-verified volume; escalate on novelty, fail closed).
- Pluggable model gateway: OpenAI-compatible local endpoints (vLLM/Ollama-class),
  subscription CLI, API — chosen per the interview.
- Verbatim WikiSkill role prompts (maintainer JSON patch ops; ReAct proposer that
  must read traces before proposing), attributed.
- Metering lesson: sum every model entry in a usage report and take the maximum
  of independent accountings — single-entry reading once undercounted 30×.
- Machine sizing: count TOTAL concurrent agent processes before parallel runs;
  a 16 GB shared host degrades hard around 30.

## Supporting evidence the builder may draw on (never cite internally in product)

Held-out result behind the whole approach: evolved skills lifted a cheap executor
36.0% → 75.7% (frontier-guided) and 62.7% (self-evolved) on a 100-task suite,
p < 0.001; ~3× lower inference cost per solved task; frontier optimization bought
per-seed reliability (70–80 vs 48–81). Public citation: WikiSkill paper results;
our numbers only via a future public write-up if the owner publishes one.

## Status and next step

Alignment confirmed through the capsule design (2026-08-31). Structure design
done same day — see `STRUCTURE.md` beside this file (naming, tree, interview
flow, three-telescope instrumentation doctrine, build order M1–M5).

Owner decisions 2026-08-31 (these update the sections above):

- **Repo exists and is named:** https://github.com/brennenawana/wikiskills-lab
  (created empty, currently PRIVATE; flips public only after the M5 release
  gates). The name openly credits the WikiSkill lineage — allowed, encouraged.
- **The spreadsheet experiment goes public** in the repo as
  `benchmarks/spreadsheet/` (STRUCTURE.md §13). This supersedes the "our numbers
  only via a future public write-up" line above — that write-up is now this case
  study. Hard rule preserved: the upstream benchmark has no license, so its data
  and checker are fetched at setup from a pinned upstream commit, never
  committed or redistributed.

Next step: **build M1** (skeleton + arrival + interview), pushing to the private
repo. The SE-1 rig at `projects/skill-evolution-mvp/` is the code quarry to
generalize from.
