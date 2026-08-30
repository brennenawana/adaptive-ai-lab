"""Inference Agent: one CLI conversation per test case, Bash tool only,
paper App. E.1 system prompt with skills injected in full. Blind to the wiki
by construction (never receives wiki paths; runs in an isolated workdir that
contains only the input spreadsheet copy)."""

import shutil
from pathlib import Path

from . import config, gateway, prompts, scorer, tasksio


def _task_message(task: dict, workdir: Path, in_file: Path, out_file: Path) -> str:
    preview = tasksio.spreadsheet_preview(in_file)
    return (
        f"working_directory: {workdir}\n"
        f"instruction: {task['instruction']}\n"
        f"spreadsheet_path: {in_file}\n"
        f"spreadsheet_content:\n{preview}\n"
        f"instruction_type: {task['instruction_type']}\n"
        f"answer_position: {task['answer_position']}\n"
        f"output_path: {out_file}\n"
    )


def _trace_from_events(events: list) -> str:
    lines = []
    for ev in events:
        t = ev.get("type")
        msg = (ev.get("message") or {})
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            if t == "assistant" and block.get("type") == "text" and block.get("text"):
                lines.append(f"assistant: {block['text']}")
            elif t == "assistant" and block.get("type") == "tool_use":
                cmd = (block.get("input") or {}).get("command", "")
                lines.append(f"[bash] {cmd}")
            elif t == "user" and block.get("type") == "tool_result":
                content = block.get("content")
                if isinstance(content, list):
                    content = " ".join(str(c.get("text", "")) for c in content
                                       if isinstance(c, dict))
                lines.append(f"tool_result: {str(content)[:1500]}")
    return "\n".join(lines)


def run_test_case(*, task: dict, tc: int, skill_section: str, workroot: Path,
                  meter, iteration) -> dict:
    workdir = workroot / f"{task['id']}_tc{tc}"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    src_in, _ = tasksio.task_files(task, tc)
    in_file = workdir / src_in.name
    shutil.copy2(src_in, in_file)
    out_file = workdir / f"{tc}_{task['id']}_output.xlsx"

    # .replace, not .format: keeps verbatim prompts robust to literal braces.
    system = prompts.EXECUTOR_SYSTEM.replace("{skill_section}", skill_section)
    prompt = _task_message(task, workdir, in_file, out_file)
    wall_cap = config.TURN_CAP * config.CMD_TIMEOUT + 300

    try:
        payload, events = gateway.run_cli(
            meter=meter, role="executor", model=config.EXECUTOR_MODEL,
            system=system, prompt=prompt, cwd=str(workdir), tools="Bash",
            max_turns=config.TURN_CAP, stream=True, timeout=wall_cap,
            extra_env={"BASH_DEFAULT_TIMEOUT_MS": str(config.CMD_TIMEOUT * 1000),
                       "BASH_MAX_TIMEOUT_MS": str(config.CMD_TIMEOUT * 1000)},
            meta={"task": str(task["id"]), "tc": tc, "iter": iteration})
        crash = False
        trace = _trace_from_events(events)
        if payload.get("is_error") and not out_file.exists():
            trace += f"\n[run ended with is_error subtype={payload.get('subtype')}]"
    except gateway.GatewayError as e:
        crash, trace, out_file_exists = True, f"[harness crash: {e}]", False
        return {"tc": tc, "crash": True, "trace": trace, "output": None}

    return {"tc": tc, "crash": crash, "trace": trace,
            "output": out_file if out_file.exists() else None}


def run_task(*, task: dict, skill_section: str, workroot: Path, meter,
             iteration, keep_trace_dir: Path | None) -> dict:
    """Roll out all 3 test cases; score = upstream soft restriction."""
    tcs = [run_test_case(task=task, tc=tc, skill_section=skill_section,
                         workroot=workroot, meter=meter, iteration=iteration)
           for tc in tasksio.test_cases(task)]
    outputs = {r["tc"]: r["output"] for r in tcs}
    result = scorer.score_task(task, outputs)
    crash = any(r["crash"] for r in tcs)

    if keep_trace_dir is not None:
        keep_trace_dir.mkdir(parents=True, exist_ok=True)
        sections = [f"=== TASK {task['id']} ===",
                    f"INSTRUCTION: {task['instruction']}",
                    f"SCORE: soft={result['soft']:.3f} "
                    f"test_cases={result['test_case_results']}"]
        for r in tcs:
            sections += [f"--- test case {r['tc']} "
                         f"({'ok' if r['output'] else 'no output file'}) ---",
                         r["trace"]]
        (keep_trace_dir / f"{task['id']}.txt").write_text("\n".join(sections))

    # Workdirs are transient; keep disk bounded.
    for r in tcs:
        wd = workroot / f"{task['id']}_tc{r['tc']}"
        shutil.rmtree(wd, ignore_errors=True)

    return {"id": task["id"], "soft": result["soft"], "hard": result["hard"],
            "test_case_results": result["test_case_results"], "crash": crash}
