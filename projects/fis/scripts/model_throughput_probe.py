"""Back-to-back throughput probe of local model endpoints on a real FIS prompt.

Latency measured *during* an eval run is confounded by whatever else the machine was
doing (a second model on the same card, power state, page cache). This sends the
identical request — a real dev case's fixed-evidence bundle under the frozen prompt —
to each endpoint in turn, several times, and reports what llama.cpp itself measured:
prompt processing (time-to-first-token proxy) and generation speed. Run it when
nothing else is on the GPU, and never during a paired eval run (it perturbs the
prompt cache).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path

import httpx
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.model_gateway import GenerationRequest, Message, ModelGateway, default_registry  # noqa: E402
from fis_platform.tool_broker.broker import ToolBroker  # noqa: E402
from schemas.investigator import InvestigationResult  # noqa: E402
from services.ai_orchestrator.investigate import _phase_one, _phase_two  # noqa: E402
from services.ai_orchestrator.prompts import PROMPTS  # noqa: E402

TOOLS_DSN = os.environ.get("FIS_TOOLS_DSN", "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis")
OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")


def build_prompt(scenario_id: str) -> str:
    with psycopg.connect(OWNER_DSN) as c, c.cursor() as cur:
        cur.execute("SELECT case_id FROM ground_truth.scenario_manifests WHERE scenario_id = %s", (scenario_id,))
        case_id = cur.fetchone()[0]
    with ToolBroker(TOOLS_DSN) as broker:
        case, _ = broker.invoke("get_case", {"case_id": case_id})
        results = [case]
        for tool, args in _phase_one(case):
            res, _ = broker.invoke(tool, args); results.append({tool: res})
        for tool, args in _phase_two(case, results):
            res, _ = broker.invoke(tool, args); results.append({tool: res})
    bundle = json.dumps(results, indent=2, default=str)
    return f"Case {case_id}.\n\nEvidence gathered from the platform:\n\n{bundle}\n\nDetermine the root cause."


async def probe(gw: ModelGateway, ref: str, user: str, prompt_ref: str, max_tokens: int, repeats: int) -> dict:
    req = GenerationRequest(model_ref=ref, system=PROMPTS[prompt_ref], messages=[Message(role="user", content=user)],
                            json_schema=InvestigationResult.model_json_schema(), max_tokens=max_tokens, purpose="probe")
    rows = []
    for _ in range(repeats):
        r = await gw.generate(req)
        t = (r.raw or {}).get("timings", {})
        rows.append({"prompt_n": t.get("prompt_n"), "prompt_ms": t.get("prompt_ms"), "prompt_tps": t.get("prompt_per_second"),
                     "gen_n": t.get("predicted_n"), "gen_ms": t.get("predicted_ms"), "gen_tps": t.get("predicted_per_second"),
                     "cache_n": t.get("cache_n"), "wall_ms": r.latency.wall_ms, "stop": r.stop_reason, "fp": r.runtime_fingerprint})
    return {"ref": ref, "runs": rows,
            "gen_tps_median": statistics.median(x["gen_tps"] or 0 for x in rows),
            "prompt_tps_cold": rows[0]["prompt_tps"], "ttft_cold_ms": rows[0]["prompt_ms"],
            "prompt_tps_warm": rows[-1]["prompt_tps"], "ttft_warm_ms": rows[-1]["prompt_ms"]}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", nargs="+", default=["local-specialist", "nemotron-lightning"])
    ap.add_argument("--scenario", default="S01-2000000")
    ap.add_argument("--prompt", default="cause_action_directed")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=2, help="alternate endpoints this many times")
    args = ap.parse_args()
    user = build_prompt(args.scenario)
    gw = ModelGateway(default_registry())
    print(f"probe prompt: {args.scenario}, ~{len(user)} chars, max_tokens {args.max_tokens}, repeats {args.repeats} × rounds {args.rounds}\n")
    for rnd in range(args.rounds):
        for ref in args.refs:
            res = await probe(gw, ref, user, args.prompt, args.max_tokens, args.repeats)
            r0, r1 = res["runs"][0], res["runs"][-1]
            print(f"round {rnd} {ref:<22} fp={r0['fp']}  prompt {r0['prompt_n']} tok: cold {r0['prompt_ms']:.0f} ms ({r0['prompt_tps']:.0f} tok/s), "
                  f"warm {r1['prompt_ms']:.0f} ms (cache_n {r1['cache_n']})  |  gen {r0['gen_n']} tok: "
                  f"{', '.join(f'{x['gen_tps']:.1f}' for x in res['runs'])} tok/s  |  wall {', '.join(str(x['wall_ms']) for x in res['runs'])} ms")
    print(f"\n{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")


if __name__ == "__main__":
    asyncio.run(main())
