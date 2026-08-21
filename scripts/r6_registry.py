#!/usr/bin/env python3
"""R6 registry CLI — register the things a number was measured on, and move state.

Every write goes to `R6Registry(default_root())`. There is deliberately no `--root` and
no environment variable: a registry you can point somewhere else is a reset button, and
the whole point of this tree is that "we already looked at TEST" is not a thing anyone
can un-say. Tests construct `R6Registry(tmp_path)` and call the `cmd_*` functions
directly with it.

Read-only subcommands (`show`, `verify`, `capture-server-args`, `build-execution-system`)
never write. `build-execution-system` prints a record for a human to paste into a
transition payload rather than writing one, because binding an execution system to a
candidate is a state change and state changes go through `transition`.

    register-artifact          hash a GGUF, read its header, write models/<artifact_id>.json
    register-runtime           photograph the engine build -> runtimes/<runtime_id>.json
    register-genconfig         read the request config out of the adapter -> genconfigs/
    register-trained-artifact  record a self-produced weights file -> trained/<artifact_id>.json
    register-candidate         bind artifact x runtime, open the log at SMOKE
    transition                 one legal edge, with its payload guards
    unlock-test                re-hash the artifact, then spend the single TEST unlock
    capture-server-args        the running llama-server's material argv
    build-execution-system     artifact + runtime + server args + genconfig, checked against /props
    show / verify              read the chains; `verify` exits 1 if anything does not verify
    phase                      append a wall-time marker to phases.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.provenance import (
    ROLES,
    TRAIN_COMPATIBLE,
    TRANSITIONS,
    WITHDRAWN,
    ExecutionSystem,
    ModelArtifact,
    R6Registry,
    RegistryIntegrityError,
    TrainedArtifact,
    TransitionRefused,
    build_generation_config,
    capture_runtime,
    capture_server_args,
    default_root,
    gguf_metadata_digest_v1,
    gguf_summary,
    read_gguf_header,
    sha256_file,
)

# The two edges a dirty tree is tolerable on: TRAIN compatibility is a fact about the
# runtime (not about a result), and withdrawing is a retreat. Everything from
# CONTRACT_FROZEN onward produces evidence, and evidence that cannot name the exact code
# that made it is not evidence.
DIRTY_TREE_ALLOWED = (TRAIN_COMPATIBLE, WITHDRAWN)


def _progress(done: int, size: int) -> None:
    pct = 100.0 * done / size if size else 0.0
    print(f"  hashed {done / (1 << 30):.1f} / {size / (1 << 30):.1f} GiB ({pct:.0f}%)",
          file=sys.stderr, flush=True)


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def require_clean_tree_for(to: str, allow_dirty: bool) -> bool:
    """Whether `transition` must insist on a clean tree. `--allow-dirty` is honoured for
    TRAIN_COMPATIBLE and WITHDRAWN only; asking for it anywhere else is refused rather
    than ignored, so nobody discovers the flag did nothing after the fact."""
    if not allow_dirty:
        return True
    if to not in DIRTY_TREE_ALLOWED:
        raise TransitionRefused(
            f"--allow-dirty is only honoured for {list(DIRTY_TREE_ALLOWED)}, not {to} — a "
            "result recorded from an uncommitted tree cannot be reproduced")
    return False


# ------------------------------------------------------------------ registration

def cmd_register_artifact(args: argparse.Namespace, reg: R6Registry) -> int:
    path = Path(args.path).resolve()
    size = path.stat().st_size
    if size != args.expected_size:
        raise TransitionRefused(
            f"{path} is {size} bytes; the plan expects {args.expected_size} — refusing "
            f"(difference {size - args.expected_size:+d})")
    print(f"hashing {path} ({size / (1 << 30):.1f} GiB)…", file=sys.stderr, flush=True)
    sha = sha256_file(path, progress=_progress)
    if sha != args.expected_sha256:
        raise TransitionRefused(
            f"{path} hashes to {sha}; the plan expects {args.expected_sha256} — refusing")
    header = read_gguf_header(path)
    summary = gguf_summary(header)
    record = ModelArtifact(
        slug=args.slug, role=args.role, family=args.family,
        base_model_repo=args.base_model_repo,
        quantizer_or_derivative_repo=args.quantizer_repo,
        source_revision=args.source_revision, source_url=args.source_url,
        filename=path.name, quantization=args.quantization,
        quantization_measured=summary["tensor_type_bytes"],
        size_bytes=size, sha256=sha,
        gguf_metadata_digest=gguf_metadata_digest_v1(header), gguf_summary=summary,
        license=args.license, license_source=args.license_source,
        architecture=str(header.kv.get("general.architecture") or ""),
        base_model_lineage=args.base_model_lineage, local_path=str(path), notes=args.notes,
    )
    reg.put_artifact(record)
    _emit(record.model_dump(mode="json"))
    return 0


def cmd_register_runtime(args: argparse.Namespace, reg: R6Registry) -> int:
    record = capture_runtime(args.engine, Path(args.llama_dir), Path(args.bin_dir),
                             Path(args.cuda_lib_dir), args.build_info_expected,
                             notes=args.notes)
    reg.put_runtime(record)
    _emit(record.model_dump(mode="json"))
    return 0


def cmd_register_genconfig(args: argparse.Namespace, reg: R6Registry) -> int:
    record = build_generation_config(args.prompt, args.max_tokens)
    reg.put_genconfig(record)
    _emit(record.model_dump(mode="json"))
    return 0


def cmd_register_trained_artifact(args: argparse.Namespace, reg: R6Registry) -> int:
    """Record a self-produced (trained) weights file. Schema/provenance only — no
    training happens here; the caller supplies a JSON object with the full
    `TrainedArtifact` field list (master plan §9)."""
    record = TrainedArtifact(**_load_payload(args.json))
    reg.put_trained_artifact(record)
    _emit(record.model_dump(mode="json"))
    return 0


def cmd_register_candidate(args: argparse.Namespace, reg: R6Registry) -> int:
    artifact = reg.get_artifact(args.artifact_id)
    runtime = reg.get_runtime(args.runtime_id)
    candidate_id = reg.register_candidate(args.slug, artifact, runtime, args.family, args.role)
    _emit(reg.read_identity(candidate_id))
    return 0


# ------------------------------------------------------------------ state

def _load_payload(source: str) -> dict[str, Any]:
    text = sys.stdin.read() if source == "-" else Path(source).read_text()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise TransitionRefused("the payload must be a JSON object")
    return payload


def cmd_transition(args: argparse.Namespace, reg: R6Registry) -> int:
    payload = _load_payload(args.payload_json)
    entry = reg.transition(args.candidate, args.to, payload,
                           require_clean_tree=require_clean_tree_for(args.to, args.allow_dirty))
    _emit(entry)
    return 0


def cmd_unlock_test(args: argparse.Namespace, reg: R6Registry) -> int:
    """Spend the one TEST look. The artifact is re-hashed HERE, not trusted from the
    record: between registration and the unlock the file has had weeks to be replaced by
    a re-upload with the same name (which has already happened upstream once)."""
    identity = reg.read_identity(args.candidate)
    artifact = reg.get_artifact(identity["artifact_id"])
    path = Path(artifact.local_path)
    print(f"re-hashing {path} before the unlock…", file=sys.stderr, flush=True)
    sha_now = sha256_file(path, progress=_progress)
    entry = reg.transition(args.candidate, "TEST_UNLOCKED", {
        "test_run_id": args.test_run_id,
        "dev_result_digest": args.dev_result_digest,
        "contract_revision": args.contract_revision,
        "execution_system_digest": args.execution_system_digest,
        "artifact_sha256_now": sha_now,
    })
    _emit(entry)
    return 0


def cmd_phase(args: argparse.Namespace, reg: R6Registry) -> int:
    _emit(reg.record_phase(args.name, args.event, args.note))
    return 0


# ------------------------------------------------------------------ read-only

def cmd_capture_server_args(args: argparse.Namespace, reg: R6Registry) -> int:
    server = capture_server_args(args.port)
    if server is None:
        raise TransitionRefused(f"no llama-server process is serving --port {args.port}")
    _emit(server.model_dump(mode="json"))
    return 0


def cmd_build_execution_system(args: argparse.Namespace, reg: R6Registry) -> int:
    identity = reg.read_identity(args.candidate)
    artifact = reg.get_artifact(identity["artifact_id"])
    runtime = reg.get_runtime(identity["runtime_id"])
    genconfig = reg.get_genconfig(args.genconfig_id)
    server = capture_server_args(args.port)
    if server is None:
        raise TransitionRefused(f"no llama-server process is serving --port {args.port}")
    ctx = server.ctx
    if ctx is None:
        raise TransitionRefused(
            f"the server on :{args.port} names no -c/--ctx-size; context length decides what "
            "fits in a prompt and must be part of the execution system")

    with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/props", timeout=5) as resp:
        props = json.load(resp)
    build_info = str(props.get("build_info", ""))
    if runtime.build_info_expected and build_info != runtime.build_info_expected:
        raise TransitionRefused(
            f"the server on :{args.port} reports build_info {build_info!r} but the runtime "
            f"record expects {runtime.build_info_expected!r} — that is a different engine")
    served = Path(str(props.get("model_path", ""))).name
    if served != artifact.filename:
        raise TransitionRefused(
            f"the server on :{args.port} is serving {served!r}, the candidate's artifact is "
            f"{artifact.filename!r}")

    system = ExecutionSystem(
        artifact_id=artifact.artifact_id, artifact_sha256=artifact.sha256,
        gguf_metadata_digest=artifact.gguf_metadata_digest,
        runtime_id=runtime.runtime_id, runtime_digest=runtime.record_digest,
        server_args_digest=server.server_args_digest, server_args_material=server.material,
        genconfig_id=genconfig.genconfig_id,
        generation_config_digest=genconfig.record_digest, ctx=ctx,
    )
    _emit(system.model_dump(mode="json"))
    return 0


def cmd_show(args: argparse.Namespace, reg: R6Registry) -> int:
    if getattr(args, "trained", None):
        record = reg.get_trained_artifact(args.trained)
        _emit(record.model_dump(mode="json"))
        return 0
    ids = [args.candidate] if args.candidate else reg.candidate_ids()
    if not ids:
        print(f"no candidates under {reg.candidates_dir}")
        return 0
    for cid in ids:
        identity = reg.read_identity(cid)
        entries = reg.read_state(cid)
        print(f"\n{cid}  family={identity['family']}  role={identity['role']}")
        print(f"  artifact {identity['artifact_id']}  runtime {identity['runtime_id']}")
        print(f"  state    {entries[-1]['to']}  ({len(entries)} log entries)")
        for e in entries:
            label = e["to"] if e["kind"] == "transition" else f"run {e['payload'].get('run_id')}"
            print(f"    {e['seq']:>3} {e['kind']:<10} {e['from']!s:<16} -> {label:<24} "
                  f"{e['at']}  {e['code_commit']}{'' if e['tree_clean'] else ' DIRTY'}")
    return 0


def cmd_verify(args: argparse.Namespace, reg: R6Registry) -> int:
    """Re-derive every digest in the tree. Exit 1 on the first thing that does not."""
    problems: list[str] = []
    for directory, loader in ((reg.models_dir, reg.get_artifact),
                              (reg.runtimes_dir, reg.get_runtime),
                              (reg.genconfigs_dir, reg.get_genconfig)):
        for path in sorted(directory.glob("*.json")) if directory.exists() else []:
            try:
                loader(path.stem)
            except (ValueError, SystemExit) as exc:
                problems.append(f"{path}: {exc}")
    head = json.loads(reg.head_file.read_text()) if reg.head_file.exists() else {}
    known = set(reg.candidate_ids())
    for cid in sorted(set(head) - known):
        problems.append(f"HEAD.json names {cid!r}, which has no identity.json")
    for cid in sorted(known):
        try:
            entries = reg.read_state(cid)
            reg.read_identity(cid)
            print(f"{cid}: {entries[-1]['to']} ({len(entries)} entries) OK")
        except (ValueError, SystemExit) as exc:
            problems.append(f"{cid}: {exc}")
    for line in problems:
        print(f"PROBLEM {line}", file=sys.stderr)
    print(f"\n{len(known)} candidates, {len(problems)} problems")
    return 1 if problems else 0


# ------------------------------------------------------------------ argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("register-artifact", help="hash + header-read a GGUF and record it")
    p.add_argument("--slug", required=True)
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--family", required=True, help="quant-family key for the <=1-quant guard")
    p.add_argument("--path", required=True)
    p.add_argument("--base-model-repo", required=True)
    p.add_argument("--quantizer-repo", required=True)
    p.add_argument("--source-revision", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--license", required=True)
    p.add_argument("--license-source", required=True, choices=("gguf", "model_card", "plan"))
    p.add_argument("--base-model-lineage", required=True)
    p.add_argument("--quantization", required=True)
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--expected-size", required=True, type=int)
    p.add_argument("--notes")
    p.set_defaults(func=cmd_register_artifact)

    p = sub.add_parser("register-runtime", help="photograph the engine build")
    p.add_argument("--engine", required=True,
                   choices=("llama.cpp-upstream", "llama.cpp-prism"))
    p.add_argument("--llama-dir", required=True)
    p.add_argument("--bin-dir", required=True)
    p.add_argument("--cuda-lib-dir", required=True)
    p.add_argument("--build-info-expected")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_register_runtime)

    p = sub.add_parser("register-genconfig", help="read the request config out of the adapter")
    p.add_argument("--prompt", required=True)
    p.add_argument("--max-tokens", required=True, type=int)
    p.set_defaults(func=cmd_register_genconfig)

    p = sub.add_parser("register-trained-artifact",
                       help="record a self-produced (trained) weights file")
    p.add_argument("--json", required=True, help="path to a JSON object, or - for stdin")
    p.set_defaults(func=cmd_register_trained_artifact)

    p = sub.add_parser("register-candidate", help="bind artifact x runtime (re-hashes the file)")
    p.add_argument("--slug", required=True)
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--runtime-id", required=True)
    p.add_argument("--family", required=True)
    p.add_argument("--role", required=True, choices=ROLES)
    p.set_defaults(func=cmd_register_candidate)

    p = sub.add_parser("transition", help="move a candidate one legal edge")
    p.add_argument("--candidate", required=True)
    p.add_argument("--to", required=True, choices=sorted(TRANSITIONS))
    p.add_argument("--payload-json", required=True, help="path to a JSON object, or - for stdin")
    p.add_argument("--allow-dirty", action="store_true",
                   help=f"only honoured for {list(DIRTY_TREE_ALLOWED)}")
    p.set_defaults(func=cmd_transition)

    p = sub.add_parser("unlock-test", help="spend the single TEST look")
    p.add_argument("--candidate", required=True)
    p.add_argument("--test-run-id", required=True)
    p.add_argument("--contract-revision", required=True)
    p.add_argument("--dev-result-digest", required=True)
    p.add_argument("--execution-system-digest", required=True)
    p.set_defaults(func=cmd_unlock_test)

    p = sub.add_parser("capture-server-args", help="the running server's material argv")
    p.add_argument("--port", required=True, type=int)
    p.set_defaults(func=cmd_capture_server_args)

    p = sub.add_parser("build-execution-system", help="print (do not write) an ExecutionSystem")
    p.add_argument("--candidate", required=True)
    p.add_argument("--port", required=True, type=int)
    p.add_argument("--genconfig-id", required=True)
    p.set_defaults(func=cmd_build_execution_system)

    p = sub.add_parser("show", help="states and chains")
    p.add_argument("--candidate")
    p.add_argument("--trained", help="show one TrainedArtifact record by artifact_id instead")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("verify", help="re-derive every digest; exit 1 on any problem")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("phase", help="append a wall-time marker")
    p.add_argument("--name", required=True)
    p.add_argument("--event", required=True, choices=("start", "end"))
    p.add_argument("--note")
    p.set_defaults(func=cmd_phase)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = R6Registry(default_root())
    try:
        return int(args.func(args, registry))
    except RegistryIntegrityError as exc:
        print(f"INTEGRITY: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
