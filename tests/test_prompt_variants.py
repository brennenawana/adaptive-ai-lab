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
    _BASE_RULES,
    _POLICY_BLOCK,
    _RULES_CITE,
    _RULES_CITE_ELIMINATIVE,
    _RULES_HEAD,
    _RULES_TAIL,
    CAUSE_TO_ACTION,
    DEFAULT_PROMPT,
    PROMPTS,
)

CITATION_RECOVERY = ["cite_last", "cite_eliminative", "cite_last_eliminative"]

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


def test_deconfounder_lists_causes_without_teaching_actions():
    """Variant D isolates the confound found in the first dev sweep: B and C both
    taught the mapping AND enumerated the hypothesis space, and diagnosis tripled.
    D must contain every cause and none of the action vocabulary."""
    d = PROMPTS["causes_only"]
    for cause in CAUSE_TO_ACTION:
        assert cause in d, f"causes_only omits {cause}"
    taught = {a for actions in CAUSE_TO_ACTION.values() for a in actions}
    for action in taught:
        assert action not in d, f"causes_only leaks the action {action}"
    assert "->" not in d


@pytest.mark.parametrize("ref", ["cause_action_table", "cause_action_directed"])
def test_intervention_variants_carry_the_whole_table(ref):
    prompt = PROMPTS[ref]
    for cause, actions in CAUSE_TO_ACTION.items():
        assert cause in prompt, f"{ref} omits {cause}"
        for action in actions:
            assert action in prompt, f"{ref} omits {action} for {cause}"


def test_rule_fragments_reconstruct_the_original_block():
    """The split is for MOVING the citation rules, not editing them. If the three
    fragments stop concatenating back to the original, variant A is silently no
    longer the prompt E2 was baselined with and the control is void."""
    assert _BASE_RULES.endswith(_RULES_TAIL)
    assert f"{_RULES_HEAD}\n{_RULES_CITE}\n{_RULES_TAIL}" in _BASE_RULES


def test_every_variant_carries_all_rules_verbatim():
    """Rules may be reordered; they may never be reworded. A variant that also
    rephrased the citation rules would confound where-vs-what."""
    for ref, prompt in PROMPTS.items():
        for name, fragment in (("head", _RULES_HEAD), ("cite", _RULES_CITE),
                               ("tail", _RULES_TAIL)):
            assert fragment in prompt, f"{ref} altered or dropped the {name} rules"


def test_citation_recovery_variants_reuse_C_policy_text_exactly():
    """E/F/G must differ from C only in citation handling. If the policy block were
    retyped rather than shared, the 2x2 would be measuring a prompt rewrite."""
    assert _POLICY_BLOCK in PROMPTS["cause_action_directed"], (
        "the shared policy block drifted from variant C, which has already been run "
        "on test — E/F/G would no longer be comparable to it"
    )
    for ref in CITATION_RECOVERY:
        assert _POLICY_BLOCK in PROMPTS[ref], f"{ref} does not carry C's policy block"


@pytest.mark.parametrize("ref", ["cite_last", "cite_last_eliminative"])
def test_recency_variants_put_citation_rules_after_the_policy(ref):
    prompt = PROMPTS[ref]
    assert prompt.index(_RULES_CITE) > prompt.index(_POLICY_BLOCK), (
        f"{ref} is supposed to test RECENCY — the citation rules must come last"
    )


@pytest.mark.parametrize("ref", ["cause_action_directed", "cite_last"])
def test_recency_only_variants_do_not_change_what_is_asked(ref):
    assert _RULES_CITE_ELIMINATIVE not in PROMPTS[ref], (
        f"{ref} isolates WHERE the rules sit; adding the eliminative line would "
        "confound it with WHAT they ask for"
    )


@pytest.mark.parametrize("ref", ["cite_eliminative", "cite_last_eliminative"])
def test_content_variants_ask_for_eliminative_evidence(ref):
    assert _RULES_CITE_ELIMINATIVE in PROMPTS[ref]


def test_the_2x2_is_actually_a_2x2():
    """Four distinct prompts, one per cell. A duplicate would silently halve the
    experiment and still produce a plausible-looking table."""
    cells = ["cause_action_directed", "cite_last", "cite_eliminative",
             "cite_last_eliminative"]
    assert len({PROMPTS[c] for c in cells}) == 4


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
