"""Skill Proposer: ReAct exploration of wiki + traces, one atomic proposal.

Declared deviation D4 from the paper's tool set: `read_file` is served by the
CLI's Read tool (workspace-restricted by cwd + prompt contract), and
`finish(proposal)` is served by schema-enforced final JSON output instead of a
tool call. A `traces/` symlink to the current iteration's raw directory keeps
the paper's `traces/<task_id>` paths literally valid."""

import os
from pathlib import Path

from . import config, gateway, prompts

PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["create", "patch", "no_action"]},
        "name": {"type": "string"},
        "skill_md": {"type": "string"},
        "purpose_md": {"type": "string"},
        "edits": {"type": "array", "items": {
            "type": "object",
            "properties": {"op": {"type": "string",
                                  "enum": ["append", "replace", "insert_after"]},
                           "target": {"type": "string"},
                           "content": {"type": "string"}},
            "required": ["op", "content"]}},
    },
    "required": ["action"],
}

TOOL_MAPPING_NOTE = """

## Tool Mapping (this environment)

- `read_file(path)` is available as the **Read** tool. Use paths under the
  workspace root given in the task message (wiki/, skills/, traces/<task_id>.txt).
- `finish(proposal)` is not a tool here: when your investigation is complete,
  output the proposal JSON object as your final answer (the output format is
  schema-enforced). Everything else about the workflow and rules is unchanged."""


def _outcome_summary(results: list) -> str:
    lines = ["task_id | soft_score | verdict"]
    for r in sorted(results, key=lambda x: str(x["id"])):
        verdict = "PASS" if r["soft"] >= 1.0 else ("CRASH" if r["crash"] else "FAIL")
        lines.append(f"{r['id']} | {r['soft']:.3f} | {verdict}")
    return "\n".join(lines)


def propose(*, run_dir: Path, results: list, iteration: int, model: str,
            meter) -> dict:
    # traces/ alias -> this iteration's raw traces (paper §E.3 note).
    alias = run_dir / "traces"
    if alias.is_symlink() or alias.exists():
        alias.unlink()
    os.symlink(run_dir / "raw" / f"iter_{iteration}", alias)

    index = (run_dir / "wiki" / "index.md").read_text()
    impact = (run_dir / "wiki" / "skill-impact.md").read_text()
    user = (f"Workspace root: {run_dir}\n\n"
            f"## wiki/index.md\n\n{index}\n\n"
            f"## wiki/skill-impact.md\n\n{impact}\n\n"
            f"## Training task outcomes (iteration {iteration})\n\n"
            f"{_outcome_summary(results)}\n\n"
            "Begin your investigation. Read pattern pages and execution traces "
            "as needed, then produce your proposal.")

    # .replace, not .format: the verbatim prompt contains literal JSON braces.
    system = prompts.PROPOSER_SYSTEM.replace("{task_desc}", prompts.TASK_DESC) + TOOL_MAPPING_NOTE
    try:
        payload, _ = gateway.run_cli(
            meter=meter, role="proposer", model=model, system=system,
            prompt=user, cwd=str(run_dir), tools="Read",
            max_turns=config.PROPOSER_TURN_CAP, json_schema=PROPOSAL_SCHEMA,
            timeout=1800, meta={"iter": iteration})
    finally:
        if alias.is_symlink():
            alias.unlink()

    proposal = gateway.structured_or_json(payload)
    if not isinstance(proposal, dict) or "action" not in proposal:
        return {"action": "no_action", "note": "unparseable proposer output"}
    return proposal
