---
name: run-se-experiment
description: Operate a skill-evolution (SE) experiment under a frozen contract — launch, monitor, resume, handle listed incidents, compute the verdict. Written so an Opus-level session can execute it without frontier supervision. Escalate anything not listed here.
---

# Runbook: Operating an SE Experiment

This document is the compiled operating knowledge of SE-1, written by the frontier
tier once so cheaper tiers can execute reliably — the same mechanism the experiment
itself validated. Plain-English standard applies. If you are an agent running this:
follow it exactly; the escalation rules at the end tell you what you must not decide
alone.

## 1. Before anything: the ground rules

- A **frozen contract** (e.g. `SE1_EXPERIMENT_CONTRACT.md`) governs every run. You
  execute its rules; you never change them. Changes go through the owner as §18
  amendments.
- Every model call is metered and capped. Halts are normal outcomes, not failures.
- TEST is sacred: one look per arm-seed, guarded by `runs/test_looks.jsonl`. Never
  read per-task TEST results (`eval_progress.jsonl`, `eval_test.json` internals)
  before the verdict computation runs.
- All work directories are checkpointed. You can always stop; you can always resume.

## 2. Setup check (new machine or new session)

```
cd projects/skill-evolution-mvp
uv sync
uv run python -m rig.cli check            # dataset, checker, CLI present?
uv run python -m rig.cli selftest-budget  # meter halts before spending?
uv run python -m rig.cli selftest-checker # scorer sane on samples?
```

New machine notes: fetch the dataset tarball and pinned checker into
`~/.cache/skill-evolution-mvp/` first (paths and hashes in `rig/config.py`); the CLI
must be logged in on the subscription; POSIX only — use WSL2 on Windows. A different
machine is a different execution system: run a 15-task no-skill VAL probe on both
machines and compare before mixing results across hosts.

## 3. The commands

```
uv run python -m rig.cli status           # one line per run + totals + looks
uv run python -m rig.cli draw-suite       # deterministic; only for a NEW contract
uv run python -m rig.cli smoke --arm C    # end-to-end test, ~$1, phase P0
uv run python -m rig.cli run --arm B --seed 2 --phase P2 --workers 5
bash scripts/run_test_look.sh <ARM> <SEED> <PHASE> <skills_from|none> <workers>
uv run python scripts/compute_verdict.py  # after ALL planned looks are spent
```

Use the wrapper script for TEST looks: some agent sandboxes block commands containing
the word "eval", and the wrapper also keeps the look-ledger arguments in order.
Re-running `run` with the same arm/seed resumes from its checkpoint.

## 4. Standard sequences

**A new seed of an existing arm:** `run --arm X --seed N --phase P2` → wait for
DONE in `status` → TEST look via the wrapper → done. The gate rules (accept only on
strict VAL improvement; plateau stop after 3 straight non-acceptances; stop at
VAL = 100%) are enforced by the rig, not by you.

**A new phase from scratch** (order is contract law, cheapest first):
1. Freeze the contract (frontier tier + owner — not you; see §7).
2. Arm-A baseline on VAL. Check the S6 band (15–60%). Outside the band → STOP,
   report STOP-RESCOPE, wait for the owner.
3. Arm-A TEST look.
4. Pilot runs, then the S7 futility check (C − A on final VAL ≥ +2).
5. Extension seeds and remaining looks. `scripts/phase1_driver.py` shows the
   sequence as executable code.

**Parallel launches:** check the machine first — `sysctl -n hw.memsize`, count what
is already running. Total concurrent CLI processes: ~12–15 on a shared 16 GB host
(measured: 31 processes forced 9 GB of swap). Worker ceiling per flow is in
`rig/config.py`. Never split one arm's seeds across machines.

## 5. Monitoring

`status` between checks; for live watching, tail a run's `ledger.jsonl`. Ledger
events you will see: `baseline_val`, `train_rollout` (with score), `proposal`,
`gate` (score, best, accepted), `retry` (transport only — harmless in small
numbers), `halt`. Spend totals: `spend` command; if parallel runs ever make
`spend.json` look wrong, trust the per-run ledgers — `compute_verdict.py`
reconciles totals from them.

## 6. Incident table — symptom → action

