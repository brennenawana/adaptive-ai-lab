"""M0 — frozen truncation-outcome classification + the pre-registered paired order.

FROZEN BEFORE WP-B INFERENCE (docs/current/NEXT_STEP_M0.md § 6-B, rev 4). This module
is committed before any treatment generation exists, and its rules are not adjusted
after outcomes are seen. The adversarial-review question it must survive: "were the
classification rules frozen before treatment-body inspection?" — the freeze commit
containing this file, made before the paired probe ran, is the evidence.

Three things live here, all deterministic:

  1. PRIMARY_CASES — the pre-registered 15-case population (NEXT_STEP_M0.md § 5),
     restated in code so every M0 script and test shares one source. Verified against
     learning.case_scores ⋈ learning.trajectories and the registry freeze record
     (calibration.cap.per_cap."8192".capped = 15) before this file was written.
  2. paired_order() — the deterministic AB/BA counterbalancing: cases sorted
     lexicographically by scenario_id, even 0-based index → AB (control first),
     odd → BA (treatment first).
  3. classify_treatment() / truncation_shape() — the (a)-(d) outcome classes and the
     convergent-vs-degenerate rubric for still-truncated reasoning, operationalising
     the three pre-declared heuristics (repetition rate, distinct-hypothesis count,
     evidence accumulation) with a priori thresholds.

Thresholds are a priori (no historical reasoning text exists to calibrate on — R6
persisted only lengths), justified in-line, and exercised on synthetic fixtures in
tests/test_m0_classify.py. The manual read of each case (n is small) is recorded
BESIDE the rubric verdict in the probe artifact, never in place of it; the (c)/(d)
counts in the frozen metric table are the rubric's.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.investigator import RootCauseLabel

# ------------------------------------------------------------------ population

#: NEXT_STEP_M0.md § 5 — the 15 verified Qwen3.8 Q3_K_M TRAIN cap-hit cases.
#: 8 scenario classes; every seed in the TRAIN range. Cases that cap-hit only on
#: other R6 arms are EXCLUDED (they enter Pass-1 context only, never this list).
PRIMARY_CASES: tuple[str, ...] = (
    "S02-1001001", "S02-1002001", "S05-1002004", "S06-1001005", "S07-1000006",
    "S07-1001006", "S07-1002006", "S08-1002007", "S10-1000009", "S10-1001009",
    "S11-1000010", "S11-1001010", "S11-1002010", "S12-1000011", "S12-1001011",
)

#: The historical control cap and the treatment target named by the M0 doc. The
#: treatment cap actually used is WP-C-certified and recorded in the probe artifact;
#: TREATMENT_TARGET_CAP is what WP-C certifies against, not a promise.
CONTROL_CAP = 8192
TREATMENT_TARGET_CAP = 12288


def paired_order(cases: tuple[str, ...] = PRIMARY_CASES) -> list[tuple[str, str]]:
    """The pre-registered counterbalanced order (NEXT_STEP_M0.md § 6-B).

    Cases sorted lexicographically by scenario_id; even 0-based index → "AB"
    (control first, then treatment), odd → "BA". Deterministic: no RNG, no input
    other than the case list itself.
    """
    return [(sid, "AB" if i % 2 == 0 else "BA") for i, sid in enumerate(sorted(cases))]


# ------------------------------------------------------------------ outcome classes

#: Treatment outcome classes, exactly the M0 doc's (a)-(d) plus one pre-declared edge:
#:   a  completed & passed (rescue)
#:   b  completed (parseable, no length stop) & failed
#:   c  still truncated (stop_reason == length), reasoning convergent
#:   d  still truncated, reasoning degenerate/circular
#:   e  EDGE (pre-declared): no length stop but no parseable object either — counted
#:      in NEITHER f_rescue, f_wrong_complete NOR f_complete; reported in its own row.
OUTCOME_CLASSES = ("a", "b", "c", "d", "e")


@dataclass
class TruncationShape:
    """Deterministic measurements over a still-truncated generation's reasoning."""

    reasoning_chars: int
    content_chars: int
    token_count: int
    trigram_count: int
    distinct_trigram_count: int
    dup_rate: float                  # 1 - distinct/total trigrams (whole text)
    tail_novelty: float              # fraction of final-quarter trigrams unseen earlier
    distinct_hypotheses: int         # distinct RootCauseLabel values mentioned anywhere
    tail_new_hypothesis: bool        # final quarter mentions a label unseen earlier
    tail_new_evidence: bool          # final quarter contains an unseen evidence token
    fired: list[str] = field(default_factory=list)
    verdict: str = "convergent"      # "convergent" | "degenerate" | "no_reasoning"


# The rubric's frozen thresholds, with the a-priori rationale:
#   D1 tail_novelty < 0.10   a reasoning stream that keeps working introduces new
#                            trigrams to the end; formulaic/JSON-adjacent prose keeps
#                            some repetition, so the bar is set LOW (0.10) — only a
#                            near-verbatim loop fails it.
#   D2 no new evidence AND no new hypothesis in the final quarter — convergence
#                            without new material is fine ONCE; combined with the
#                            other signals it marks treading water.
#   D3 dup_rate > 0.50       more than half of all trigrams are repeats — the
#                            whole-text signature of circular generation.
# Verdict: degenerate iff >= 2 of {D1, D2, D3} fire. One indicator alone never
# condemns a case (each has benign causes); two independent ones are the signature.
D1_TAIL_NOVELTY_LT = 0.10
D3_DUP_RATE_GT = 0.50
DEGENERATE_MIN_FIRED = 2

