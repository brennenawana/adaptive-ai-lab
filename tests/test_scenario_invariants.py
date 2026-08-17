"""Suite v3 scenario invariants — deterministic world properties, independent of any
model, checked over EVERY corpus seed (96 test / 48 dev / 144 train).

`SUITE_V3_RELEASE_CONTRACT.md` § 2 and § 4. Each invariant names the Suite v2 defect
it closes; a world that violates one is a benchmark defect wearing a model's clothes,
which is the failure mode that has cost this project the most time.
"""

from __future__ import annotations

from collections import Counter

import pytest

from fis_platform.events.projection import project
from scenarios.generator.catalog import BUILDERS
from scenarios.generator.run import SPLIT_RANGES, build

CODES = sorted(BUILDERS)
PER_CLASS = {"test": 8, "dev": 4, "train": 12}      # Makefile `corpus`

# Classes whose customer holds a card and transacts; each carries background purchases.
CARD_ACTIVITY = {"S01", "S02", "S05", "S06", "S07", "S08", "S10", "S11"}
NO_SETTLEMENTS = {"S03", "S04", "S09", "S12"}


def corpus_plan() -> list[tuple[str, int]]:
    """Exactly the seeds `make corpus` generates, in generation order."""
    plan = []
    for split, (lo, _) in SPLIT_RANGES.items():
        for idx, code in enumerate(CODES):
            for i in range(PER_CLASS[split]):
                plan.append((code, lo + i * 1000 + idx))
    return plan


@pytest.fixture(scope="module")
def corpus():
    worlds = {}
    for code, seed in corpus_plan():
        world, manifest = build(code, seed)
        worlds[manifest["scenario_id"]] = (world, manifest, project(world.published, world.mapping_versions))
    return worlds


def _by_class(corpus, code):
    return [(w, m, p) for sid, (w, m, p) in corpus.items() if sid.startswith(code + "-")]


# ---------------------------------------------------------------- A. background settlements
@pytest.mark.parametrize("code", CODES)
def test_every_settlement_is_posted_exactly_once_except_the_injected_defects(corpus, code):
    """v2: `_distractors` settlements were never published, so six classes carried
    S10's fault signature as ambient noise. v3: a settlement without exactly one
    posting exists only where the scenario injects it (S02 posts twice, S10 not at
    all), and classes without card activity have no settlements."""
    for world, manifest, proj in _by_class(corpus, code):
        postings = Counter(e["reference_id"] for e in proj.entries if e["reference_type"] == "settlement")
        if code in NO_SETTLEMENTS:
            assert not world.settlements and not postings, f"{manifest['scenario_id']} has settlements"
            continue
        assert code in CARD_ACTIVITY
        for sett in world.settlements:
            n = postings.get(sett["settlement_id"], 0)
            if code == "S02" and sett is world.settlements[0]:
                assert n == 2, f"{manifest['scenario_id']}: the missing-key settlement must post twice"
            elif code == "S10" and sett is world.settlements[0]:
                assert n == 0, f"{manifest['scenario_id']}: the gap settlement must not post"
            else:
                assert n == 1, (f"{manifest['scenario_id']}: settlement {sett['settlement_id']} "
                                f"posted {n} times")
        # ...and nothing posts that no settlement or reversal explains.
        refs = {s["settlement_id"] for s in world.settlements} | {a["auth_id"] for a in world.authorizations}
        assert {e["reference_id"] for e in proj.entries} <= refs


@pytest.mark.parametrize("code", sorted(CARD_ACTIVITY))
def test_background_purchases_exist_and_are_addressable(corpus, code):
    """Background activity is real: approved authorizations with settlements, each
    published under its own provider_ref (reachable by get_webhook_history) with a
    safe idempotency key, and named in the manifest's distractor ids where the class
    has background."""
    for world, manifest, proj in _by_class(corpus, code):
        approved = [a for a in world.authorizations if a["processor_state"] == "approved"]
        assert approved, f"{manifest['scenario_id']} has no approved activity"
        pev_to_events = {}
        for e in world.published:
            pev_to_events.setdefault(e.provider_event_id, []).append(e)
        refs = {s["provider_ref"] for s in world.settlements}
        for sett in world.settlements:
            if code == "S10" and sett is world.settlements[0]:
                assert sett["provider_ref"] not in pev_to_events
                continue
            events = pev_to_events[sett["provider_ref"]]
            assert all(e.event_type == "settlement.created" for e in events)
            assert all(e.raw_payload["reference_id"] == sett["settlement_id"] for e in events)
        assert all(e.provider_event_id in refs or e.event_type != "settlement.created"
                   for e in world.published)
        if code not in {"S10", "S11"}:
            auth_ids = {a["auth_id"] for a in world.authorizations}
            alert_ids = {a["alert_id"] for a in world.alerts}
            assert manifest["distractor_event_ids"], f"{manifest['scenario_id']} names no distractors"
            assert set(manifest["distractor_event_ids"]) <= auth_ids | alert_ids


