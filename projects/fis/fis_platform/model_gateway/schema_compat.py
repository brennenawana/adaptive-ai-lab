"""Make a JSON Schema safe for llama.cpp's GBNF converter.

llama.cpp compiles JSON Schema into a grammar and supports only a subset of the
vocabulary. Measured on this build (commit 9b05354): `minLength`/`maxLength` cause
`failed to parse grammar` and a 400. Regex `pattern` is fine; `enum`, `$ref` and
`$defs` are fine.

Stripping these is not a loss of enforcement, because the two mechanisms do
different jobs:

    grammar  -> guarantees the output SHAPE (valid JSON, right keys, enum members)
    verifier -> guarantees the output SEMANTICS (citation format, id existence,
                confidence calibration, length)

The strict Pydantic model still validates every response in the verifier, so a
too-short summary is still caught — just at validation time rather than being made
unrepresentable during decoding.
"""

from __future__ import annotations

import copy
from typing import Any

# Verified unsupported by this llama.cpp build's schema->GBNF converter.
_UNSUPPORTED = frozenset({
    "minLength", "maxLength",
    "minItems", "maxItems",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "format",
})


def to_gbnf_safe(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively drop constraint keywords the converter cannot compile."""

    def scrub(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: scrub(v) for k, v in node.items() if k not in _UNSUPPORTED}
        if isinstance(node, list):
            return [scrub(v) for v in node]
        return node

    return scrub(copy.deepcopy(schema))


def stripped_keywords(schema: dict[str, Any]) -> set[str]:
    """Which unsupported keywords were present — worth logging once per run so a
    silently-relaxed constraint is visible rather than surprising."""
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in _UNSUPPORTED:
                    found.add(k)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(schema)
    return found


# --------------------------------------------------------------------------------------
# Key-order invariance (R0.1)
# --------------------------------------------------------------------------------------
#
# llama.cpp compiles a JSON schema to a GBNF grammar that enforces object properties
# in the ORDER they appear in `properties`. Any hop that re-serialises JSON with sorted
# keys (NeMo Switchyard 0.2.0's Rust core does) therefore changes the grammar, and a
# greedy model's output with it — measured in R1 as 0/48 identical outputs.
#
# JSON arrays survive key sorting. llama.cpp's converter (C++ and the reference Python
# in examples/) builds an object rule from `allOf` by appending each component's
# properties in array order, marking a component's properties required unless the
# component sits inside `anyOf`, and passing no additionalProperties (which the rule
# builder treats exactly like `false`). So an object written as
#
#     {"type": "object", "allOf": [{"properties": {p1: s1}}, {"anyOf": [{"properties": {p2: s2}}]}, ...]}
#
# compiles to the SAME rule text as {"type":"object","properties":{p1:s1,p2:s2},
# "required":[p1],"additionalProperties":false} — one property per component, so
# sorting keys inside a component is a no-op, and the array fixes the order.
# `tests/test_switchyard_passthrough.py` pins grammar equality with llama.cpp's own
# converter, and R0.1 confirmed it end to end (identical output digests through the
# gateway).
#
# Applied ONLY on the routed path. The direct path keeps sending the plain schema it
# was baselined with; the transform is provably a no-op there and stays out of it.

def key_order_invariant(schema: dict[str, Any]) -> dict[str, Any]:
    """Rewrite every object schema so its property order survives key sorting."""

    def rewrite(node: Any) -> Any:
        if isinstance(node, list):
            return [rewrite(x) for x in node]
        if not isinstance(node, dict):
            return node
        out = {k: rewrite(v) for k, v in node.items()}
        # Explicit `type: object` only. The allOf components this function emits
        # carry `properties` but no `type`, so a second application (or a nested
        # walk) leaves them alone — the transform is idempotent.
        if out.get("type") == "object" and isinstance(out.get("properties"), dict) \
                and "allOf" not in out:
            required = set(out.get("required") or [])
            components = []
            for name, sub in out["properties"].items():
                comp = {"properties": {name: sub}}
                components.append(comp if name in required else {"anyOf": [comp]})
            # `additionalProperties` must go: an object that still carries it is
            # routed to the converter's `properties` branch with an empty property
            # list. The allOf branch forbids additional properties anyway.
            for k in ("properties", "required", "additionalProperties"):
                out.pop(k, None)
            out["allOf"] = components
        return out

    return rewrite(copy.deepcopy(schema))


def property_order(schema: dict[str, Any]) -> list[str]:
    """Property names of an object schema in grammar order, whichever form it is in.
    Test helper: the order must be the same before and after key sorting."""
    if "allOf" in schema:
        names: list[str] = []
        for comp in schema["allOf"]:
            for c in comp.get("anyOf", [comp]):
                names += list(c.get("properties", {}))
        return names
    return list(schema.get("properties", {}))
