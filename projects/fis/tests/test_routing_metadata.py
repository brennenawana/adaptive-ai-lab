"""Routing metadata enriches the canonical trajectory; it never replaces it.

The pivot guide's boundary: a routing gateway may own backend selection, fallback
and per-request stats, and FIS keeps the trajectory record, scoring and lineage.
These tests pin the shape that boundary takes in the schemas — a routed invocation
is an ordinary `ModelInvocation` with one extra optional field, and every derived
metric the scorer relies on is unchanged by it.
"""

import json

import pytest
from pydantic import ValidationError

from schemas import (
    LatencyRecord, ModelInvocation, ModelManifest, ModelTier, PriceTable, Provider,
    RouteMode, RoutingProfile, RoutingRecord, Trajectory,
)


def _inv(**kw) -> ModelInvocation:
    base = dict(tier=ModelTier.SPECIALIST, provider=Provider.SWITCHYARD,
                model_id="fis-local-specialist", prompt_version="1",
                latency=LatencyRecord(wall_ms=100))
    base.update(kw)
    return ModelInvocation(**base)


def _routed() -> RoutingRecord:
    return RoutingRecord(gateway="switchyard", gateway_version="0.2.0",
                         route_profile="fis-local-specialist", route_mode=RouteMode.PASSTHROUGH,
                         selected_backend="local-llamacpp-8082")


def test_direct_path_invocation_has_no_routing_record():
    """The control arm's record is unchanged: routing stays None."""
    inv = _inv(provider=Provider.LOCAL_LLAMACPP)
    assert inv.routing is None
    assert "routing" in inv.model_dump()  # present as a field, empty by default


def test_routed_invocation_round_trips_through_trajectory_json():
    """What goes into learning.trajectories (JSONB of model_dump_json) must come back
    identical, or the R1 comparison would be reading a lossy record."""
    traj = Trajectory(workflow="w", workflow_version="1", task_type="t", user="u",
                      model_invocations=[_inv(routing=_routed(), stop_reason="stop")])
    again = Trajectory.model_validate(json.loads(traj.model_dump_json()))
    assert again.model_invocations[0].routing == _routed()
    assert again.model_invocations[0].stop_reason == "stop"


def test_routing_does_not_change_derived_metrics():
    """`used_frontier`, cost and wall time are computed from tier/cost/latency —
    a passthrough route to a local model must not read as cloud escalation."""
    plain = Trajectory(workflow="w", workflow_version="1", task_type="t", user="u",
                       model_invocations=[_inv(provider=Provider.LOCAL_LLAMACPP)])
    routed = Trajectory(workflow="w", workflow_version="1", task_type="t", user="u",
                        model_invocations=[_inv(routing=_routed())])
    assert plain.used_frontier is routed.used_frontier is False
    assert plain.wall_ms == routed.wall_ms
    assert plain.reference_cost_usd == routed.reference_cost_usd


def test_manifest_provider_and_profile_must_agree():
    """A manifest that says SWITCHYARD without a profile (or a profile without the
    provider) is lying about its transport, and R1's claim rests on that not
    being possible."""
    profile = RoutingProfile(gateway="switchyard", route_profile="p",
                             route_mode=RouteMode.PASSTHROUGH, backends=["b"],
                             all_backends_local=True)
    common = dict(tier=ModelTier.SPECIALIST, model_id="m", context_window=4096,
                  max_output_tokens=512, base_url="http://127.0.0.1:4000/v1")
    with pytest.raises(ValidationError, match="disagree"):
        ModelManifest(ref="a", provider=Provider.SWITCHYARD, **common)
    with pytest.raises(ValidationError, match="disagree"):
        ModelManifest(ref="b", provider=Provider.LOCAL_LLAMACPP, routing=profile, **common)
    ok = ModelManifest(ref="c", provider=Provider.SWITCHYARD, routing=profile, **common)
    assert ok.routing.route_mode is RouteMode.PASSTHROUGH


def test_frontier_via_gateway_still_needs_a_price():
    """Routing through a gateway does not make a frontier backend free."""
    profile = RoutingProfile(gateway="switchyard", route_profile="p",
                             route_mode=RouteMode.PASSTHROUGH, backends=["cloud"],
                             all_backends_local=False)
    with pytest.raises(ValidationError, match="PriceTable"):
        ModelManifest(ref="f", tier=ModelTier.FRONTIER, provider=Provider.SWITCHYARD,
                      routing=profile, model_id="m", context_window=4096,
                      max_output_tokens=512, base_url="http://127.0.0.1:4000/v1")
    ModelManifest(ref="g", tier=ModelTier.FRONTIER, provider=Provider.SWITCHYARD,
                  routing=profile, model_id="m", context_window=4096, max_output_tokens=512,
                  base_url="http://127.0.0.1:4000/v1",
                  price=PriceTable(basis="t", input_per_mtok=1, output_per_mtok=1))
