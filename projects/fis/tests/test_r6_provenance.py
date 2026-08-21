"""R6 provenance primitives: the GGUF reader, the metadata digest recipe, and the records.

Everything here runs against synthetic files under `tmp_path`. No real model file is
read, no server is contacted, no registry is touched — the point of these tests is that
the digest recipe is *stable and sensitive*, and that can be shown on a 200-byte GGUF as
well as on a 19 GB one.

What each group is defending:

  reader     a header parser that silently mis-reads one field produces a confident,
             wrong identity — worse than no identity at all;
  digest     the recipe must change for every change that could change arithmetic
             (tensor offsets, quant type ids, tokenizer contents) and must not depend on
             when or where it was computed;
  records    a record whose digest does not match its own fields must fail closed;
  genconfig  the recorded request config is read OUT of the adapter, so this test fails
             the day someone changes the adapter's greedy defaults without saying so.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.provenance import (
    BULK_ARRAY_THRESHOLD,
    ExecutionSystem,
    GenerationConfig,
    GGUFFormatError,
    ModelArtifact,
    RuntimeIdentity,
    ServerArgs,
    build_generation_config,
    gguf_metadata_digest_payload_v1,
    gguf_metadata_digest_v1,
    gguf_summary,
    read_gguf_header,
    sha256_file,
    tensor_byte_sizes,
)

# GGUF KV type ids, restated here on purpose: a test that imports the module's own table
# cannot catch the table being wrong.
UINT32, FLOAT32, BOOL, STRING, ARRAY = 4, 6, 7, 8, 9
FMT = {4: "<I", 5: "<i", 6: "<f", 7: "<B", 10: "<Q", 11: "<q", 12: "<d"}
F32, Q4_K = 0, 12


def _gstr(text: str) -> bytes:
    raw = text.encode("utf-8")
    return struct.pack("<Q", len(raw)) + raw


def _value(type_id: int, value: Any, elem: int | None = None) -> bytes:
    if type_id == STRING:
        return _gstr(value)
    if type_id == ARRAY:
        assert elem is not None
        out = struct.pack("<I", elem) + struct.pack("<Q", len(value))
        return out + b"".join(_value(elem, v) for v in value)
    if type_id == BOOL:
        return struct.pack("<B", 1 if value else 0)
    return struct.pack(FMT[type_id], value)


def _build_gguf(path: Path, kv: list[tuple[str, int, Any, int | None]],
                tensors: list[tuple[str, list[int], int, int]], *, version: int = 3,
                alignment: int = 32, data_len: int = 96) -> Path:
    """Write a minimal but real GGUF. `tensors` carries explicit offsets so a test can
    move one by hand; `data_len` is the size of the tensor-data section."""
    body = b"GGUF" + struct.pack("<I", version)
    body += struct.pack("<Q", len(tensors)) + struct.pack("<Q", len(kv))
    for key, type_id, value, elem in kv:
        body += _gstr(key) + struct.pack("<I", type_id) + _value(type_id, value, elem)
    for name, dims, type_id, offset in tensors:
        body += _gstr(name) + struct.pack("<I", len(dims))
        body += b"".join(struct.pack("<Q", d) for d in dims)
        body += struct.pack("<I", type_id) + struct.pack("<Q", offset)
    pad = (-len(body)) % alignment
    path.write_bytes(body + b"\0" * pad + bytes(data_len))
    return path


TOKENS = [f"tok{i}" for i in range(100)]


def _kv(arch: str = "testarch", rope: float = 1000000.5,
        tokens: list[str] | None = None) -> list[tuple[str, int, Any, int | None]]:
    return [
        ("general.architecture", STRING, arch, None),
        ("general.alignment", UINT32, 32, None),
        (f"{arch}.block_count", UINT32, 2, None),
        (f"{arch}.rope.freq_base", FLOAT32, rope, None),
        ("tokenizer.ggml.tokens", ARRAY, tokens if tokens is not None else TOKENS, STRING),
        ("testarch.small_array", ARRAY, [1, 2, 3], UINT32),
        ("testarch.big_array", ARRAY, list(range(100)), UINT32),
    ]


TENSORS = [("blk.0.weight", [4, 4], F32, 0), ("blk.1.weight", [8, 8], Q4_K, 32)]


# ------------------------------------------------------------------ (a) the reader

def test_reader_round_trips_values_offsets_and_byte_deltas(tmp_path):
    path = _build_gguf(tmp_path / "m.gguf", _kv(), TENSORS, data_len=96)
    h = read_gguf_header(path)

    assert (h.version, h.n_tensors, h.n_kv) == (3, 2, 7)
    assert h.kv["general.architecture"] == "testarch"
    assert h.kv["testarch.block_count"] == 2
    assert h.kv["tokenizer.ggml.tokens"] == TOKENS
    assert h.kv["testarch.small_array"] == [1, 2, 3]
    assert h.kv["testarch.rope.freq_base"] == pytest.approx(1000000.5)
    assert h.alignment == 32
    assert h.data_offset == h.header_end + (-h.header_end % 32) and h.data_offset % 32 == 0
    assert h.file_size == h.data_offset + 96

    assert [t["name"] for t in h.tensors] == ["blk.0.weight", "blk.1.weight"]
    assert [t["type_name"] for t in h.tensors] == ["F32", "Q4_K"]
    assert [t["dims"] for t in h.tensors] == [[4, 4], [8, 8]]
    # delta to the next tensor in FILE order; the last runs to EOF
    assert tensor_byte_sizes(h) == [32, 64]

    summary = gguf_summary(h)
    assert summary["general.architecture"] == "testarch"
    assert summary["testarch.block_count"] == 2
    assert summary["vocab_size"] == 100
    assert summary["chat_template"] is False
    assert summary["tensor_type_bytes"] == {"F32": 32, "Q4_K": 64}
    assert summary["tensor_type_histogram"]["F32"] == {"count": 1, "bytes": 32}
    assert summary["total_tensor_bytes"] == 96 == h.file_size - h.data_offset


def test_reader_handles_v2_and_refuses_what_it_cannot_read(tmp_path):
    v2 = _build_gguf(tmp_path / "v2.gguf", _kv(), TENSORS, version=2)
    assert read_gguf_header(v2).version == 2

    (tmp_path / "bad.gguf").write_bytes(b"NOPE" + bytes(64))
    with pytest.raises(GGUFFormatError, match="magic"):
        read_gguf_header(tmp_path / "bad.gguf")

    v9 = _build_gguf(tmp_path / "v9.gguf", _kv(), TENSORS, version=9)
    with pytest.raises(GGUFFormatError, match="version 9"):
        read_gguf_header(v9)

    truncated = tmp_path / "short.gguf"
    truncated.write_bytes(v2.read_bytes()[:40])
    with pytest.raises(GGUFFormatError, match="ends inside the header"):
        read_gguf_header(truncated)


# ------------------------------------------------------------------ (b) the digest

def test_metadata_digest_is_stable_and_sensitive(tmp_path):
    base = _build_gguf(tmp_path / "a.gguf", _kv(), TENSORS)
    d1 = gguf_metadata_digest_v1(read_gguf_header(base))
    d2 = gguf_metadata_digest_v1(read_gguf_header(base))
    assert d1 == d2, "the digest must not depend on when it was computed"

    # a copy at another path is the same header, so the same digest — identity is content
    copied = tmp_path / "copy.gguf"
    copied.write_bytes(base.read_bytes())
    assert gguf_metadata_digest_v1(read_gguf_header(copied)) == d1

    moved = _build_gguf(tmp_path / "offset.gguf", _kv(),
                        [("blk.0.weight", [4, 4], F32, 0), ("blk.1.weight", [8, 8], Q4_K, 64)])
    assert gguf_metadata_digest_v1(read_gguf_header(moved)) != d1, "tensor offsets are in"

    requant = _build_gguf(tmp_path / "type.gguf", _kv(),
                          [("blk.0.weight", [4, 4], F32, 0), ("blk.1.weight", [8, 8], 14, 32)])
    assert gguf_metadata_digest_v1(read_gguf_header(requant)) != d1, "tensor type ids are in"

    kv_changed = _build_gguf(tmp_path / "kv.gguf", _kv(rope=500000.0), TENSORS)
    assert gguf_metadata_digest_v1(read_gguf_header(kv_changed)) != d1, "KV values are in"

    reordered = _build_gguf(tmp_path / "bulk_order.gguf",
                            _kv(tokens=TOKENS[1:] + TOKENS[:1]), TENSORS)
    assert gguf_metadata_digest_v1(read_gguf_header(reordered)) != d1, \
        "the bulk hash is order-sensitive: a permuted vocabulary is a different tokenizer"

    swapped = _build_gguf(tmp_path / "bulk_value.gguf",
                          _kv(tokens=["OTHER"] + TOKENS[1:]), TENSORS)
    assert gguf_metadata_digest_v1(read_gguf_header(swapped)) != d1


def test_bulk_arrays_are_hashed_not_embedded(tmp_path):
    header = read_gguf_header(_build_gguf(tmp_path / "m.gguf", _kv(), TENSORS))
    payload = gguf_metadata_digest_payload_v1(header)

    assert payload["recipe"] == "gguf_metadata_digest_v1"
    assert "tokenizer.ggml.tokens" not in payload["kv"], "bulk keys never sit in kv"
    assert payload["kv"]["testarch.small_array"] == [1, 2, 3], "small arrays stay inline"
    assert payload["kv"]["general.architecture"] == "testarch"

    tokens = payload["bulk"]["tokenizer.ggml.tokens"]
    stream = b"".join(struct.pack("<Q", len(t.encode())) + t.encode() for t in TOKENS)
    assert tokens == {"count": 100, "kind": "string",
                      "sha256": hashlib.sha256(stream).hexdigest()}

    # an oversized array that is not one of the four canonical bulk keys goes to bulk too,
    # and says so
    big = payload["bulk"]["testarch.big_array"]
    assert big["count"] == 100 and big["kind"] == "int"
    assert str(BULK_ARRAY_THRESHOLD) in big["note"]
    assert big["sha256"] == hashlib.sha256(
        b"".join(struct.pack("<q", i) for i in range(100))).hexdigest()

    assert payload["tensors"] == [["blk.0.weight", [4, 4], F32, 0],
                                  ["blk.1.weight", [8, 8], Q4_K, 32]]
    assert payload["data_offset"] == header.data_offset
    assert payload["file_size"] == header.file_size
    # the digest is exactly sha256 of this payload, serialized the documented way
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert gguf_metadata_digest_v1(header) == hashlib.sha256(text.encode()).hexdigest()


# ------------------------------------------------------------------ (c) records

def _artifact(**over) -> ModelArtifact:
    fields: dict[str, Any] = {
        "slug": "qwen35-9b-q4km", "role": "modern_small", "family": "qwen35.9b",
        "base_model_repo": "Qwen/Qwen3.5-9B",
        "quantizer_or_derivative_repo": "unsloth/Qwen3.5-9B-GGUF",
        "source_revision": "99a1b218", "source_url": "https://example/x.gguf",
        "filename": "x.gguf", "quantization": "Q4_K_M",
        "quantization_measured": {"Q4_K": 64, "F32": 32}, "size_bytes": 96,
        "sha256": "a" * 64, "gguf_metadata_digest": "b" * 64,
        "gguf_summary": {"n_tensors": 2}, "license": "apache-2.0", "license_source": "gguf",
        "architecture": "qwen35", "base_model_lineage": "Qwen3.5-9B",
        "local_path": "/models/x.gguf",
    }
    fields.update(over)
    return ModelArtifact(**fields)


def _runtime(**over) -> RuntimeIdentity:
    fields: dict[str, Any] = {
        "engine": "llama.cpp-upstream", "git_rev": "9b05354ec6fb58b4e665e9a39ebc40285c015638",
        "binaries": {"llama-server": "c" * 64, "libggml-cuda.so": "d" * 64},
        "build_info_expected": "b1-9b05354",
    }
    fields.update(over)
    return RuntimeIdentity(**fields)


def _genconfig(**over) -> GenerationConfig:
    fields: dict[str, Any] = {
        "prompt_ref": "cause_action_directed", "prompt_sha256": "e" * 64,
        "prompt_version": "1", "workflow_version": "1.0.0", "max_tokens": 4096,
        "response_format": {"type": "json_schema", "json_schema": {"name": "fis_output"}},
    }
    fields.update(over)
    return GenerationConfig(**fields)


def _server_args() -> ServerArgs:
    return ServerArgs(argv=["/opt/bin/llama-server", "--host", "127.0.0.1", "--port", "8082",
                            "-m", "/models/x.gguf", "-c", "16384", "-ngl", "99",
                            "--flash-attn", "on", "--jinja", "--parallel", "1",
                            "--alias", "fis-local", "--log-file", "/tmp/s.log"])


def _execution_system(**over) -> ExecutionSystem:
    server = _server_args()
    fields: dict[str, Any] = {
        "artifact_id": _artifact().artifact_id, "artifact_sha256": "a" * 64,
        "gguf_metadata_digest": "b" * 64, "runtime_id": _runtime().runtime_id,
        "runtime_digest": _runtime().record_digest,
        "server_args_digest": server.server_args_digest,
        "server_args_material": server.material, "genconfig_id": _genconfig().genconfig_id,
        "generation_config_digest": _genconfig().record_digest, "ctx": 16384,
    }
    fields.update(over)
    return ExecutionSystem(**fields)


def test_ids_are_derived_from_the_bytes_they_name():
    assert _artifact().artifact_id == "qwen35-9b-q4km@" + "a" * 12
    runtime = _runtime()
    assert runtime.runtime_id == f"llama.cpp-upstream-9b05354@{runtime.binary_set_digest[:12]}"
    assert runtime.runtime_digest == runtime.record_digest
    assert _genconfig().genconfig_id.startswith("gc@")
    # a hand-supplied id that disagrees with the content is a lie, and is refused
    with pytest.raises(ValueError, match="artifact_id"):
        _artifact(artifact_id="something-else@000000000000")


@pytest.mark.parametrize("make, field, value", [
    (_artifact, "size_bytes", 97),
    (_artifact, "license", "proprietary"),
    (_runtime, "build_info_expected", "b1-deadbee"),
    (_genconfig, "max_tokens", 2048),
    (_server_args, "material", ["-c", "8192"]),
    (_execution_system, "ctx", 8192),
])
def test_every_record_detects_tampering(make, field, value):
    record = make()
    record.verify()
    setattr(record, field, value)
    with pytest.raises(ValueError, match="record_digest"):
        record.verify()


def test_a_record_loaded_from_json_keeps_the_digest_it_was_written_with():
    original = _artifact()
    payload = json.loads(json.dumps(original.model_dump(mode="json")))
    assert ModelArtifact(**payload).verify() is not None
    payload["notes"] = "quietly edited"
    with pytest.raises(ValueError, match="record_digest"):
        ModelArtifact(**payload).verify()


# ------------------------------------------------------------------ (d) server args

def test_material_args_drop_the_informational_flags_and_keep_order():
    server = _server_args()
    assert server.material == ["-c", "16384", "-ngl", "99", "--flash-attn", "on",
                               "--jinja", "--parallel", "1"]
    assert server.ctx == 16384
    # the same computation on another port/alias/model path is the same execution system
    other = ServerArgs(argv=["/elsewhere/llama-server", "--port", "9099", "--alias", "other",
                             "--model", "/models/x.gguf", "-c", "16384", "-ngl", "99",
                             "--flash-attn", "on", "--jinja", "--parallel", "1"])
    assert other.server_args_digest == server.server_args_digest
    # …but a different context length is NOT
    shorter = ServerArgs(argv=["/opt/bin/llama-server", "-c", "8192"])
    assert shorter.server_args_digest != server.server_args_digest


# ------------------------------------------------------------------ (e) generation config

def test_generation_config_is_read_out_of_the_adapter_not_restated():
    """If this fails, the recorded request config has drifted from the body the runner
    actually sends — which is exactly the silent confound the record exists to prevent."""
    from fis_platform.model_gateway.base import GenerationRequest, Message
    from fis_platform.model_gateway.local import LocalLlamaCppAdapter
    from fis_platform.model_gateway.schema_compat import to_gbnf_safe
    from schemas.common import ModelTier, Provider
    from schemas.investigator import InvestigationResult
    from schemas.model_manifest import ModelManifest
    from services.ai_orchestrator.investigate import PROMPT_VERSION, WORKFLOW_VERSION
    from services.ai_orchestrator.prompts import PROMPTS

    config = build_generation_config("cause_action_directed", 4096)

    assert config.response_format == {
        "type": "json_schema",
        "json_schema": {"name": "fis_output",
                        "schema": to_gbnf_safe(InvestigationResult.model_json_schema()),
                        "strict": True},
    }
    manifest = ModelManifest(ref="probe", tier=ModelTier.SPECIALIST,
                             provider=Provider.LOCAL_LLAMACPP, model_id="probe",
                             context_window=16384, max_output_tokens=4096,
                             base_url="http://127.0.0.1:0/v1")
    body = LocalLlamaCppAdapter(manifest).build_body(GenerationRequest(
        model_ref="probe", messages=[Message(role="user", content="probe")],
        system=PROMPTS["cause_action_directed"],
        json_schema=InvestigationResult.model_json_schema(), max_tokens=4096))
    assert (config.temperature, config.seed) == (body["temperature"], body["seed"])
    assert config.response_format == body["response_format"]
    assert (config.prompt_version, config.workflow_version) == (PROMPT_VERSION, WORKFLOW_VERSION)
    assert config.prompt_sha256 == hashlib.sha256(
        PROMPTS["cause_action_directed"].encode()).hexdigest()
    assert config.evidence_mode == "fixed_evidence"

    rebuilt = GenerationConfig(
        prompt_ref="cause_action_directed", prompt_sha256=config.prompt_sha256,
        prompt_version=PROMPT_VERSION, workflow_version=WORKFLOW_VERSION,
        temperature=body["temperature"], seed=body["seed"], max_tokens=body["max_tokens"],
        response_format=body["response_format"])
    assert rebuilt.record_digest == config.record_digest
    assert rebuilt.genconfig_id == config.genconfig_id
    # the id is a function of the config, so two identical configs collide by design
    assert build_generation_config("cause_action_directed", 4096).record_digest == \
        config.record_digest
    assert build_generation_config("baseline", 4096).record_digest != config.record_digest
    with pytest.raises(ValueError, match="unknown prompt"):
        build_generation_config("no_such_prompt", 4096)


# ------------------------------------------------------------------ (f) sha256_file

def test_sha256_file_matches_hashlib_and_reports_progress(tmp_path):
    blob = b"northstar" * 1000
    path = tmp_path / "blob.bin"
    path.write_bytes(blob)
    assert sha256_file(path) == hashlib.sha256(blob).hexdigest()
    assert sha256_file(path, chunk=7) == hashlib.sha256(blob).hexdigest()
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    assert sha256_file(empty) == hashlib.sha256(b"").hexdigest()
