"""Wiki Maintainer: one optimizer call per iteration over the current wiki plus
a stratified trace sample (<=5 failing, <=3 passing, 15K chars each — paper
App. C). Output is the paper's JSON edit object, schema-enforced."""

import random

from . import config, gateway, prompts, wiki

MAINTAINER_SCHEMA = {
    "type": "object",
    "properties": {
        "create_patterns": {"type": "array", "items": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "content": {"type": "string"}},
            "required": ["name", "content"]}},
        "update_patterns": {"type": "array", "items": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "edits": {"type": "array", "items": {
                "type": "object",
                "properties": {"op": {"type": "string",
                                      "enum": ["append", "replace", "insert_after"]},
                               "target": {"type": "string"},
                               "content": {"type": "string"}},
                "required": ["op", "content"]}}},
            "required": ["name", "edits"]}},
        "update_index": {"type": "string"},
        "append_log": {"type": "string"},
    },
    "required": ["update_index", "append_log"],
}


def sample_traces(results: list, trace_dir, iteration: int) -> str:
    rng = random.Random(config.SUITE_SEED + iteration)
    fails = [r for r in results if r["soft"] < 1.0 and not r["crash"]]
    passes = [r for r in results if r["soft"] >= 1.0]
    rng.shuffle(fails)
    rng.shuffle(passes)
    chosen = fails[:config.SAMPLE_MAX_FAIL] + passes[:config.SAMPLE_MAX_PASS]
    parts = []
    for r in chosen:
        p = trace_dir / f"{r['id']}.txt"
        if p.exists():
            parts.append(p.read_text()[:config.TRACE_CHAR_CAP])
    return "\n\n".join(parts)


def maintain(*, run_dir, results: list, iteration: int, model: str, meter) -> list:
    traces = sample_traces(results, run_dir / "raw" / f"iter_{iteration}", iteration)
    user = (f"## Current Wiki\n\n{wiki.wiki_context(run_dir)}\n\n"
            f"## Execution Traces from Iteration {iteration}\n\n{traces}\n\n"
            "Analyze the traces against the current wiki and return the JSON "
            "edit object now.")
    payload, _ = gateway.run_cli(
        meter=meter, role="maintainer", model=model,
        system=prompts.MAINTAINER_SYSTEM, prompt=user,
        json_schema=MAINTAINER_SCHEMA, meta={"iter": iteration})
    ops = gateway.structured_or_json(payload)
    if not isinstance(ops, dict):
        return ["maintainer returned no parseable JSON; wiki unchanged"]
    return wiki.apply_maintainer_ops(run_dir, ops, iteration)