_TOKEN_RE = re.compile(r"[a-z0-9_./:-]+")
_EVIDENCE_TOKEN_RE = re.compile(r"^(?=.*\d)[a-z0-9_./:-]{6,}$")
_HYPOTHESES = tuple(v.value for v in RootCauseLabel if v is not RootCauseLabel.UNKNOWN)


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _trigrams(tokens: list[str]) -> list[tuple[str, str, str]]:
    return [tuple(tokens[i:i + 3]) for i in range(len(tokens) - 2)]


def truncation_shape(reasoning_text: str | None, content_text: str | None = None
                     ) -> TruncationShape:
    """The frozen rubric, applied to one still-truncated generation.

    Pre-declared special case: a truncation with NO reasoning text and non-empty
    content text was cut INSIDE the answer — the model had left reasoning, which is
    itself the convergence signal (R6 found 16/47 TEST cap-hits in this shape).
    Verdict "convergent". A truncation with neither text is "no_reasoning"
    (unclassifiable, reported as its own row, never silently binned).
    """
    reasoning = reasoning_text or ""
    content = content_text or ""
    if not reasoning.strip():
        shape = TruncationShape(
            reasoning_chars=0, content_chars=len(content), token_count=0,
            trigram_count=0, distinct_trigram_count=0, dup_rate=0.0, tail_novelty=1.0,
            distinct_hypotheses=0, tail_new_hypothesis=False, tail_new_evidence=False)
        shape.verdict = "convergent" if content.strip() else "no_reasoning"
        return shape

    toks = _tokens(reasoning)
    tris = _trigrams(toks)
    distinct = set(tris)
    dup_rate = 1.0 - (len(distinct) / len(tris)) if tris else 0.0

    # The final quarter, by token position — the region a loop occupies.
    cut = max(1, int(len(toks) * 0.75))
    head_toks, tail_toks = toks[:cut], toks[cut:]
    head_tris = set(_trigrams(head_toks))
    tail_tris = _trigrams(tail_toks)
    tail_novelty = (sum(1 for t in tail_tris if t not in head_tris) / len(tail_tris)
                    if tail_tris else 0.0)

    head_text = " ".join(head_toks)
    tail_text = " ".join(tail_toks)
    head_hyp = {h for h in _HYPOTHESES if h in head_text}
    tail_hyp = {h for h in _HYPOTHESES if h in tail_text}
    all_hyp = head_hyp | tail_hyp
    tail_new_hypothesis = bool(tail_hyp - head_hyp)

    head_ev = {t for t in head_toks if _EVIDENCE_TOKEN_RE.match(t)}
    tail_new_evidence = any(t not in head_ev for t in tail_toks
                            if _EVIDENCE_TOKEN_RE.match(t))

    fired: list[str] = []
    if tail_novelty < D1_TAIL_NOVELTY_LT:
        fired.append("D1-tail-novelty")
    if not tail_new_evidence and not tail_new_hypothesis:
        fired.append("D2-no-new-material")
    if dup_rate > D3_DUP_RATE_GT:
        fired.append("D3-dup-rate")

    shape = TruncationShape(
        reasoning_chars=len(reasoning), content_chars=len(content),
        token_count=len(toks), trigram_count=len(tris),
        distinct_trigram_count=len(distinct), dup_rate=round(dup_rate, 4),
        tail_novelty=round(tail_novelty, 4), distinct_hypotheses=len(all_hyp),
        tail_new_hypothesis=tail_new_hypothesis, tail_new_evidence=tail_new_evidence,
        fired=fired)
    shape.verdict = "degenerate" if len(fired) >= DEGENERATE_MIN_FIRED else "convergent"
    return shape


def classify_treatment(*, stop_reason: str | None, passed: bool, parseable: bool,
                       reasoning_text: str | None,
                       content_text: str | None) -> tuple[str, TruncationShape | None]:
    """One treatment generation → its frozen outcome class (a)-(e).

    `passed` is the deterministic scorer's all_pass on the treatment generation;
    `parseable` is whether a structured object was recovered (schema-valid parse).

    Precedence (frozen): a deterministic PASS is a rescue (a) whatever the stop
    reason — f_rescue's definition is "treatment passes among reconfirmed cap-hits",
    and a pass that grazed the new cap is still a pass. Then: length stop → (c)/(d)
    by the rubric; parseable non-pass → (b); the remainder → (e). The five classes
    partition every generation exactly once.
    """
    if passed:
        return "a", None
    if stop_reason == "length":
        shape = truncation_shape(reasoning_text, content_text)
        return ("d" if shape.verdict == "degenerate" else "c"), shape
    if parseable:
        return "b", None
    return "e", None
