"""R1 — the Switchyard passthrough arm must differ from the direct arm by transport only.

These pin, without a server, everything about the routed registry entry that has to
be identical to the direct entry for the equivalence experiment to mean anything —
and pin, as an executable note, the one thing that was found NOT to survive the hop.
"""

import json
from pathlib import Path

import httpx
import pytest

from fis_platform.model_gateway import (
    GenerationRequest, GenerationResponse, Message, ModelGateway, SwitchyardAdapter,
    default_registry,
)
from fis_platform.model_gateway.gateway import SWITCHYARD_PASSTHROUGH_ROUTE, SWITCHYARD_ROUTES_YAML
from fis_platform.model_gateway.local import LocalLlamaCppAdapter
from schemas import DataPolicy, LatencyRecord, ModelTier, Provider, RouteMode
from schemas.investigator import InvestigationResult

ROOT = Path(__file__).resolve().parents[1]
DIRECT, ROUTED = "local-specialist", "local-specialist-switchyard"


def _req(ref: str) -> GenerationRequest:
    return GenerationRequest(
        model_ref=ref, system="You are an investigator.",
        messages=[Message(role="user", content="Case case_1. Determine the root cause.")],
        json_schema=InvestigationResult.model_json_schema(), max_tokens=64,
    )


def test_routed_entry_describes_the_same_model_as_the_direct_entry():
    reg = default_registry()
    a, b = reg.resolve(DIRECT), reg.resolve(ROUTED)
    same = ("tier", "canonical_model", "quantization", "context_window", "max_output_tokens",
            "supports_tool_calling", "supports_structured_output", "supports_seed", "price")
    for field in same:
        assert getattr(a, field) == getattr(b, field), field
    assert a.provider is Provider.LOCAL_LLAMACPP and b.provider is Provider.SWITCHYARD
    assert b.routing is not None and b.routing.route_mode is RouteMode.PASSTHROUGH
    assert b.routing.all_backends_local is True
    assert b.model_id == SWITCHYARD_PASSTHROUGH_ROUTE == a.model_id, (
        "route id must equal the direct model_id so the request body is byte-identical")


def test_routed_adapter_is_the_local_adapter_with_a_different_base_url():
    gw = ModelGateway(default_registry())
    a, b = gw.adapter(DIRECT), gw.adapter(ROUTED)
    assert type(a) is LocalLlamaCppAdapter and isinstance(b, SwitchyardAdapter)
    assert isinstance(b, LocalLlamaCppAdapter)          # inherits, does not reimplement
    assert b.build_body.__func__ is LocalLlamaCppAdapter.build_body  # not overridden
    assert a.manifest.base_url != b.manifest.base_url
    assert ":4000" in b.manifest.base_url


def test_request_body_is_byte_identical_on_both_paths():
    """This is the R1 premise. If it fails, the routed arm is a different experiment."""
    gw = ModelGateway(default_registry())
    body_a = gw.adapter(DIRECT).build_body(_req(DIRECT))
    body_b = gw.adapter(ROUTED).build_body(_req(ROUTED))
    assert json.dumps(body_a) == json.dumps(body_b)


def test_local_only_policy_is_honoured_through_the_gateway():
    """A passthrough to a local backend keeps data on the machine — the profile says
    so, and the check has to read the profile rather than the provider."""
    gw = ModelGateway(default_registry())
    req = _req(ROUTED).model_copy(update={"data_policy": DataPolicy.LOCAL_ONLY})
    gw.adapter(ROUTED)._check_policy(req)   # must not raise


