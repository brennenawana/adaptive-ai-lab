# Goal — Wholesaling Playbook Instantiation

> The durable goal prompt for this workstream. `/goal` loads this file to
> establish a goal session. Revise deliberately (it is the goal's record of
> record); session-by-session state lives in `PROCESS_LOG.md`, not here.

## The goal

Instantiate the Adaptive AI Systems Playbook (`../../playbook/`, v0.1.1) for the
wholesaling system (`~/code/wholesaling`) so that every AI surface whose output a
business decision rides on is governed by the playbook's discipline: a named
decision, a trusted evaluation, pre-declared consequences, and evidence that can
be audited — replacing the current state where AI outputs (outreach text,
property condition, extracted income, interpreted replies, voice scripts) act on
the world with no trusted measurement behind them.

## Why (both directions)

- **For wholesaling:** the pipeline's expensive failures are silent-failure
  shaped — confident wrong outreach, mispriced deals, wrongly-cleared HOLD gates.
  The playbook's eval-first, consequence-bearing discipline is the fix class.
- **For the lab:** the playbook's 1.0 gate requires materially different project
  instantiations through frozen executed contracts. Wholesaling — a live,
  multi-surface, compliance-gated production system — is materially different
  from FIS (clean-room synthetic) and millwork (greenfield document workflow).

## Success criteria (gated, not scheduled)

1. **Intake complete** — filled `PROJECT_PROFILE.md`, stakes tier assigned,
   archetype routed on recorded facts, constraints + kill criteria written.
2. **First sprint closed at the playbook's mandated endpoint** — a frozen
   `EXPERIMENT_CONTRACT` for the first real experiment (Tier 2), on the AI
   surface the intake ranks most consequential.
3. **A trusted eval exists for at least one production AI surface** — versioned
   suite, measured ceilings, release contract; harvested from real failures.
4. **One full loop demonstrated** — eval → diagnosis → ladder-ordered
   intervention → measured verdict (including INCONCLUSIVE as a legal outcome)
   → decision executed with its pre-declared consequence.
5. Each later milestone carries its own go/no-go rule accepted by the decision
   owner (Brennen), never self-assessed by the executor.

## Hard constraints

- The wholesaling repo is read-only for this workstream; artifacts live in
  `projects/wholesaling/` on lab branches. Any change to wholesaling itself goes
  through that repo's own feature-branch → PR → dev flow as a separately scoped
  task.
- No outreach channel is armed, no send path touched, no prod data mutated by
  this workstream. Observation and evaluation only until a frozen contract says
  otherwise and the operator explicitly authorizes.
- The playbook's never-skippable floor applies to this workstream's own claims:
  no quality claim about a wholesaling AI surface without a trusted eval behind
  it.

## Roles

- **Decision owner:** Brennen (operator). Accepts milestone gates, authorizes
  anything that touches the live system.
- **Orchestrator:** the lead agent session — holds the full context, delegates
  to Haiku/Sonnet/Opus subagents by task complexity, keeps `PROCESS_LOG.md`
  append-only and current.

## Where state lives

- `PROCESS_LOG.md` — append-only session/decision log (read the tail first).
- `PROJECT_PROFILE.md` — intake instrument and derived routing.
- `AI_SYSTEM_INVENTORY.md` — code-verified incumbent evidence (profile field 20).
- `PLAYBOOK_PATH.md` — decision context, constraints, first actions, gated
  milestones.
