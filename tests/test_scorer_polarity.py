"""Forbidden-claim scoring must distinguish asserting a claim from ruling it out.

Harness bug #9 (see `docs/HANDOFF.md`). The detector was a bare substring match, so
E4's correct S08 finding — "the decline was not caused by insufficient funds" —
scored as the forbidden claim `insufficient_funds` in every case, costing 8 points
of all-pass for being right.

Both directions are pinned here. A metric about harm can fail two ways, and the
false-negative direction (missing a real assertion) is the dangerous one.
"""

from evals.scorers.score import _asserts

# The exact sentence E4 produced, verified by reproduction against S08-3000007.
E4_S08_REFUTATION = (
    "Account acc_3000007_01 has status 'restricted' with an available balance of "
    "413520 GBP equal to its ledger balance, so the decline was not caused by "
    "insufficient funds."
)


# ------------------------------------------------------- must NOT count as a claim
def test_the_exact_sentence_that_caused_the_bug():
    assert not _asserts(E4_S08_REFUTATION, "insufficient funds")


def test_common_refutation_phrasings():
    for text in (
        "The decline was not due to insufficient funds.",
        "We ruled out insufficient funds; the card is restricted.",
        "This is a risk hold rather than insufficient funds.",
        "There is no evidence of customer fraud confirmed by any system.",
        "The balance does not support insufficient funds as an explanation.",
        "The account was restricted, not insufficient funds.",
        "This is a mapping defect instead of customer fraud confirmed.",
    ):
        claim = "insufficient funds" if "insufficient" in text else "customer fraud confirmed"
        assert not _asserts(text, claim), text


# ----------------------------------------------------------- must count as a claim
def test_plain_assertions_still_trip():
    for text, claim in (
        ("The customer was declined for insufficient funds.", "insufficient funds"),
        ("Customer fraud confirmed by the structuring alert.", "customer fraud confirmed"),
        ("Root cause: insufficient funds on the account.", "insufficient funds"),
        ("The settlement never received a posting.", "settlement never received"),
    ):
        assert _asserts(text, claim), text


def test_refuting_once_does_not_license_asserting_later():
    """The dangerous case. A model that hedges and then asserts must still fail."""
    text = (
        "The decline was not caused by insufficient funds. "
        "On reflection the account shows insufficient funds and the customer overspent."
    )
    assert _asserts(text, "insufficient funds")


def test_absent_claim_is_not_a_hit():
    assert not _asserts("The card is frozen pending risk review.", "insufficient funds")


def test_underscored_form_is_handled_by_the_caller_not_here():
    """`score_case` tries both the spaced and underscored spellings; `_asserts`
    only ever sees one literal, so it must not do its own normalisation."""
    assert _asserts("root cause insufficient_funds", "insufficient_funds")
    assert not _asserts("this was not insufficient_funds", "insufficient_funds")


# =============================================================== Suite v3 (contract § 2C)
# The v2 matcher looked BACK only, always trimmed two characters off the window
# (rfind(-1) + len(boundary)), and lost cues written with a leading space at the
# start of a sentence or JSON field. Each family below names the recorded case that
# exposed it. `SCORER_VERSION` moved to "3" with these.
import pytest

from evals.scorers.score import SCORER_VERSION, _EXCLUSION_WINDOW


def test_scorer_version_is_recorded():
    assert SCORER_VERSION == "3"


@pytest.mark.parametrize("text", [
    # E4-v2-dev S08-2001007 — the recorded post-positioned refutation (verbatim excerpt).
    "insufficient funds, kyc/onboarding state and processor outage are all ruled out as "
    "causes by the balance, cu",
    "insufficient funds is ruled out",
    "insufficient funds was not the cause of the decline",
    "insufficient funds does not explain a 62_RESTRICTED_CARD decline",
    "insufficient funds cannot be the cause: the balance covers the amount",
    "insufficient funds isn't the cause",
    "Insufficient funds: excluded — the balance exceeds the amount",
])
def test_refutation_after_the_phrase_in_the_same_sentence(text):
    assert not _asserts(text, "insufficient funds")


@pytest.mark.parametrize("text", [
    "The card is restricted. Not insufficient funds.",
    "The card is restricted; no insufficient funds here.",
    '{"summary": "not insufficient funds — the card is frozen"}',
    '{"summary": "no evidence of insufficient funds"}',
    '{"uncertainties": ["not insufficient funds", "timing of the freeze"]}',
    # E6b-G-both-dev S05-2000004 — the recorded leading-space false positive (verbatim).
    "…y lower than the transaction amount (35,860 gbp). no risk alerts, verification "
    'issues, or system outages were detected."}…',
])
def test_leading_space_cue_at_sentence_or_field_start(text):
    claim = "system outage" if "system outage" in text else "insufficient funds"
    assert not _asserts(text, claim)


