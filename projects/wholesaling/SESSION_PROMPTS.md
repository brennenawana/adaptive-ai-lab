# Session Prompts — How to Start Work in Each Repo

> Copy-paste launch prompts and the rules governing which session does what.
> Two repos, two session kinds, one direction of flow: the **lab** session
> compiles work orders; the **wholesaling** session executes exactly one.

## Repo A — `~/code/adaptive-ai-lab` (the lab session)

**What it knows on startup:** the `/goal` command loads `GOAL.md`, the tail of
`PROCESS_LOG.md`, and the profile's derived outputs, then restates the goal,
criteria status, and the next gated action before doing anything. That is the
orientation mechanism — a fresh lab session needs no other briefing.

**Launch prompt (standard, any lab session):**

```
/goal wholesaling
```

**If `/goal` is unavailable in that session,** the equivalent explicit prompt:

```
Read ~/code/adaptive-ai-lab/projects/wholesaling/GOAL.md and the last three
entries of PROCESS_LOG.md in that directory. Restate the goal, which success
criteria are met/in-progress, and the single next gated action. Then proceed
with that action only, logging decisions to PROCESS_LOG.md (append-only) and
committing at checkpoints on branch project/wholesaling-intake.
```

**What lab sessions do:** author/revise work-order briefs, verify acceptance
gates after a package returns, run evaluation-design work, keep the ledgers
(look, prediction, feedback), harvest learnings into the playbook at
milestones. **Never** commit to the wholesaling repo.

## Repo B — `~/code/wholesaling` (the executing session)

**What it knows on startup:** its own `CLAUDE.md` (repo rules, branch flow,
environments) plus **one work-order brief**, which is self-contained by
construction. It needs no lab documents and must not read them — the brief
inlines everything, and lab paths appear only in a footer marked do-not-read.

**Launch prompt (one per authorized package):**

```
Execute the work order at
~/code/adaptive-ai-lab/projects/wholesaling/packages/<ID>/BRIEF.md

Read that file first and treat it as your complete task context. Follow its
standing rules exactly, including the echo check before any code change and
the declared stop point. Do not read any other document outside this repo.
```

Set the session model to the one named in the brief's header (Opus for P1).
One package per session, fresh context, per `HANDOFF_PROTOCOL.md` §3.

**What wholesaling sessions do:** implement the spec, open the PR to `dev`,
run the acceptance commands, write `RESULT.md`, stop. They do not merge past
their stated stop point, do not self-assess the acceptance gate, and do not
pick up the next package.

## Which session handles what (quick routing)

| Work | Session |
|---|---|
| "Change something in the product" | wholesaling — but only via an authorized brief |
| "Design/verify an eval, freeze a contract, read a verdict" | lab |
| "Something's broken in prod right now" | wholesaling, as ordinary operator work — **not** a lab package (incidents are yours, not the lab's) |
| "Write/revise a work order" | lab |
| "Feed a finding back into the playbook" | lab, at a milestone harvest |

## Order of operations for the current step

1. **Operator authorizes P1** — edit `packages/P1/BRIEF.md`: change
   `Status: DRAFT (not yet authorized — do not execute)` to
   `Status: AUTHORIZED v1 (<date>)`. Nothing else changes.
2. **Wholesaling session** runs P1 with the Repo-B prompt above → PR opened
   against `dev`, `RESULT.md` written, session ends.
3. **Lab session** verifies P1's acceptance, records the PR/SHA, and proceeds
   to M1 action 2 (classify the observed-failure corpus into the taxonomy) —
   which does not depend on P1 and can run in parallel if you prefer.
4. Merge of the P1 PR is yours, after the lab's verification.
