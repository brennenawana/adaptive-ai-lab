"""Canonical round-robin scenario ordering — playbook §4, M-STAT implementation map §4.

Normative rule (playbook §4, "TRAIN screening and calibration"): every run whose
prefix might inform a decision runs in deterministic round-robin order across the
12 scenario classes (S01, S02, ..., S12) — not the class-blocked `ORDER BY
scenario_id` the runner uses today (`evals/runner/run_eval.py:249`). This is not
cosmetic: class-blocked order has been measured to produce 5.4x worse prefix
estimates than round-robin, because the first N cases of a blocked run are N cases
of one class rather than a stratified sample of all of them — so any early-stop,
ASHA-rung, or interim-look decision that reads a prefix (TRAIN screening, and DEV/
TEST wherever curtailment arithmetic reads a prefix) is reading a biased slice of
the design under the old order.

The interleave this module produces: sort scenario ids within each class
lexicographically (which is seed order, since ids are `Sxx-` + a zero-padded
7-digit seed), then emit the 1st id of each class in class order (S01, S02, ...,
S12), then the 2nd of each, and so on. A class with fewer remaining members is
simply skipped once it is exhausted — unequal class sizes interleave without gaps
or padding. The whole thing is a pure function of the id set: no RNG, no
wall-clock, no external state, so the same input always orders the same way.

Comparability boundary (declared here, not resolved here): changing execution
order changes each case's prompt-cache predecessor within a local llama.cpp server
session — a documented source of within-session nondeterminism, since KV-cache
reuse depends on what request came immediately before. A round-robin run and a
historical class-blocked run therefore do not share predecessor structure case for
case, even when they cover the same scenario ids: case-level comparisons between
the two are descriptive only, never a paired statistical claim. An experiment
contract that wants to make a paired claim against historical data must say so and
account for it; this module's job is only to produce the canonical order and let
`is_round_robin` prove a given run used it.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Sequence

__all__ = [
    "MalformedScenarioId",
    "class_of",
    "is_round_robin",
    "round_robin",
    "round_robin_rows",
]

# Scenario id shape, pinned in schemas/scenario.py: `Sxx-` + a 7-digit seed. The class
# is the first 3 characters (the capture group), e.g. "S01" of "S01-1000000".
_ID_PATTERN = re.compile(r"^(S\d{2})-\d{7}$")


class MalformedScenarioId(SystemExit):
    """A scenario id did not match `^S\\d{2}-\\d{7}$`.

    The round-robin ordering is defined entirely by class membership (the id's
    first 3 characters) and seed order (the remaining 7 digits). An id that does
    not parse cleanly has no well-defined class or seed rank, and any attempt to
    guess one — truncating, loosely regexing, treating a prefix as "close enough"
    — would silently corrupt the interleave for every class after it. Fail closed
    instead: an ordering built on a guess is not the canonical order.
    """


def class_of(scenario_id: str) -> str:
    """The class key (`S01`..`S12` for in-suite ids; any `Sxx` prefix parses) of one
    scenario id. Raises `MalformedScenarioId` — never guesses — when `scenario_id`
    does not match the `Sxx-<7 digits>` shape.
    """
    match = _ID_PATTERN.match(scenario_id)
    if match is None:
        raise MalformedScenarioId(
            f"{scenario_id!r} does not match the scenario id shape ^S\\d{{2}}-\\d{{7}}$ "
            "— refusing to guess its class"
        )
    return match.group(1)


def _grouped(ids: Sequence[str]) -> dict[str, list[str]]:
    """Ids bucketed by `class_of`, each bucket sorted lexicographically (seed order).
    Bucket iteration order is irrelevant here — `round_robin` sorts the class keys
    itself — so a plain dict (insertion order = first-seen class) is fine.
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for scenario_id in ids:
        groups[class_of(scenario_id)].append(scenario_id)
    for members in groups.values():
        members.sort()
    return groups


def round_robin(ids: Sequence[str]) -> list[str]:
    """The canonical class-balanced round-robin order of `ids` (playbook §4).

    Groups by class, sorts each class's ids lexicographically (seed order), then
    interleaves: the 1st id of every class present, in class order (S01, S02, ...),
    then the 2nd of every class, and so on. A class that runs out simply drops out
    of later rounds — this is what keeps a prefix of the output class-balanced even
    when the classes are not equal-sized (a 12-case prefix has one case of each of
    12 classes present; a 5-class input still fills a 5-case prefix with 5 distinct
    classes, not padding). Deterministic and pure: the output depends only on the
    id set, never on input order, wall-clock, or randomness.
    """
    groups = _grouped(ids)
    class_order = sorted(groups)
    max_len = max((len(members) for members in groups.values()), default=0)
    out: list[str] = []
    for round_idx in range(max_len):
        for cls in class_order:
            members = groups[cls]
            if round_idx < len(members):
                out.append(members[round_idx])
    return out


def round_robin_rows(rows: Sequence[dict], key: str = "scenario_id") -> list[dict]:
    """`round_robin`, applied to the runner's manifest rows rather than bare ids.

    Each row is returned by reference (never copied or rebuilt) so callers can rely
    on row identity — the same dict objects, reordered. Rows sharing a scenario id
    (not expected in a manifest, but not assumed impossible) are handed back in
    their original relative order for that id: a queue per id, filled in input
    order and drained in canonical order, so nothing is dropped or duplicated.
    """
    queues: dict[str, deque] = defaultdict(deque)
    ids: list[str] = []
    for row in rows:
        scenario_id = row[key]
        ids.append(scenario_id)
        queues[scenario_id].append(row)
    return [queues[scenario_id].popleft() for scenario_id in round_robin(ids)]


def is_round_robin(ids: Sequence[str]) -> bool:
    """True iff `ids` is EXACTLY the canonical round-robin order of its own id set —
    i.e. `list(ids) == round_robin(ids)`. This is the check a run's provenance can
    cite to prove it used the canonical order rather than merely covering the same
    ids in some other sequence (e.g. the class-blocked `ORDER BY scenario_id` this
    ordering replaces).
    """
    return list(ids) == round_robin(ids)