| Symptom | Meaning | Your action |
|---|---|---|
| `STOPPED-BUDGET(...)` in summary | A cap did its job | Checkpoint is intact. Report which cap and the numbers. Do NOT raise anything; resuming needs an owner note (§18). |
| S9 crash-rate halt | Rig defect suspected, not evidence | Stop that flow. Read the failing traces' error text. If the cause is listed here, fix per this table; otherwise escalate. |
| `retry` events, occasional | Provider transport blip | Nothing; it self-heals. Many per iteration → pause parallel flows, report. |
| Machine slow, other sessions crawling | Too many concurrent processes | Reduce flows/workers to the §4 limits. Check swap: `sysctl vm.swapusage`. |
| Eval interrupted mid-look | Power/kill/halt during a look | Safe: per-task checkpoint. Re-run the same wrapper command — a spent look with no result file continues as the same look. |
| VAL score identical across iterations at 1.0 | Task too easy (smoke saw this) | Expected on tiny splits; the val-100 early stop is contract behavior. |
| A run's spend near its cap in `status` | Projection error like SE-1's first halt | Report BEFORE it halts, with per-task pacing math. The owner decides; you do not. |
| Anything not in this table | Novel incident | STOP that flow (others may continue). Write what you saw. Escalate. |

## 7. Escalation rules — what the operator never decides alone

Never, regardless of how obvious it seems: amend or reinterpret the frozen contract;
raise any cap; spend an unplanned TEST look or re-look at a completed one; edit
frozen documents (contracts, landed research reports); change prompts, models, or
scorer; declare a verdict outside `compute_verdict.py`; continue past a novel
incident. All of these go to the frontier tier and/or the owner. Escalating early is
free; improvising is not.

## 8. Model-tier delegation (generalized; candidate doctrine)

The general rule, from SE-1's own result and this project's operating experience:
**match the model tier to the reversibility and novelty of the decision, not to the
technical difficulty of the task.** Executing well-specified work is cheap-tier work
no matter how technical it looks; making calls that are costly to unwind, or that no
written rule covers, is frontier work no matter how small it looks.

Three tiers, with current examples:

| Tier | Example | Use for | Because |
|---|---|---|---|
| Frontier | Fable-level | Creating the rules: experiment/contract design; compiling knowledge into artifacts others execute (skills, runbooks, briefs); novel-incident diagnosis; verdict interpretation; adversarial review; anything touching instrument integrity | Errors here corrupt everything downstream, silently. SE-1 evidence: frontier discovery produced reliable results across every seed (70–80); cheap discovery scattered (48–81). |
| Strong | Opus-level | Orchestrating frozen rules: running this runbook; handling listed incidents; drafting inside established formats; code changes inside an existing architecture; rubric-guided review | The default working tier. Judgment within written boundaries. |
| Cheap | Haiku-level | High-volume execution with verifiable output: rollouts, scoring, data preparation, formatting — anything a checker, gate, or schema validates | Volume work; correctness is enforced by machinery, not trust. |

How to delegate well:

1. **Delegate artifacts, not intentions.** The frontier tier writes the skill,
   runbook, or brief once; cheaper tiers execute it many times. (SE-1: skills made
   the cheap executor both better and 3× cheaper per solved task. The wholesaling
   protocol's compiled briefs are the same mechanism by hand.)
2. **Escalate by novelty, fail closed.** A cheaper tier that meets a situation its
   instructions do not cover must stop and hand up — never improvise. Improvisation
   is precisely the capability you did not pay for.
3. **Keep the gates mechanical.** Acceptance rules, budget caps, and look ledgers
   are enforced by code, so delegation never weakens governance — a cheap operator
   physically cannot overspend or double-look.
4. **Spend frontier tokens where they compound.** One-time compilation (designs,
   reviews, post-mortems that improve the runbook) — not per-run labor. A recurring
   escalation is a signal: encode it as a new runbook entry and the work moves
   down-tier permanently.
5. **Audit the delegation on a sample.** The frontier tier occasionally reads
   cheap-tier transcripts, the way the wiki maintainer reads traces — looking for
   quiet drift, not for errors the gates already catch.
6. **Respect the capability floor both ways.** Below a tier's ability to follow the
   procedure, delegation returns garbage (SE-1's executor lesson applies to
   operators too). Above the needed judgment, you are burning money for comfort.

Status of this section: candidate doctrine, captured in `PLAYBOOK_FEEDBACK.md` for
adjudication; not yet playbook rule.
