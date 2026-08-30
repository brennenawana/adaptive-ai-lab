"""The WikiSkill evolution loop (paper Alg. 1) under the lab's stop criteria.

Wiki persists across iterations and is never rolled back; skills are gated on
strict validation improvement. Every halt is clean: state.json checkpoints
after each step, and BudgetExceeded exits with the ledger intact."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import config, executor, maintainer, proposer, wiki
from .budget import BudgetExceeded, Meter


def _rollout(tasks: list, skill_section: str, *, run_dir: Path, meter,
             iteration, trace_name: str | None, workers: int) -> list:
    trace_dir = (run_dir / "raw" / trace_name) if trace_name else None

    def one(task):
        return executor.run_task(task=task, skill_section=skill_section,
                                 workroot=run_dir / "workdirs", meter=meter,
                                 iteration=iteration, keep_trace_dir=trace_dir)

    if workers <= 1:
        results = [one(t) for t in tasks]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(one, tasks))

    crash_rate = sum(r["crash"] for r in results) / max(len(results), 1)
    if crash_rate > config.CRASH_RATE_HALT:
        meter.log_event("halt", reason="S9-crash-rate", rate=crash_rate)
        raise RuntimeError(f"S9: crash rate {crash_rate:.0%} exceeds "
                           f"{config.CRASH_RATE_HALT:.0%} — rig defect, not evidence")
    return results


def mean_soft(results: list) -> float:
    return sum(r["soft"] for r in results) / max(len(results), 1)


def _checkpoint(run_dir: Path, state: dict) -> None:
    (run_dir / "state.json").write_text(json.dumps(state, indent=2))


def run_evolution(*, arm: str, seed: int, phase: str, train: list, val: list,
                  k_iterations: int = config.K_ITERATIONS,
                  workers: int = config.ROLLOUT_WORKERS,
                  run_id: str | None = None, audit: bool = False,
                  force_full_loop: bool = False) -> dict:
    run_id = run_id or f"{arm}{seed}-{time.strftime('%Y%m%d-%H%M%S')}"
    run_dir = config.RUNS_DIR / run_id
    wiki.init_workspace(run_dir)
    meter = Meter(phase=phase, run_id=run_id, arm=arm, run_dir=run_dir,
                  iteration_projection_usd=config.ITERATION_PROJECTION_USD.get(arm))
    optimizer_model = config.OPTIMIZER_MODEL.get(arm)

    state_file = run_dir / "state.json"
    state = (json.loads(state_file.read_text()) if state_file.exists() else
             {"run_id": run_id, "arm": arm, "seed": seed, "iteration_done": 0,
              "r_best": None, "accepted": [], "plateau": 0, "stop_reason": None})

    def finish(stop_reason: str) -> dict:
        state["stop_reason"] = stop_reason
        state["spend_usd_equiv"] = meter.run_spend()
        _checkpoint(run_dir, state)
        (run_dir / "summary.json").write_text(json.dumps(state, indent=2))
        return state

    try:
        # Iteration 0: baseline validation with the current (initially empty) skill set.
        if state["r_best"] is None:
            meter.new_iteration(0)
            base = _rollout(val, wiki.skills_text(run_dir / "skills"),
                            run_dir=run_dir, meter=meter, iteration=0,
                            trace_name="iter_0_baseline" if audit else None,
                            workers=workers)
            state["r_best"] = mean_soft(base)
            meter.log_event("baseline_val", score=state["r_best"])
            _checkpoint(run_dir, state)

        if arm == "A":
            return finish("baseline-only")

        for k in range(state["iteration_done"] + 1, k_iterations + 1):
            if not force_full_loop:
                if state["r_best"] >= 1.0:
                    return finish("early-stop-val-100")
                if state["plateau"] >= config.PLATEAU_STOP:
                    return finish("EARLY-PLATEAU")

            meter.new_iteration(k)
            skill_section = wiki.skills_text(run_dir / "skills")

            train_results = _rollout(train, skill_section, run_dir=run_dir,
                                     meter=meter, iteration=k,
                                     trace_name=f"iter_{k}", workers=workers)
            meter.log_event("train_rollout", score=mean_soft(train_results),
                            n=len(train_results))

            notes = maintainer.maintain(run_dir=run_dir, results=train_results,
                                        iteration=k, model=optimizer_model,
                                        meter=meter)
            if notes:
                meter.log_event("maintainer_notes", notes=notes)

            prop = proposer.propose(run_dir=run_dir, results=train_results,
                                    iteration=k, model=optimizer_model,
                                    meter=meter)
            meter.log_event("proposal", action=prop.get("action"),
                            name=prop.get("name"))

            if prop.get("action") == "no_action":
                wiki.record_skill_impact(run_dir, iteration=k, proposal=prop,
                                         val_score="-", best_before=state["r_best"],
                                         outcome="NO_ACTION", diff="")
                state["plateau"] += 1
                state["iteration_done"] = k
                _checkpoint(run_dir, state)
                continue

            cand = wiki.stage_candidate(run_dir)
            changed, diff, notes = wiki.apply_proposal(cand, prop)
            if not changed:
                wiki.record_skill_impact(run_dir, iteration=k, proposal=prop,
                                         val_score="-", best_before=state["r_best"],
                                         outcome=f"INVALID ({'; '.join(notes)})",
                                         diff="")
                state["plateau"] += 1
                state["iteration_done"] = k
                _checkpoint(run_dir, state)
                continue

            val_results = _rollout(val, wiki.skills_text(cand), run_dir=run_dir,
                                   meter=meter, iteration=k,
                                   trace_name=f"iter_{k}_val" if audit else None,
                                   workers=workers)
            score = mean_soft(val_results)
            accepted = score > state["r_best"]
            wiki.record_skill_impact(run_dir, iteration=k, proposal=prop,
                                     val_score=f"{score:.4f}",
                                     best_before=state["r_best"],
                                     outcome="ACCEPTED" if accepted else "REJECTED",
                                     diff=diff)
            meter.log_event("gate", score=score, best=state["r_best"],
                            accepted=accepted)
            if accepted:
                wiki.promote_candidate(run_dir)
                state["r_best"] = score
                state["accepted"].append({"iteration": k,
                                          "action": prop.get("action"),
                                          "name": prop.get("name"),
                                          "val": score})
                state["plateau"] = 0
            else:
                state["plateau"] += 1

            state["iteration_done"] = k
            _checkpoint(run_dir, state)

        return finish("completed-K")

    except BudgetExceeded as e:
        meter.log_event("halt", reason=str(e))
        return finish(f"STOPPED-BUDGET: {e}")
    except RuntimeError as e:  # S9
        return finish(str(e))


def evaluate_split(*, arm: str, run_id: str, phase: str, tasks: list,
                   split_name: str, skills_from: str | None = None,
                   workers: int = config.ROLLOUT_WORKERS) -> dict:
    """One pre-registered look at a held-out split (S11: caller owns the look
    ledger). skills_from names a run whose accepted skills/ to inject."""
    run_dir = config.RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    meter = Meter(phase=phase, run_id=run_id, arm=arm, run_dir=run_dir)
    meter.new_iteration(-1)
    skill_section = ""
    if skills_from:
        skill_section = wiki.skills_text(config.RUNS_DIR / skills_from / "skills")
    results = _rollout(tasks, skill_section, run_dir=run_dir, meter=meter,
                       iteration=-1, trace_name=None, workers=workers)
    out = {"run_id": run_id, "split": split_name, "n": len(results),
           "mean_soft": mean_soft(results),
           "mean_hard": sum(r["hard"] for r in results) / max(len(results), 1),
           "per_task": results, "skills_from": skills_from}
    (run_dir / f"eval_{split_name}.json").write_text(json.dumps(out, indent=2))
    return out
