# Intake interview

> DRAFT — pending field trial; see README.md in this directory.

**What this produces:** a filled `templates/PROJECT_PROFILE.md` in the
engagement home (`profile/PROJECT_PROFILE.md`), the first ledger rows,
and an initial routing recommendation. The profile template is the
artifact and stays canonical — this interview is how it gets filled:
conversationally, one question at a time, answers written **as they are
given**, each marked (owner) or (default). Skip any question whose
purpose an earlier answer already satisfied. Reflect each answer back in
one sentence so errors die young.

Time promise: 20–30 minutes for a first pass; the profile can be
completed incrementally — mark unfilled sections `TBD` with a ledger row
noting what is missing and why it can wait.

## Stage 0 — Frame it (do not skip)

Say in plain words: what this engagement is for, that everything recorded
lands in this engagement home and nowhere else (client isolation), that
an append-only ledger will record every significant decision, and what
the next hour looks like. Then record the engagement's name and the
playbook version in `ENGAGEMENT_STATE.json`.

## Stage 1 — The decision (ch. 01; profile §1, §3)

1. **Purpose: the driving decision.** "What decision is this engagement
   supposed to answer — what will you (or the client) do differently
   depending on the result?" An engagement without a driving decision is
   not started; help sharpen one first.
2. **Purpose: the business outcome** behind that decision, in the
   client's units (profile §1).
3. **Purpose: criticality.** "What does a wrong answer cost — money,
   trust, safety?" (profile §3). This sets the rigor tier everything
   else calibrates to.

## Stage 2 — The task and its bar (profile §2, §4, §5)

4. **Purpose: task population.** What the system actually does, how
   often, with what variety (profile §2). Ask for one typical item
   narrated start to finish.
5. **Purpose: the quality target** — in whose judgment, measured how
   today (profile §4). "I read it and use my judgment" is a common,
   honest answer; record it verbatim.
6. **Purpose: latency/throughput constraints** that bind (profile §5).

## Stage 3 — The world (profile §6, §7, §8)

7. **Purpose: blast radius.** Every repository and every outside service
   a task touches, and which of them automation touches directly. (This
   is what later observation and capsule work must cover.)
8. **Purpose: data and knowledge availability** (profile §7) and
   **privacy/residency constraints** (profile §6).
9. **Purpose: tool/action permissions** — what the system may do on its
   own vs with a human (profile §8).

## Stage 4 — Resources (profile §9–§16)

10. **Purpose: model candidates and where they run** (profile §9), and
    the **compute reality**: owned, rentable, managed APIs (profile
    §10–§12).
11. **Purpose: money and time.** Capex, recurring budget, staffing
    (profile §13, §14, §16) — in the owner's own cost unit; budgets in
    later contracts are sized from this answer, measured not guessed.
12. **Purpose: growth expectations** (profile §15) — only if a scaling
    decision is plausibly the driving decision.

## Stage 5 — Existing evidence (routes the first move)

13. **Purpose: what measurement already exists.** Evals, dashboards,
    incident history, prior experiments — or nothing. Do not audit yet;
    inventory.
14. **Purpose: the known pain, their words.** Recorded verbatim; the
    owner's stated goal outranks any ranking later.

## Close

Summarize the whole profile back in under ten sentences; correct;
write the profile file and the ledger rows if not already streamed; then
produce the **first routing recommendation** per `routing.md` (for a
fresh system with no measurement, expect it to be the chapter 03
eval-foundation gate — say why in one sentence, give the cost shape, ask
approve-or-steer).
