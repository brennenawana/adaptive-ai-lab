"""Forbidden-claim scoring must distinguish asserting a claim from ruling it out.

Harness bug #8. The detector was a bare substring match, so E4's correct S08
finding — "the decline was not caused by insufficient funds" — scored as the
forbidden claim `insufficient_funds` in every case, costing 8 points of all-pass
for being right.

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
