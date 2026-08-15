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