def test_annotate_records_only_what_the_gateway_reported():
    gw = ModelGateway(default_registry())
    b = gw.adapter(ROUTED)
    resp = GenerationResponse(text="{}", model_id="x", provider=Provider.SWITCHYARD,
                              tier=ModelTier.SPECIALIST, latency=LatencyRecord(wall_ms=1),
                              raw={"model": "fis-local-specialist"})
    out = b._annotate(resp, httpx.Headers({}))
    r = out.routing
    assert r is not None
    assert r.gateway == "switchyard" and r.route_mode is RouteMode.PASSTHROUGH
    assert r.upstream_model == "fis-local-specialist"
    # A passthrough chain records no selection; the record must say so honestly.
    assert r.selected_backend is None and r.decision_id is None
    assert r.escalated is False and r.fallback_used is False


def test_route_bundle_declares_exactly_the_passthrough_the_registry_expects():
    yaml = pytest.importorskip("yaml")
    cfg = yaml.safe_load((ROOT / SWITCHYARD_ROUTES_YAML).read_text(encoding="utf-8"))
    assert set(cfg) == {"defaults", "routes"}
    assert cfg["defaults"]["base_url"] == "http://127.0.0.1:8082/v1"
    assert cfg["defaults"]["api_key"] == "", "empty string, or Switchyard falls back to $OPENAI_API_KEY"
    assert cfg["defaults"]["format"] == "openai", "'auto' probes the upstream at startup"
    assert list(cfg["routes"]) == [SWITCHYARD_PASSTHROUGH_ROUTE]
    route = cfg["routes"][SWITCHYARD_PASSTHROUGH_ROUTE]
    assert route["type"] == "model"
    assert route["model"] == SWITCHYARD_PASSTHROUGH_ROUTE, "route id == upstream model: the rewrite is a no-op"


def test_route_bundle_loads_in_switchyard_itself():
    """Parse the committed bundle with the installed Switchyard, so a schema drift
    in a future Switchyard version fails here rather than at `make serve-switchyard`."""
    rb = pytest.importorskip("switchyard.cli.route_bundle")
    table = rb.load_route_bundle_table(str(ROOT / SWITCHYARD_ROUTES_YAML))
    assert list(table.registered_models()) == [SWITCHYARD_PASSTHROUGH_ROUTE]


def test_schema_property_order_is_not_alphabetical__the_known_r1_difference():
    """Executable note on the one thing that does NOT survive the hop.

    Switchyard 0.2.0's Rust core re-serialises every JSON object with sorted keys
    (serde_json without preserve_order). The request that reaches llama.cpp is
    semantically equal but the `properties` of the response schema arrive in
    alphabetical order — and llama.cpp compiles the JSON schema to a GBNF grammar
    that enforces property ORDER, so the model is forced to emit e.g. `facts`
    before `root_cause` and its output changes. Verified byte-for-byte with a tap
    on 2026-08-16 (docs/routing-experiments.md, R1).

    While this assertion holds, exact equivalence through Switchyard 0.2.0 is not
    achievable for the grammar-constrained local arm, and every R1 report must
    carry the measured delta. If someone canonicalises the schema order (a suite
    bump — it changes the frozen local baseline), this test fails to remind them
    that the R1 result and the baseline both need re-measuring.
    """
    props = list(InvestigationResult.model_json_schema()["properties"])
    assert props != sorted(props), (
        "schema property order became alphabetical: re-baseline the local arm and re-run R1")


def _both_servers_up() -> bool:
    try:
        return all(httpx.get(u, timeout=1.0).status_code == 200 for u in
                   ("http://127.0.0.1:4000/health", "http://127.0.0.1:8082/health"))
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _both_servers_up(), reason="needs Switchyard on 4000 and llama.cpp on 8082")
def test_live_passthrough_reaches_llamacpp():
    import asyncio
    gw = ModelGateway(default_registry())
    req = GenerationRequest(model_ref=ROUTED, messages=[Message(role="user", content="hi")],
                            max_tokens=1)
    resp = asyncio.run(gw.generate(req))
    assert not resp.is_error, resp.error
    assert resp.routing is not None and resp.routing.upstream_model == SWITCHYARD_PASSTHROUGH_ROUTE