@pytest.mark.parametrize("code", CODES)
def test_nothing_post_dates_the_case(corpus, code):
    """v2 generated background purchases AFTER `add_case`, so a card frozen at T
    approved purchases at T+ and a case opened at T investigated activity from T+.
    An operator opens a case about what has happened."""
    for world, manifest, proj in _by_class(corpus, code):
        opened = world.cases[0]["opened_at"]
        sid = manifest["scenario_id"]
        stamps = (
            [("verification", v["event_time"]) for v in world.verifications]
            + [("authorization", a["authorized_at"]) for a in world.authorizations]
            + [("reversal", a["reversed_at"]) for a in world.authorizations if a["reversed_at"]]
            + [("settlement", s["settled_at"]) for s in world.settlements]
            + [("alert", a["raised_at"]) for a in world.alerts]
            + [("failed delivery", d["received_at"]) for d in world.deliveries]
            + [("published", e.published_at) for e in world.published]
            + [("occurred", e.occurred_at) for e in world.published]
            + [("entry", e["posted_at"]) for e in proj.entries]
        )
        late = [(k, t) for k, t in stamps if t > opened]
        assert not late, f"{sid}: {late[:3]} post-date the case ({opened})"


@pytest.mark.parametrize("code", CODES)
def test_deliveries_are_received_after_their_events_occurred(corpus, code):
    """v2 S07 'received' both webhooks at T+2/T+4 for events that occurred at
    T+75/T+65. A delivery cannot precede the event it delivers; the race is late
    delivery of an EARLIER event, which requires published_at >= occurred_at."""
    for world, manifest, _ in _by_class(corpus, code):
        for e in world.published:
            assert e.published_at >= e.occurred_at, (
                f"{manifest['scenario_id']}: {e.event_type} received {e.published_at} "
                f"before it occurred {e.occurred_at}")


@pytest.mark.parametrize("code", CODES)
def test_only_the_injected_defect_corrupts_or_inverts(corpus, code):
    """No accidental second defect: exactly S06's injected posting differs from its
    settlement (mapper v3 on that event only; v4 on the rest), and exactly S07 has a
    posted_at inversion in posting order — one, between the reversal and the late
    settlement."""
    for world, manifest, proj in _by_class(corpus, code):
        sid = manifest["scenario_id"]
        by_sett = {s["settlement_id"]: s for s in world.settlements}
        corrupted = [e for e in proj.entries
                     if e["reference_type"] == "settlement"
                     and e["amount"] != by_sett[e["reference_id"]]["amount"]]
        if code == "S06":
            assert len(corrupted) == 1 and corrupted[0]["reference_id"] == world.settlements[0]["settlement_id"], sid
            assert world.mapping_versions[0] == 3 and set(world.mapping_versions[1:]) == {4}, sid
        else:
            assert not corrupted, f"{sid}: {corrupted}"
            assert 3 not in world.mapping_versions, sid

        inversions = [(a, b) for a, b in zip(proj.entries, proj.entries[1:])
                      if a["account_id"] == b["account_id"] and b["posted_at"] < a["posted_at"]]
        if code == "S07":
            assert len(inversions) == 1, f"{sid}: {len(inversions)} inversions"
            assert inversions[0][0]["reference_type"] == "reversal"
            assert inversions[0][1]["reference_type"] == "settlement"
        else:
            assert not inversions, f"{sid}: unexpected posting-order inversion"


