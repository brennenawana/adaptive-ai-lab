"""A router may be *scored* by ground truth. It may never be *fed* it.

The pivot guide: "Do not route using gold root cause, scenario ID, or required-
evidence recall; those are eval labels, not production signals." A router that read
them would look, in every aggregate, like a router that had learned the task — the
most invisible way for the routing result to be wrong. These tests make the leak a
schema error and a static-analysis error, so it fails at the point of writing
rather than at the point of interpreting a suspiciously good number.
"""

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas import GOLD_FEATURE_NAMES, RouteMode, RoutingRecord, ScenarioManifest

ROOT = Path(__file__).resolve().parents[1]

# Modules that decide or describe routing. Anything added under these paths
# inherits the import ban below.
ROUTING_MODULES = [
    ROOT / "fis_platform" / "model_gateway",
    ROOT / "schemas" / "routing.py",
    ROOT / "infra" / "switchyard",
]

# Where the answer key lives. Importing any of these from routing code is a leak
# whether or not the value is used yet.
FORBIDDEN_IMPORTS = {
    "evals.scorers", "evals.scorers.score", "schemas.scenario", "scenarios.generator",
    "scenarios.generator.catalog", "scenarios.generator.world",
}


def _py_files():
    for p in ROUTING_MODULES:
        if p.is_file():
            yield p
        elif p.is_dir():
            yield from p.rglob("*.py")


def test_gold_feature_list_covers_every_manifest_field():
    """If a new gold field is added to the manifest, this fails until it is added
    to GOLD_FEATURE_NAMES too — the list cannot silently fall behind the schema."""
    manifest_fields = set(ScenarioManifest.model_fields)
    # `case_id` and `subject_ids` are what the CASE carries and the model sees;
    # `generated_at` is bookkeeping. Everything else in the manifest is an answer.
    visible = {"case_id", "subject_ids", "generated_at"}
    assert manifest_fields - visible <= GOLD_FEATURE_NAMES, (
        sorted(manifest_fields - visible - GOLD_FEATURE_NAMES))


@pytest.mark.parametrize("leak", sorted(GOLD_FEATURE_NAMES))
def test_router_signals_reject_gold_features(leak):
    with pytest.raises(ValidationError, match="ground truth"):
        RoutingRecord(gateway="g", route_profile="p", route_mode=RouteMode.CASCADE,
                      router_signals={leak: 1.0})


def test_router_signals_accept_production_available_features():
    rec = RoutingRecord(gateway="g", route_profile="p", route_mode=RouteMode.CASCADE,
                        router_signals={"parse_ok": True, "verifier_ok": False,
                                        "evidence_bundle_chars": 41000})
    assert rec.router_signals["verifier_ok"] is False


def test_routing_code_never_imports_the_answer_key():
    offenders = []
    for path in _py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for n in names:
                if n in FORBIDDEN_IMPORTS or n.startswith("ground_truth"):
                    offenders.append(f"{path.relative_to(ROOT)}: {n}")
    assert not offenders, offenders


def test_switchyard_config_carries_no_scenario_knowledge():
    """The route bundle is transport config. Any scenario id, class label or gold
    field name in it means routing has started to key on the answer key."""
    cfg_dir = ROOT / "infra" / "switchyard"
    if not cfg_dir.exists():
        pytest.skip("no switchyard config yet")
    banned = set(GOLD_FEATURE_NAMES) | {"ground_truth", "manifest"}
    for path in cfg_dir.rglob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        hits = sorted(b for b in banned if b in text)
        assert not hits, f"{path.name} mentions {hits}"
        assert "S0" not in text and "S1" not in text, f"{path.name} names a scenario class"
