# Handoff Protocol — Feeding Work to the Wholesaling Agent

> How intervention packages become executable sessions in the wholesaling
> repo. Operationalizes [`INTEGRATION_AND_FEEDBACK.md`](INTEGRATION_AND_FEEDBACK.md)
> Direction 1. Written 2026-08-22.

## 0. The one rule everything else serves

**The wholesaling agent reads exactly ONE file per session — its brief — and
that file is complete.** The lab session (which holds the full context)
COMPILES context into the brief; the agent never follows links to acquire
context. If the brief references another document, the needed content is
inlined as an excerpt. Link fan-out is a defect in the brief, not homework
for the agent.

The firewall has one deliberate exception: the wholesaling **codebase
itself**. The agent reads as much of the repo's code as the task needs —
that's its job. The firewall applies to lab/methodology/context documents,
not to the code being changed.

## 1. Artifacts and layout

```
projects/wholesaling/packages/
  TEMPLATE_BRIEF.md          ← the authoring template
  P1/
    BRIEF.md                 ← the single file the agent reads (frozen at authorization)
    RESULT.md                ← the agent's completion report (appended at session end)
  P2/ …
```

- **BRIEF.md** is written by a lab session from the template, reviewed by the
  operator, and **frozen at authorization** (a `Status: AUTHORIZED v1` line).
  Changing an authorized brief = version bump + a **fresh session** — never
  patch a running session's understanding mid-flight.
- **RESULT.md** is written by the wholesaling agent at session end (fixed
  format, template §7). The lab session commits it and records the PR SHA
  against the package.

## 2. Session lifecycle

**Launch.** The operator starts a session in `~/code/wholesaling` with a
one-line prompt:

> Execute the work order at
> `~/code/adaptive-ai-lab/projects/wholesaling/packages/P1/BRIEF.md`. Read
> that file first and treat it as the complete task context.

**Echo check (mandatory, in the brief's standing rules).** Before touching
code, the agent restates in 3–6 lines: the objective, the non-goals, the
acceptance criteria, and where it will stop (PR-open vs merge-to-dev). A wrong
echo means the brief is defective — fix the brief, new session; don't correct
the agent conversationally and hope.

**Execute.** Normal wholesaling flow per that repo's own rules (feature branch
off `origin/dev`, PR to `dev`, never push `main`/`dev`, secret-scan before
push). The brief inlines the 5–10 repo rules that matter for the specific
task so the agent isn't reconstructing policy from CLAUDE.md alone.

**Stop point.** Each brief declares it explicitly. Default for lab packages:
**stop at PR-open** — the acceptance gate is lab-side measurement, so merging
waits for the lab's verification + operator's go-ahead. A brief may authorize
merge-to-dev-after-green-CI when the acceptance check is fully contained in CI.

**Report.** Agent writes RESULT.md (format in the template) and ends. It does
not update lab documents, does not self-assess the acceptance gate, and does
not start the next package.

## 3. When to start a NEW session (vs continue)

Start fresh when ANY of these holds:

1. **New package.** One session per package, always. No cross-package reuse —
   residual context from P1 is contamination in P2.
2. **Brief amended.** Version bump → fresh session (§1).
3. **Context degraded.** The session has compacted, or >~60% of context is
   spent before implementation is done → have the agent write an interim
   RESULT with precise state, then relaunch with the brief + that interim
   result appended to it (the relaunch still reads one file).
4. **Scope discovery.** The agent hits something the brief didn't anticipate
   that changes the spec → it stops and reports (escalation rule in every
   brief); the lab revises the brief; fresh session. The agent never
   improvises spec changes.

Continue the same session for: review feedback on its own PR, CI fixes,
mechanical follow-ups inside the same spec.

## 4. Model and effort selection

| Situation | Model | Rationale |
|---|---|---|
| Default for any package touching pipeline logic, schema, or judgment calls | **Opus** (or the strongest available tier) | Wholesaling's standing rule is Opus for substantive work; packages are pre-specced but implementation still needs judgment |
| Tightly-specced mechanical package (rename sweep, config plumbing, doc-only) | Sonnet | The brief carries the judgment; execution is bounded |
| Anything in the wholesaling repo | never Haiku as the session driver | Repo is production; Haiku is for subagent grunt work only |
| Subagents inside a wholesaling session | per wholesaling's own standing rule (Opus) unless the brief says otherwise | That repo's memory rule governs there |
| Effort | high (default) | Match the repo default |

The brief's header **names the model** for its package so the operator never
decides ad hoc at launch time.

## 5. Brief authoring rules (the context-engineering contract)

Written for the lab session that compiles a brief; enforced by template
structure:

1. **Self-contained or defective.** Everything needed is in the file:
   objective, why (2–4 sentences, compiled — not "see PLAYBOOK_PATH"), spec,
   inlined excerpts of any external material, acceptance criteria,
   verification commands, constraints, stop point, escalation rule.
2. **≤ ~250 lines.** If a brief can't fit, the package is too big — split it.
3. **Code pointers, not code dumps.** `path:line` references into the
   wholesaling repo are encouraged (the agent will read them); pasted code
   only when pointing is ambiguous.
4. **Provenance footer, marked non-load.** Lab document references appear
   once, at the bottom, under "Provenance (do not read — for audit only)".
5. **No nested instructions.** The brief never says "follow the process in
   X"; the relevant process steps are copied in.
6. **Acceptance criteria are checkable by the agent** (tests pass, command
   output, schema present) even when the *gate* is lab-side; the agent
   verifies what it can and reports raw output.
7. **Freeze discipline.** `Status: DRAFT` → operator review → `AUTHORIZED
   v1` + date. Post-authorization edits bump the version.

## 6. Division of duties (recap)

| Actor | Does | Never does |
|---|---|---|
| Lab session | Compiles briefs, verifies acceptance gates, records results/SHAs, revises briefs | Commits to wholesaling; executes packages |
| Operator | Authorizes briefs, launches sessions, owns merges/releases | — |
| Wholesaling agent | Executes one brief per session, opens the PR, writes RESULT.md | Reads lab docs beyond its brief; changes spec; self-assesses the gate; merges beyond its stated stop point |
