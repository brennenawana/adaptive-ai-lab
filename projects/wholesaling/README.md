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

**Start here:** [SESSION_PROMPTS.md](SESSION_PROMPTS.md) — the launch prompt
for each repo and what each session kind is allowed to do.

| File | Role |
|---|---|
| [SESSION_PROMPTS.md](SESSION_PROMPTS.md) | Launch prompts per repo; session routing; current order of operations |
| [HANDOFF_PROTOCOL.md](HANDOFF_PROTOCOL.md) | Single-brief context firewall, session lifecycle, model selection |
| [INTEGRATION_AND_FEEDBACK.md](INTEGRATION_AND_FEEDBACK.md) | Lab→product intervention packages; product→playbook promotion loop |
| [PLAYBOOK_FEEDBACK.md](PLAYBOOK_FEEDBACK.md) | Append-only ledger of candidate playbook learnings (F-1…) |
| [packages/](packages/) | Work orders: `TEMPLATE_BRIEF.md`, `P1/BRIEF.md` + `RESULT.md` |
| [GOAL.md](GOAL.md) | Durable goal prompt; loaded by the `/goal` command |
| [PROCESS_LOG.md](PROCESS_LOG.md) | Append-only session/decision/delegation log |
| [AI_SYSTEM_INVENTORY.md](AI_SYSTEM_INVENTORY.md) | Code-verified survey of every AI surface (profile field 20 evidence) |
| [PROJECT_PROFILE.md](PROJECT_PROFILE.md) | The 21-field intake, stakes tier, archetype routing |
| [PLAYBOOK_PATH.md](PLAYBOOK_PATH.md) | Decision context, constraints, kill criteria, first actions, gated milestones |

Working branch: `project/wholesaling-intake`.
