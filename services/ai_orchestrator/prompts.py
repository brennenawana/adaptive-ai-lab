"""Investigator system prompts, versioned.

E6's intervention lives here. The measured defect is not that the local model picks
bad remedies — it is that its remedy is *uncorrelated with its own diagnosis*:
action accuracy was 18.8% when its root cause was right and 17.5% when it was wrong.
It has no model of which remedy attaches to which defect, so the fix to try first is
simply telling it.

This is legitimate company knowledge, not the answer key. `CAUSE_TO_ACTION` is a
static policy table — the same one an operator would have on the wall — and contains
nothing case-specific. Nothing here reads `ground_truth`; doing so would put the
answer key in the model's context, which the clean-room boundary forbids.

**Measurement note, and it matters for reading E6.** Once the policy table is in the
prompt, `next_action_accuracy` stops measuring operational judgement and starts
measuring lookup compliance — a model that identifies the cause can read the answer
off the table. That is the intervention working as designed, not a leak, but it means
the aggregate action rate is no longer comparable to E2's. Judge E6 on:

  * **P(action acceptable | root cause correct)** — can it apply a policy at all?
    Baseline 18.8%. This is the number the experiment is about.
  * **root-cause accuracy** — must not regress. A longer prompt costs attention, and
    trading diagnosis for remedy would be a bad deal.
"""

from __future__ import annotations

# Root cause -> sanctioned operational responses.
#
# Mirrors `docs/task-ontology.md` §3, which is normative.
# `test_prompt_table_matches_the_rubric` fails if the two drift apart — a prompt
# that teaches a policy the scorer does not use would make E6 unreadable.
CAUSE_TO_ACTION: dict[str, list[str]] = {
    "duplicate_webhook_handled": ["no_action_required"],
    "missing_idempotency": ["open_reconciliation_review", "escalate_to_engineering"],
    "kyc_hold": ["request_kyc_documents", "no_action_required"],
    "provider_outage": ["contact_identity_vendor", "escalate_to_engineering"],
    "processor_decline": ["no_action_required"],
    "settlement_amount_mapping_error": ["open_reconciliation_review", "inspect_mapping_version"],
    "reversal_race": ["open_reconciliation_review", "escalate_to_engineering"],
    "risk_hold": ["escalate_to_risk_team", "release_risk_hold_review"],
    "stale_integration_mapping": ["inspect_mapping_version", "escalate_to_engineering"],
    "reconciliation_gap": ["open_reconciliation_review", "escalate_to_engineering"],
    "false_positive_alert": ["no_action_required", "release_risk_hold_review"],
    "compound_failure": ["request_kyc_documents", "escalate_to_engineering"],
}


def _render_table() -> str:
    width = max(len(c) for c in CAUSE_TO_ACTION)
    return "\n".join(
        f"  {cause:<{width}}  ->  {', '.join(actions)}"
        for cause, actions in CAUSE_TO_ACTION.items()
    )


_BASE_RULES = """Given a case, determine the most likely root cause from the evidence available.

Rules:
- Separate facts from hypotheses. A fact is something a tool result directly shows;
  anything inferred, suspected or probable is a hypothesis, not a fact.
- Every fact must cite its source as tool://<tool_name>/<entity_id>, where
  <tool_name> is the tool the evidence came from and <entity_id> is the specific
  record id. For example: tool://get_ledger_entries/le_001539
- Put the specific record ids you relied on in each fact's entity_ids list.
- Do not assert customer fraud, or any conclusion the evidence does not directly
  support. An open alert is a pattern match, not a finding.
- The surface symptom is often not the root cause. A decline may be caused by an
  upstream risk hold; an inactive card may be waiting on identity verification.
- "Nothing is wrong" is a legitimate conclusion when the authoritative systems agree.
- Set confidence honestly. Low confidence with correct reasoning is better than
  high confidence you cannot support."""

_HEADER = "You are an operations investigator for Northstar Bank."
_FOOTER = "Respond only via the provided schema."


# ---------------------------------------------------------------- variants
# A: the control. Byte-identical to the prompt E2 was baselined with, so E6 has a
#    same-run comparison rather than one against a number from another day.
_A_BASELINE = f"""{_HEADER}

{_BASE_RULES}

{_FOOTER}"""


# B: the table, presented as reference material and nothing else. Tests the weakest
#    version of the hypothesis — that the model simply did not know the mapping.
_B_TABLE = f"""{_HEADER}

{_BASE_RULES}

Operational response policy. Once you have identified the root cause, the
sanctioned responses for it are:

{_render_table()}

{_FOOTER}"""


# C: the table plus an explicit ordering of the work. Tests whether knowing the
#    mapping is enough, or whether the model also has to be told to *use its own
#    conclusion* as the lookup key. Given that its action is currently uncorrelated
#    with its diagnosis, the two failures are distinguishable and worth separating.
_C_TABLE_DIRECTED = f"""{_HEADER}

{_BASE_RULES}

Operational response policy. Each root cause has a fixed set of sanctioned
responses:

{_render_table()}

Choose the recommended_next_action by looking up the root cause you concluded, in
the table above, and selecting from that row. Do not choose an action because it
matches words in the case summary. If your chosen action does not appear on the row
for your chosen root cause, one of the two is wrong — revisit them before answering.

{_FOOTER}"""


# D: the deconfounder, added after the first dev sweep.
#
# B and C tripled ROOT-CAUSE accuracy (18.8% -> 56.3% / 62.5%), which the
# cause→action intervention has no business doing. They changed two things at once:
# they taught the mapping, and they enumerated the twelve valid root causes in the
# prompt for the first time. The label set was previously only in the response
# grammar, which constrains what the model may *emit* but never puts the hypothesis
# space in front of its reasoning.
#
# D lists exactly the same causes in the same order and format, with the action
# column removed and nothing else changed. If D recovers most of the diagnostic
# gain, the headline is "enumerate the hypothesis space" — a far cheaper and more
# general finding than "teach the remedy policy", and it would mean B/C's diagnostic
# lift should not be credited to E6's intervention at all.
_D_CAUSES_ONLY = f"""{_HEADER}

{_BASE_RULES}

The possible root causes are:

{chr(10).join(f"  {cause}" for cause in CAUSE_TO_ACTION)}

{_FOOTER}"""


PROMPTS: dict[str, str] = {
    "baseline": _A_BASELINE,
    "cause_action_table": _B_TABLE,
    "cause_action_directed": _C_TABLE_DIRECTED,
    "causes_only": _D_CAUSES_ONLY,
}

DEFAULT_PROMPT = "baseline"
