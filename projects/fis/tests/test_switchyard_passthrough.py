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
from fis_platform.model_gateway.schema_compat import (
    key_order_invariant, property_order, to_gbnf_safe,
)
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
    assert b._post.__func__ is LocalLlamaCppAdapter._post   # same transport code
    assert a.manifest.base_url != b.manifest.base_url
    assert ":4000" in b.manifest.base_url


def _sorted_keys(o):
    """What Switchyard 0.2.0's Rust core does to every object on the way through."""
    if isinstance(o, dict):
        return {k: _sorted_keys(o[k]) for k in sorted(o)}
    if isinstance(o, list):
        return [_sorted_keys(x) for x in o]
    return o


def test_request_body_is_identical_on_both_paths_except_the_schema_rewrite():
    """R1 premise, restated after R0.1: everything but the schema representation is
    byte-identical, and the schema differs only by the key-order-invariant rewrite."""
    gw = ModelGateway(default_registry())
    body_a = gw.adapter(DIRECT).build_body(_req(DIRECT))
    body_b = gw.adapter(ROUTED).build_body(_req(ROUTED))
    sa, sb = body_a["response_format"]["json_schema"]["schema"], body_b["response_format"]["json_schema"]["schema"]
    assert sb == key_order_invariant(sa)
    body_a["response_format"]["json_schema"]["schema"] = None
    body_b["response_format"]["json_schema"]["schema"] = None
    assert json.dumps(body_a) == json.dumps(body_b)


def test_key_order_invariant_preserves_property_order_and_requiredness_under_sorting():
    """The whole point: after Switchyard sorts every key, the property order the
    grammar will enforce is still the declared one, for every object in the schema."""
    schema = to_gbnf_safe(InvestigationResult.model_json_schema())
    routed = _sorted_keys(key_order_invariant(schema))
    objects = {"root": (schema, routed)}
    for name in schema["$defs"]:
        objects[name] = (schema["$defs"][name], routed["$defs"][name])
    for name, (orig, after) in objects.items():
        if "properties" not in orig:
            continue                                     # enums etc.
        assert property_order(after) == list(orig["properties"]), name
        assert property_order(_sorted_keys(orig)) != list(orig["properties"]) or len(orig["properties"]) < 2, (
            f"{name}: fixture no longer demonstrates the problem")
        req_after = {p for comp in after["allOf"] if "anyOf" not in comp for p in comp["properties"]}
        assert req_after == set(orig.get("required", [])), name
        assert "additionalProperties" not in after and "properties" not in after
    # Idempotent: applying it to an already-rewritten schema changes nothing.
    assert key_order_invariant(key_order_invariant(schema)) == key_order_invariant(schema)


def _llamacpp_converter():
    """llama.cpp's reference JSON-schema->GBNF converter (examples/), if the build
    the model server runs from is on this machine. Skipped otherwise."""
    import importlib.util
    import os
    from dotenv import dotenv_values
    env = {**dotenv_values(ROOT / ".env"), **os.environ}
    llama_dir = Path(env.get("FIS_LLAMA_DIR") or Path.home() / "llama.cpp-upstream").expanduser()
    src = llama_dir / "examples" / "json_schema_to_grammar.py"
    if not src.exists():
        pytest.skip(f"llama.cpp converter not found at {src}")
    spec = importlib.util.spec_from_file_location("llama_j2g", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def grammar(schema):
        import copy
        conv = mod.SchemaConverter(prop_order={}, allow_fetch=False, dotall=False, raw_pattern=False)
        resolved = conv.resolve_refs(copy.deepcopy(schema), "fis")
        conv.visit(resolved, "")
        return conv.format_grammar()
    return grammar


def test_grammar_through_switchyard_equals_grammar_on_the_direct_path():
    """The R0.1 claim, checked with llama.cpp's own converter: the schema the gateway
    forwards (rewritten, then key-sorted) compiles to the byte-identical grammar text
    the direct path's plain schema compiles to — while the plain schema, key-sorted,
    does not. Live confirmation: identical output digests through the gateway."""
    grammar = _llamacpp_converter()
    gw = ModelGateway(default_registry())
    direct = gw.adapter(DIRECT).build_body(_req(DIRECT))["response_format"]["json_schema"]["schema"]
    routed = gw.adapter(ROUTED).build_body(_req(ROUTED))["response_format"]["json_schema"]["schema"]
    assert grammar(_sorted_keys(routed)) == grammar(direct)
    assert grammar(_sorted_keys(direct)) != grammar(direct), "fixture no longer shows the bug"


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


def test_schema_property_order_is_not_alphabetical__why_r0_1_exists():
    """Executable note. Switchyard 0.2.0's Rust core re-serialises every JSON object
    with sorted keys; llama.cpp compiles the response schema to a GBNF grammar that
    enforces property ORDER. With a non-alphabetical schema a plain passthrough
    changed the grammar and the model's output (R1: 0/48 identical). R0.1 fixed it in
    the adapter (`key_order_invariant`), which is only worth its existence while this
    assertion holds. If the schema is ever canonicalised alphabetically (a suite bump
    — it re-baselines the local arm), this fails to say the rewrite can go, and the
    R1/R0.1 numbers need re-measuring."""
    props = list(InvestigationResult.model_json_schema()["properties"])
    assert props != sorted(props), (
        "schema property order became alphabetical: re-baseline the local arm, re-run R1")


def _live_ok() -> bool:
    """Opt-in (FIS_LIVE_TESTS=1) AND both servers up.

    Opt-in on purpose: a request to the local model perturbs its prompt-cache state,
    and case-level local results reproduce only within one server session with the
    same request order — so a stray `make test` during a paired run would silently
    change one case of the arm it interrupted. The default suite must never touch
    :8082.
    """
    import os
    if os.environ.get("FIS_LIVE_TESTS") != "1":
        return False
    try:
        return all(httpx.get(u, timeout=1.0).status_code == 200 for u in
                   ("http://127.0.0.1:4000/health", "http://127.0.0.1:8082/health"))
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _live_ok(), reason="set FIS_LIVE_TESTS=1 with Switchyard on 4000 and llama.cpp on 8082")
def test_live_passthrough_reaches_llamacpp():
    import asyncio
    gw = ModelGateway(default_registry())
    req = GenerationRequest(model_ref=ROUTED, messages=[Message(role="user", content="hi")],
                            max_tokens=1)
    resp = asyncio.run(gw.generate(req))
    assert not resp.is_error, resp.error
    assert resp.routing is not None and resp.routing.upstream_model == SWITCHYARD_PASSTHROUGH_ROUTE
