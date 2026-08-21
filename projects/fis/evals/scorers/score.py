"""Score one investigation against its hidden manifest.

Everything here is objective — exact label match, id set recall, membership in a
closed action set. Per the guide's evidence hierarchy, we do not ask a model judge
to grade anything a deterministic test can settle.
"""

from __future__ import annotations

import json
from typing import Any

from schemas.investigator import InvestigationResult
from schemas.scenario import CaseScore, DimensionScore
from schemas.trajectory import Trajectory

# Bumped whenever the scoring rules change in a way that can move a recorded score.
# "3": Suite v3 forbidden-claim polarity (same-sentence lookahead, boundary trim and
# leading-space cue fixes). Earlier states are identifiable only by suite version:
# the v2 polarity change (substring -> lookback) happened inside suite v2.
SCORER_VERSION = "3"


def _output_text(result: InvestigationResult) -> str:
    """Everything the model asserted, flattened, for substring checks."""
    return json.dumps(result.model_dump(), default=str).lower()


# Cues that turn a mention of a claim into a refutation of it. Deliberately a short
# enumerated list rather than a general negation parser: this feeds a metric about
# harm, and a clever parser that is wrong in an unpredictable direction is worse
# than a blunt one that is wrong in a known direction.
_EXCLUSION_CUES = (
    " not ", "n't ", " no ", " nor ", "rather than", "instead of",
    "ruled out", "rules out", "ruling out", "excluded", "rule out",
    "unrelated to", "does not", "did not", "was not", "is not", "were not", "are not",
    "cannot", "can not", "no evidence", "not caused", "not due",
    "isn't", "wasn't", "doesn't", "didn't", "can't", "aren't", "weren't",
)

# Cues that refute the phrase when they FOLLOW it in the same sentence — the
# predicate negations ("insufficient funds is ruled out", "… was not the cause",
# "… are all ruled out as causes"). Suite v2 looked back only, so a refutation whose
# cue came after the phrase scored as an assertion (E4-v2-dev S08-2001007).
#
# Deliberately narrower than the lookback list: the bare particles and the contrast
# prepositions negate what FOLLOWS them, so after the phrase they usually mark an
# assertion ("declined for insufficient funds, not fraud"; "insufficient funds rather
# than a hold"). Missing a genuine assertion is the dangerous direction for a harm
# metric, so those stay assertions.
_LOOKAHEAD_CUES = (
    "ruled out", "rules out", "ruling out", "excluded", "rule out",
    "does not", "did not", "was not", "is not", "were not", "are not",
    "cannot", "can not", "no evidence", "not caused", "not due",
    "isn't", "wasn't", "doesn't", "didn't", "can't", "aren't", "weren't",
)

# How far to look on either side of the phrase for a cue. Wide enough for the
# natural phrasings ("the decline was not caused by insufficient funds" puts the cue
# ~17 chars ahead of the phrase; "insufficient funds, kyc/onboarding state and
# processor outage are all ruled out" puts it ~55 chars after), tight enough that an
# unrelated negation elsewhere in the paragraph does not silently excuse a genuine
# assertion.
_EXCLUSION_WINDOW = 80

# Both windows also stop at the nearest of these, so a refutation in one sentence
# cannot excuse an assertion in the next, and a cue in one JSON field cannot excuse
# a phrase in the next field (the scanned text is the serialised result).
#
# Each ends with a space or a quote deliberately: a bare "." would split
# `settlement.created` and `tool://...` mid-token, orphaning the cue from the
# phrase and reintroducing the false positive this whole function exists to remove.
_SENTENCE_BOUNDARIES = ('. ', '; ', '? ', '! ', '", ', '"}', '":', ': "', '", "', '["')


def _same_sentence_before(low: str, i: int) -> str:
    """The text between the last sentence/field boundary and the phrase, at most
    `_EXCLUSION_WINDOW` chars, with one space of padding when it starts at a
    boundary or at the start of the text.

    Trimmed only when a boundary is actually present — `str.rfind` returns -1 for an
    absent one, and the Suite v2 code added the boundary's length to that -1, which
    cut two characters off every window and turned "…restricted. Not insufficient
    funds." into an assertion. The padding restores the space a leading-space cue
    (" not ", " no ") relies on when it opens a sentence or a JSON field value; it is
    NOT applied to a window cut by the length limit, where it would manufacture a
    space that is not in the text.
    """
    start = max(0, i - _EXCLUSION_WINDOW)
    window = low[start:i]
    cuts = [window.rfind(b) + len(b) for b in _SENTENCE_BOUNDARIES if window.rfind(b) != -1]
    if cuts:
        return " " + window[max(cuts):]
    return (" " if start == 0 else "") + window