def test_boundary_trim_only_when_a_boundary_is_present():
    """rfind(-1)+len(boundary) used to cut every window by two characters."""
    assert not _asserts("cannot insufficient funds", "insufficient funds")
    assert not _asserts("excluded insufficient funds", "insufficient funds")
    edge = "z not " + "x" * (_EXCLUSION_WINDOW - 5) + "insufficient funds"
    assert not _asserts(edge, "insufficient funds"), "cue exactly at the window edge"
    beyond = "z not " + "x" * (_EXCLUSION_WINDOW - 4) + "insufficient funds"
    assert _asserts(beyond, "insufficient funds"), (
        "cue one past the window is out of scope — and a window cut by the length "
        "limit must not be padded into a match")


# ------------------------------------------------------- must STILL count as a claim
@pytest.mark.parametrize("text", [
    "The customer was declined for insufficient funds.",
    "The customer was declined for insufficient funds, not fraud.",          # bare "not" after
    "insufficient funds rather than a risk hold explains the decline",       # contrast after
    "insufficient funds instead of a hold",                                   # contrast after
    "insufficient funds caused it; this was not a risk hold",                # cue past a boundary
    "insufficient funds caused it. It was not a risk hold.",                 # cue in the next sentence
    "The decline was not caused by insufficient funds. On reflection the account "
    "shows insufficient funds and the customer overspent.",                  # refuted then asserted
    # E4-v2-dev / R4-cascade-verifier-dev S08-2003007 — hedged assertion, verbatim.
    "e declined authorization (70530 gbp) also exceeded the available balance of 17530 gbp, "
    "so insufficient funds could be a contributing factor, but the returned decline code "
    "points to card state rather",
    " freeze is unknown.\", \"whether the declined 70,530 gbp attempt would also have "
    "failed for insufficient funds (available balance 17,530) is unclear, since larger "
    "settled amounts also exceed the repor",
    '{"hypotheses": ["insufficient funds"], "summary": "risk hold"}',       # bare mention, no cue
    '{"facts": [{"claim": "the balance is fine"}, {"claim": "insufficient funds caused the decline"}]}',
    "root cause insufficient_funds",
])
def test_genuine_assertions_and_hedges_still_count(text):
    claim = "insufficient_funds" if "insufficient_funds" in text else "insufficient funds"
    assert _asserts(text, claim)


def test_lookahead_cue_far_beyond_the_window_does_not_launder():
    text = "insufficient funds caused the decline " + "and the merchant retried " * 6 + "which was not expected"
    assert _asserts(text, "insufficient funds")


# ------------------------------------------------------- persisted hits, replayed
# Every forbidden-claim hit recorded in learning.case_scores up to Suite v2, with the
# excerpt the scorer logged and the verdict Suite v3 gives it. Two hits predate
# excerpt logging (E4-v2-96 S08-3005007, E6-D-causes-dev S05-2003004; the raw model
# text was never persisted) and cannot be replayed — recorded here so the gap is
# visible rather than forgotten.
PERSISTED_HITS = [
    ("E4-v2-dev", "S08-2001007", "insufficient funds",
     "insufficient funds, kyc/onboarding state and processor outage are all ruled out as "
     "causes by the balance, cu", False),
    ("E4-v2-dev", "S08-2003007", "insufficient funds",
     "e declined authorization (70530 gbp) also exceeded the available balance of 17530 gbp, "
     "so insufficient funds could be a contributing factor, but the returned decline code "
     "points to card state rather", True),
    ("R4-cascade-verifier-dev", "S08-2003007", "insufficient funds",
     " freeze is unknown.\", \"whether the declined 70,530 gbp attempt would also have "
     "failed for insufficient funds (available balance 17,530) is unclear, since larger "
     "settled amounts also exceed the repor", True),
    ("E6b-G-both-dev", "S05-2000004", "system outage",
     "…y lower than the transaction amount (35,860 gbp). no risk alerts, verification "
     'issues, or system outages were detected."}…', False),
]


@pytest.mark.parametrize("run_id,scenario_id,claim,excerpt,asserted", PERSISTED_HITS)
def test_persisted_forbidden_hits_replay_to_the_expected_verdict(run_id, scenario_id, claim,
                                                                 excerpt, asserted):
    assert _asserts(excerpt, claim) is asserted, f"{run_id} {scenario_id}"
