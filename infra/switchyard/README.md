# NeMo Switchyard in FIS — routing middleware, nothing above it

`nemo-switchyard` (pinned **0.2.0**, `uv pip install --python .venv/bin/python
"nemo-switchyard[cli,server]==0.2.0"`) runs as an OpenAI-compatible listener on
**127.0.0.1:4000** and forwards to the model backends FIS already has. It is the
first implementation behind the *routing* boundary of the pivot guide; it can be
replaced by editing this directory and one registry entry.

```
orchestrator ── FIS gateway (GenerationRequest) ── adapter ── :4000 Switchyard ── :8082 llama.cpp
                                                     │
                                       (direct path: adapter ── :8082 llama.cpp)
```

## What Switchyard owns here, and what it does not

| Switchyard owns | FIS keeps |
|---|---|
| protocol translation between LLM APIs | scenario truth, task ontology, ground_truth schema |
| backend selection *inside* a route profile | which evidence / tools a task may use (`FIXED_EVIDENCE` plan) |
| strong/weak splitting, fallback (later R-series) | prompt variants (`prompts.py`) and the response grammar |
| per-request backend stats (`/v1/stats`, `/metrics`, routing log JSONL) | required-evidence sets, reachability ceilings, the scorer, dev/test split |
| OpenAI / Anthropic backend plumbing | the canonical trajectory (`learning.trajectories`) and experiment lineage |

Whatever the gateway reports about a request is copied into the FIS trajectory as
`ModelInvocation.routing` (`schemas/routing.py`), and only what it *actually*
reported — a passthrough records `selected_backend=None`, it is not back-filled.
`tests/test_routing_no_gold_leak.py` forbids scenario/gold names in this directory.

## Files

| File | Purpose |
|---|---|
| `routes.yaml` | the route bundle. R1: one `type: model` route `fis-local-specialist` → `http://127.0.0.1:8082/v1` |
| `serve.sh` | `make serve-switchyard`: starts the listener with `--routing-log-file`, waits for `/health`, prints the served route ids |

Make targets: `serve-switchyard`, `stop-switchyard`, `switchyard-health`, `switchyard-stats`.
Registry entry: `local-specialist-switchyard` (`fis_platform/model_gateway/gateway.py`);
adapter: `fis_platform/model_gateway/switchyard.py`.

## Configuration facts that cost time (0.2.0)

- The YAML loader has **no `type: passthrough`**; a single-target route is
  `type: model` (aliases `direct`, `target`, `llm_target`). `passthrough` is the
  Rust `routes.toml` spelling.
- Route id (the YAML key) is what clients send as `model`; the route's `model:` is
  what goes upstream. Switchyard **rewrites `model`** to the target value — the one
  request field it changes on a non-streaming call. FIS sets both to
  `fis-local-specialist` so the rewrite is a no-op.
- `api_key` **must be the empty string** for a key-less backend. Omitting it makes
  Switchyard fall back to `$OPENAI_API_KEY` and send it to llama.cpp.
- `format: openai` is pinned. `format: auto` probes the upstream at startup and
  *requires* an api_key.
- Default `--host` is `0.0.0.0`; `serve.sh` passes `127.0.0.1`. Default port 4000.
- No default upstream timeout (the FIS adapter enforces its own 600 s), no retries,
  no fallback on a passthrough route. Stats are always on (`enable_stats` is not an
  accepted key for `type: model`).
- Endpoints besides `/v1/chat/completions`: `/health`, `/v1/models`, `/v1/stats`,
  `/v1/routing/stats`, `/metrics`, `/v1/messages`, `/v1/responses`.

## The R1 finding you need to know before trusting any routed local run

Switchyard 0.2.0's Rust core re-serialises JSON with **sorted object keys**. The
body reaching llama.cpp is semantically equal to what FIS sent, but the response
schema's `properties` arrive in alphabetical order — and llama.cpp compiles a JSON
schema to a GBNF grammar that enforces property **order**. The model is therefore
forced to write, e.g., `facts` before `root_cause`, and its greedy output differs
from the direct path on the identical request. Proven with a byte tap and by
reproducing Switchyard's exact output on the direct path with only the schema keys
sorted (see `docs/routing-experiments.md`, R1). Sending a client-side GBNF string
instead restores transport equivalence but disables the model's `<think>` phase
(llama.cpp applies `response_format` grammars lazily after reasoning, raw
`grammar` from token one) — so it is *not* used for the frozen baseline.

Until either Switchyard preserves key order or FIS bumps the suite with a
canonical (sorted) schema order for every arm, **a routed local run is a different
grammar from the direct run** and must be compared, not assumed equal.
`test_schema_property_order_is_not_alphabetical__the_known_r1_difference` keeps
this on the record.