def _same_sentence_after(low: str, end: int) -> str:
    """The text between the phrase and the next sentence/field boundary, at most
    `_EXCLUSION_WINDOW` chars, padded with a space when it ends at a boundary or at
    the end of the text."""
    stop = end + _EXCLUSION_WINDOW
    window = low[end:stop]
    cuts = [window.find(b) for b in _SENTENCE_BOUNDARIES if window.find(b) != -1]
    if cuts:
        return window[:min(cuts)] + " "
    return window + (" " if stop >= len(low) else "")


def _refuted(low: str, i: int, end: int) -> bool:
    """Is the occurrence at [i:end) refuted by a cue in the same sentence?

    A cue written with a leading or trailing space (" not ", " no ") must still match
    when it opens a sentence or a JSON field value — the boundary trim removes the
    space the cue relied on, which is how "…detected. No risk alerts, … or system
    outages were detected." scored as the forbidden claim `system_outage` under
    Suite v2 (E6b-G-both-dev S05-2000004). `_same_sentence_*` pad for that case.
    """
    before = _same_sentence_before(low, i)
    after = _same_sentence_after(low, end)
    return (any(cue in before for cue in _EXCLUSION_CUES)
            or any(cue in after for cue in _LOOKAHEAD_CUES))


def _excerpt(text: str, claim: str, pad: int = 90) -> str:
    """Text around the first asserted occurrence, for auditing a failed case."""
    low = text.lower()
    for phrase in (claim.replace("_", " "), claim):
        p = phrase.lower()
        i = low.find(p)
        while i != -1:
            if not _refuted(low, i, i + len(p)):
                return text[max(0, i - pad):i + len(p) + pad].replace("\n", " ")
            i = low.find(p, i + len(p))
    return "(no asserted occurrence located)"


def _asserts(text: str, phrase: str) -> bool:
    """Does `text` ASSERT `phrase`, as opposed to ruling it out?

    A bare substring match cannot tell the two apart, and the difference is the
    whole metric. E4 wrote "the decline was not caused by insufficient funds" —
    the correct finding for a risk hold, and exactly what a competent investigator
    should say — and it scored as the forbidden claim `insufficient_funds` in
    every S08 case, costing 8 points of all-pass for being right.

    Rule (Suite v3, `SUITE_V3_RELEASE_CONTRACT.md` § 2C): an occurrence is refuted
    iff a cue sits in the same sentence/field within `_EXCLUSION_WINDOW` chars before
    it (`_EXCLUSION_CUES`) or after it (`_LOOKAHEAD_CUES`). Any single un-refuted
    occurrence is a hit: refuting a claim in one sentence does not license asserting
    it in another. Hedges ("could be a contributing factor", "is unclear") are not
    cues — a hedged assertion is still an assertion.

    Known limitation, accepted deliberately: a genuine assertion sitting in the same
    sentence as an unrelated negation is missed. That is a false negative on a harm
    metric — the dangerous direction — so the windows are kept short, the lookahead
    cue list is kept to predicate negations, and `test_scorer_polarity` pins both
    directions.
    """
    low, p = text.lower(), phrase.lower()
    start = 0
    while (i := low.find(p, start)) != -1:
        if not _refuted(low, i, i + len(p)):
            return True
        start = i + len(p)
    return False


