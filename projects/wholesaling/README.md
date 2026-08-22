# Wholesaling — Playbook Instantiation

The Adaptive AI Systems Playbook (`../../playbook/`) instantiated for the
wholesaling system — a live, compliance-gated real-estate wholesaling pipeline
(`~/code/wholesaling`, Python/FastAPI + React, Supabase, Vercel) with multiple
production AI surfaces (outreach generation, reply interpretation, vision-based
condition analysis, prose→JSON extraction, AI voice) and, at intake, no trusted
evaluation behind any of them.

This is the lab's third instantiation (after `fis/` and `millwork-estimating/`)
and the first against a **live production system** the lab does not get to
redesign — the instantiation works archetype-C style: evidence first, diagnosis
before intervention, the product repo treated as read-only.

| File | Role |
|---|---|
| [GOAL.md](GOAL.md) | Durable goal prompt; loaded by the `/goal` command |
| [PROCESS_LOG.md](PROCESS_LOG.md) | Append-only session/decision/delegation log |
| [AI_SYSTEM_INVENTORY.md](AI_SYSTEM_INVENTORY.md) | Code-verified survey of every AI surface (profile field 20 evidence) |
| [PROJECT_PROFILE.md](PROJECT_PROFILE.md) | The 21-field intake, stakes tier, archetype routing |
| [PLAYBOOK_PATH.md](PLAYBOOK_PATH.md) | Decision context, constraints, kill criteria, first actions, gated milestones |

Working branch: `project/wholesaling-intake`.