@pytest.mark.parametrize("code", CODES)
def test_injected_evidence_is_named_and_reachable_before_background(corpus, code):
    """The fixed-evidence plan follows the first six provider refs it discovers in
    time order (`_phase_two`). Required webhook/ledger evidence therefore has to
    belong to activity that precedes the background — S01/S02/S06/S07 generate the
    injected settlement first. Checked structurally: every required id is produced,
    and any required pipeline id descends from the first published event of its
    provider ref."""
    for world, manifest, proj in _by_class(corpus, code):
        produced = proj.ids()
        for attr, key in (("verifications", "verification_id"), ("accounts", "account_id"),
                          ("cards", "card_id"), ("authorizations", "auth_id"),
                          ("settlements", "settlement_id"), ("alerts", "alert_id"),
                          ("deliveries", "delivery_id"), ("cases", "case_id")):
            produced |= {r[key] for r in getattr(world, attr)}
        missing = [e for e in manifest["required_evidence"] if e not in produced]
        assert not missing, f"{manifest['scenario_id']}: {missing}"
        if code in {"S01", "S02", "S06", "S07"}:
            # In time order the refs are: card, then authorizations, then settlements.
            # The injected authorization must precede every background one so that
            # the injected settlement lands within the first six refs.
            auths = sorted(world.authorizations, key=lambda a: a["authorized_at"])
            setts = sorted(world.settlements, key=lambda s: s["settled_at"])
            assert auths[0]["auth_id"] == world.authorizations[0]["auth_id"], manifest["scenario_id"]
            assert setts[0]["settlement_id"] == world.settlements[0]["settlement_id"], manifest["scenario_id"]
            refs = ([world.cards[0]["provider_ref"]] + [a["provider_ref"] for a in auths]
                    + [s["provider_ref"] for s in setts])
            assert world.settlements[0]["provider_ref"] in refs[:6], manifest["scenario_id"]


def test_corpus_plan_matches_the_makefile():
    plan = corpus_plan()
    assert len(plan) == 288
    assert Counter(seed // 1_000_000 for _, seed in plan) == {1: 144, 2: 48, 3: 96}


# ---------------------------------------------------------------- B. amounts vs balances
def test_s08_2003007_declined_amount_is_below_the_available_balance():
    """The recorded Suite v2 defect, reproduced by seed: dev S08-2003007 declined
    70 530 against an available balance of 17 530, which made the forbidden
    `insufficient_funds` hypothesis data-consistent (`routing-experiments.md` § R2).
    Under v3 semantics the balance is the snapshot at case time and the injected
    decline is the last thing before the case, so it must fit inside it."""
    world, manifest = build("S08", 2_003_007)
    declined = [a for a in world.authorizations if a["processor_state"] == "declined"]
    assert len(declined) == 1
    assert declined[0]["amount"] < world.accounts[0]["available_balance"], (
        f"{manifest['scenario_id']}: declined {declined[0]['amount']} > "
        f"available {world.accounts[0]['available_balance']}")


@pytest.mark.parametrize("code", ["S05", "S08"])
def test_declines_are_consistent_with_the_balance_snapshot(corpus, code):
    """S08 (risk hold): the decline is NOT a funding problem, so the amount must fit
    the balance. S05 (insufficient funds): it IS one, so the amount must exceed it,
    and available == ledger since nothing else explains a gap between them."""
    for world, manifest, _ in _by_class(corpus, code):
        acc = world.accounts[0]
        (declined,) = [a for a in world.authorizations if a["processor_state"] == "declined"]
        if code == "S08":
            assert declined["amount"] < acc["available_balance"], manifest["scenario_id"]
            assert declined["decline_code"] == "62_RESTRICTED_CARD"
        else:
            assert declined["amount"] > acc["available_balance"], manifest["scenario_id"]
            assert declined["decline_code"] == "51_INSUFFICIENT_FUNDS"
        assert acc["available_balance"] == acc["ledger_balance"], (
            f"{manifest['scenario_id']}: available {acc['available_balance']} != "
            f"ledger {acc['ledger_balance']} with no hold to explain it")


@pytest.mark.parametrize("code", CODES)
def test_every_account_balance_pair_is_consistent(corpus, code):
    """Balances are a snapshot at case time (contract § 2B). No builder models a
    hold, so available and ledger balance agree everywhere."""
    for world, manifest, _ in _by_class(corpus, code):
        for acc in world.accounts:
            assert acc["available_balance"] == acc["ledger_balance"], manifest["scenario_id"]
            assert acc["available_balance"] > 0
