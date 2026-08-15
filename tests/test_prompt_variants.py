"""E6 prompt variants.

The load-bearing test here is `test_prompt_table_matches_the_rubric`. E6 teaches the
model a cause→action policy; the scorer grades against each scenario's
`acceptable_next_actions`. If the two ever drift apart the experiment becomes
unreadable — a variant would be penalised for correctly applying what it was told,
and the natural (wrong) reading would be "the intervention did not work".
"""

import pytest

from scenarios.generator.catalog import BUILDERS
from scenarios.generator.run import build
from services.ai_orchestrator.prompts import (
    CAUSE_TO_ACTION,
    DEFAULT_PROMPT,
    PROMPTS,
)

CODES = sorted(BUILDERS)


def test_prompt_table_matches_the_rubric():
    """Every generated scenario's sanctioned actions must equal the table's row.

    Checked against the generator rather than the docs, because the generator is
    what the scorer actually grades against.
    """
    seen: dict[str, set[str]] = {}
    for code in CODES:
        _, m = build(code, 3_000_500)
        seen.setdefault(m["root_cause"], set()).update(m["acceptable_next_actions"])

    for cause, actions in seen.items():
        assert cause in CAUSE_TO_ACTION, (
            f"root cause {cause!r} is generated but absent from the E6 prompt table"
        )
        assert set(CAUSE_TO_ACTION[cause]) == actions, (
            f"{cause}: prompt teaches {sorted(CAUSE_TO_ACTION[cause])}, "
            f"scorer accepts {sorted(actions)}"
        )


def test_table_has_no_causes_the_corpus_never_generates():
    """A row for a cause that never appears is dead weight in the prompt — and
    `unknown` in particular must never be taught as diagnosable."""
    generated = {build(code, 3_000_500)[1]["root_cause"] for code in CODES}
    assert set(CAUSE_TO_ACTION) == generated
    assert "unknown" not in CAUSE_TO_ACTION


def test_replay_webhook_is_not_taught():
    """It is sanctioned for no root cause and is kept deliberately as a distractor.
    Teaching it would destroy the name-anchoring signal it exists to measure."""
    taught = {a for actions in CAUSE_TO_ACTION.values() for a in actions}
    assert "replay_webhook" not in taught


# ------------------------------------------------------------------ variants
def test_baseline_is_the_control():
    """Variant A must be byte-identical to the prompt E2 was baselined with, or E6
    has no same-run control and can only be compared against another day's number."""
    baseline = PROMPTS["baseline"]
    assert "Operational response policy" not in baseline
    assert "->" not in baseline
    assert DEFAULT_PROMPT == "baseline"


@pytest.mark.parametrize("ref", ["cause_action_table", "cause_action_directed"])
def test_intervention_variants_carry_the_whole_table(ref):
    prompt = PROMPTS[ref]
    for cause, actions in CAUSE_TO_ACTION.items():
        assert cause in prompt, f"{ref} omits {cause}"
        for action in actions:
            assert action in prompt, f"{ref} omits {action} for {cause}"


def test_variants_differ_only_by_the_intervention():
    """The control's rules must survive verbatim in every variant. A variant that
    also reworded the citation rules would confound the measurement."""
    baseline = PROMPTS["baseline"]
    rules = baseline[baseline.index("Rules:"):baseline.index("Respond only")].strip()
    for ref, prompt in PROMPTS.items():
        assert rules in prompt, f"{ref} altered the shared rules block"


def test_directed_variant_tells_the_model_to_use_its_own_conclusion():
    """The distinction B vs C is the experiment: does the model need the mapping, or
    does it also need to be told to key the lookup on its own diagnosis?"""
    assert "looking up the root cause you concluded" in PROMPTS["cause_action_directed"]
    assert "looking up the root cause you concluded" not in PROMPTS["cause_action_table"]


def test_no_prompt_leaks_ground_truth_vocabulary():
    """The table is policy, not answers. Nothing case-specific may appear."""
    for ref, prompt in PROMPTS.items():
        low = prompt.lower()
        for leak in ("scenario_id", "ground_truth", "required_evidence",
                     "acceptable_next_actions", "s01", "s07", "manifest"):
            assert leak not in low, f"{ref} leaks {leak!r}"
