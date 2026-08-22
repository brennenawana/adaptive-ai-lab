---
description: Establish a goal session for a lab project instantiation (default: wholesaling)
argument-hint: [project-name]
---

Establish a goal session for the Adaptive AI Lab project instantiation named by
`$ARGUMENTS` (default when empty: `wholesaling`). A goal session means: before
doing any work, re-anchor on the durable goal, the current state, and the next
gated action — then work only inside that frame.

Steps:

1. **Load the goal.** Read `projects/<project>/GOAL.md` in the adaptive-ai-lab
   repo (`~/code/adaptive-ai-lab`). If it does not exist, stop and say so — a
   goal session cannot be established without a goal record.
2. **Load the state.** Read the tail (most recent entries) of
   `projects/<project>/PROCESS_LOG.md`, and the "Derived outputs" section of
   `projects/<project>/PROJECT_PROFILE.md` if present.
3. **Verify the working frame.** Confirm the repo is on the project's working
   branch (for wholesaling: `project/wholesaling-intake`, or its successor named
   in the process log). Confirm the hard constraints in GOAL.md still hold; if
   any recent entry contradicts them, surface the contradiction instead of
   proceeding.
4. **Restate the goal session.** Output, concisely: (a) the goal in one
   sentence, (b) which success criteria are met / in progress / not started,
   (c) the single next gated action and which playbook chapter governs it,
   (d) what is explicitly out of scope this session.
5. **Open the session in the log.** Append a dated "goal session" entry to
   `PROCESS_LOG.md` recording the restatement from step 4 (append-only — never
   edit prior entries).
6. **Proceed** with the next gated action only, delegating to subagents by
   complexity (Haiku: mechanical, Sonnet: bounded analysis/synthesis, Opus:
   judgment-heavy or code-verification work), and record delegation summaries
   and decisions in the process log as they land. Commit and push the lab repo
   at meaningful checkpoints.

The never-skippable floor applies to this session's own claims: state the
decision each piece of work drives; keep provenance for anything that might be
acted on; make no quality claim about an AI surface without naming the evidence
behind it.