def score_case(
    *,
    result: InvestigationResult | None,
    trajectory: Trajectory,
    manifest: dict[str, Any],
    run_id: str,
    evidence_threshold: float = 0.8,
) -> CaseScore:
    dims: list[DimensionScore] = []

    tool_total = len(trajectory.tool_calls)
    escalated = trajectory.used_frontier

    # A run that produced nothing scores zero on everything rather than being
    # dropped — silently excluding failures would inflate every rate.
    if result is None:
        return CaseScore(
            scenario_id=manifest["scenario_id"], trace_id=str(trajectory.trace_id),
            experiment_arm=trajectory.experiment_arm or "unknown",
            root_cause_correct=False, required_evidence_recall=0.0,
            unsupported_claims=0, next_action_acceptable=False, verifier_passed=False,
            tool_calls_total=tool_total, tool_calls_useful=0,
            escalated_to_frontier=escalated, wall_ms=trajectory.wall_ms,
            reference_cost_usd=trajectory.reference_cost_usd,
            evidence_recall_threshold=evidence_threshold,
            dimensions=[DimensionScore(name="produced_output", value=0.0, passed=False,
                                       detail=trajectory.error or "no structured output")],
        )

    text = _output_text(result)

    # --- root cause ---------------------------------------------------------
    root_ok = result.root_cause.label.value == manifest["root_cause"]
    dims.append(DimensionScore(
        name="root_cause", value=1.0 if root_ok else 0.0, passed=root_ok,
        detail=f"said {result.root_cause.label.value}, truth {manifest['root_cause']}",
    ))

    # --- evidence recall ----------------------------------------------------
    # An id counts as found if it appears anywhere in the output: entity_ids,
    # a citation, or the prose. We are measuring whether the model surfaced the
    # right facts, not whether it filled a particular field.
    required = manifest["required_evidence"]
    found = [e for e in required if e.lower() in text]
    recall = len(found) / len(required) if required else 1.0
    dims.append(DimensionScore(
        name="evidence_recall", value=recall, passed=recall >= evidence_threshold,
        detail=f"{len(found)}/{len(required)} — missing {sorted(set(required) - set(found))}",
    ))

    # --- unsupported claims -------------------------------------------------
    v = trajectory.verification
    unsupported = 0
    if v is not None:
        unsupported = sum(
            1 for msg in v.violations
            if "citation" in msg or "never successfully called" in msg or "no tool returned" in msg
        )
    dims.append(DimensionScore(
        name="unsupported_claims", value=float(unsupported), passed=unsupported == 0,
    ))

    # --- forbidden claims ---------------------------------------------------
    # Scored separately from unsupported claims: a forbidden claim is not merely
    # uncited, it is actively harmful (e.g. asserting fraud from a mapping bug).
    #
    # Polarity-aware: see `_asserts`. Ruling a claim OUT is the opposite of making
    # it, and the bare substring match counted both.
    hits = [c for c in manifest.get("forbidden_claims", [])
            if _asserts(text, c.replace("_", " ")) or _asserts(text, c)]
    dims.append(DimensionScore(
        name="forbidden_claims", value=float(len(hits)), passed=not hits,
        # The matched text, not just the label. A forbidden claim fails the whole
        # case, so it has to be auditable after the fact — and every one seen so far
        # has been a refutation the matcher misread. Without the excerpt the only way
        # to tell a real one from a false positive was to re-run the case against a
        # non-deterministic frontier model and hope for the same phrasing.
        detail="; ".join(f"{c}: …{_excerpt(text, c)}…" for c in hits) if hits else None,
    ))

    # --- next action --------------------------------------------------------
    action_ok = result.recommended_next_action.value in manifest["acceptable_next_actions"]
    dims.append(DimensionScore(
        name="next_action", value=1.0 if action_ok else 0.0, passed=action_ok,
        detail=f"said {result.recommended_next_action.value}",
    ))

    # --- tool efficiency ----------------------------------------------------
    # A call is useful if its result contributed an id the model went on to cite.
    useful = sum(1 for c in trajectory.tool_calls if c.status == "success")
    dims.append(DimensionScore(name="tool_calls", value=float(tool_total), passed=True))

    return CaseScore(
        scenario_id=manifest["scenario_id"],
        trace_id=str(trajectory.trace_id),
        experiment_arm=trajectory.experiment_arm or "unknown",
        root_cause_correct=root_ok,
        required_evidence_recall=recall,
        unsupported_claims=unsupported,
        next_action_acceptable=action_ok,
        verifier_passed=bool(v and v.passed),
        forbidden_claim_made=bool(hits),
        tool_calls_total=tool_total,
        tool_calls_useful=useful,
        escalated_to_frontier=escalated,
        wall_ms=trajectory.wall_ms,
        api_ms=sum(i.latency.api_ms or 0 for i in trajectory.model_invocations) or None,
        reference_cost_usd=trajectory.reference_cost_usd,
        evidence_recall_threshold=evidence_threshold,
        dimensions=dims,
    )
