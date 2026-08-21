"""Leakage-canary mechanism — the BIG-bench canary-string model, for FUTURE suites only.

`PLAYBOOK_ADAPTATION.md` §8: "canary GUIDs go into TEST scenario content
and any published excerpts (M-STAT lands the mechanism, inactive for frozen Suite v3 —
activating a canary changes the corpus digest, so activation happens only at the next
versioned suite release)." `M_STAT_IMPLEMENTATION_MAP.md` §9 states the constraint this
module exists to satisfy: `scripts/corpus_digest.py` digests every row of every table
the corpus writes, so injecting anything into the frozen Suite v3 corpus — even one
byte, even a GUID nobody reads — changes `corpus_digest` and breaks the v3 freeze that
`SUITE_V3_RELEASE_CONTRACT.md` § 4 recorded. This module is therefore built to be
provably inert for `SUITE_VERSION <= 3` (currently "3"): every function here either
takes no action or returns `None` on every code path that suite v3's generator run can
reach, and the one function that CAN turn a canary on refuses outright, `force` included,
for any suite that has already shipped.

The mechanism: a single, recognisable string embedded in TEST-split content only —
`canary_token()` — such that its appearance anywhere outside this repository (in model
output, in a scraped training corpus, in a leaderboard writeup) is direct evidence that
TEST content leaked. One GUID per suite release (`canary_guid`) so a leak can be dated to
the suite that produced it. Activation is a one-way, owner-level decision
(`CANARY_ACTIVE_FROM_SUITE`), not a runtime flag: the value the mechanism reads is a
constant in this file, not an environment variable, for the same reason
`fis_platform.provenance.default_root` refuses to be relocated — a relocatable toggle is
a reset button with extra steps.
"""

from __future__ import annotations

from uuid import UUID, uuid5

__all__ = [
    "CANARY_ACTIVE_FROM_SUITE",
    "CANARY_NAMESPACE",
    "CanaryRefused",
    "activate_canary",
    "canary_guid",
    "canary_token",
]

# Owner decision (playbook §8; implementation-map §9): the canary stays off through the
# Suite v3 freeze and switches on only with a future versioned suite release — Suite v4
# is the anticipated one, but the gate below is written against the number, not the name,
# so the owner can defer activation past v4 without touching this constant's meaning.
CANARY_ACTIVE_FROM_SUITE = 4

# Fixed namespace UUID (uuid5 of NAMESPACE_URL over a stable URL, computed once and
# hardcoded — the world-generator's ENVELOPE_NAMESPACE / DOMAIN_NAMESPACE pattern in
# `scenarios/generator/world.py` and `fis_platform/events/envelope.py`). Fixed so that
# `canary_guid` is reproducible from source alone, with no external state to lose.
CANARY_NAMESPACE = UUID("2e9ba0ae-9d7c-57b1-babd-bd49fc45b05a")


def canary_guid(suite_version: str | int) -> str:
    """One deterministic GUID per suite release: uuid5(CANARY_NAMESPACE, "fis-suite-
    canary-v<suite>"). Same suite -> same GUID on every call, on every machine, forever
    — the BIG-bench canary-string model needs exactly one recognisable string per
    release, not a fresh one per generation run, or a match could never be dated to the
    release that leaked it.
    """
    return str(uuid5(CANARY_NAMESPACE, f"fis-suite-canary-v{suite_version}"))


def canary_token(suite_version: str | int, split: str) -> str | None:
    """The literal string to embed in model-observable content, or `None` when the
    canary is not active for this (suite, split).

    Two independent conditions must both hold, and either's absence is `None`:
      * `int(suite_version) >= CANARY_ACTIVE_FROM_SUITE` — the suite has to be one the
        owner has actually released with the canary switched on; Suite v3 never
        qualifies, by construction of the constant above.
      * `split == "test"` — TRAIN and DEV are read repeatedly by design (screening,
        calibration, gate-setting); a canary planted there would fire on the lab's own
        legitimate use. Only TEST is the content whose appearance elsewhere is leakage.

    Returns `"FIS-CANARY-DO-NOT-TRAIN <guid> suite-v<suite>"` when active — the
    DO-NOT-TRAIN phrase makes an accidental hit self-explanatory even torn out of all
    context, and the trailing `suite-v<n>` dates it without a second lookup.
    """
    v = int(suite_version)
    if v < CANARY_ACTIVE_FROM_SUITE or split != "test":
        return None
    return f"FIS-CANARY-DO-NOT-TRAIN {canary_guid(v)} suite-v{v}"


class CanaryRefused(SystemExit):
    """A guard said no. Raised by `activate_canary` for any suite_version <= 3."""


def activate_canary(suite_version: str | int, *, force: bool = False) -> str:
    """Guard for future release tooling: the one call site allowed to say "this suite's
    canary is live." Refuses unconditionally for `suite_version <= 3` — Suite v3 (and
    everything before it) is a frozen, already-released corpus, and mutating a frozen
    suite's content is never legal no matter how the caller asks. `force` exists only so
    a caller cannot treat this refusal as a bypassable safety rail the way `force` is a
    legitimate escape hatch elsewhere in this codebase; here it changes nothing about
    the outcome, only about how loudly refusing insists on it.

    Returns the TEST-split canary token for `suite_version >= CANARY_ACTIVE_FROM_SUITE`
    — the only content activation is ever about, per `canary_token`'s split rule.
    """
    v = int(suite_version)
    if v <= 3:
        raise CanaryRefused(
            f"suite {suite_version} is frozen (<= 3) — activating a canary would mutate "
            f"an already-released suite's corpus digest and is refused unconditionally "
            f"(force={force} changes nothing: mutating a frozen suite is never legal)"
        )
    token = canary_token(v, "test")
    if token is None:
        # Unreachable given CANARY_ACTIVE_FROM_SUITE == 4 and v > 3 above, but a guard
        # that trusts its own invariant instead of checking it is the failure mode this
        # whole module exists to avoid.
        raise CanaryRefused(
            f"suite {suite_version} is >= CANARY_ACTIVE_FROM_SUITE={CANARY_ACTIVE_FROM_SUITE} "
            "but canary_token still returned None — refusing to activate on a mechanism "
            "that disagrees with itself"
        )
    return token
