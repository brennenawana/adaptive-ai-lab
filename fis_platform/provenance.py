"""R6 provenance: what a number was measured ON, and the state machine that keeps it honest.

R5 proved the discipline works for *policies* (one frozen artifact per model, one TEST
look, an append-only unlock record). R6 measures *models*, and the thing that can drift
is no longer a JSON artifact we wrote ourselves — it is a 19 GB weights file, a CUDA
build, a set of server flags and a request body. Every one of those has already been
observed to move underneath a comparison:

  * two GGUF files can carry byte-identical tokenizer metadata and different block
    geometry (the upstream-vs-Prism Q2_0 QK 64/128 divergence), so "same quant label"
    is not "same arithmetic";
  * the same 48 dev cases moved 23 scored outcomes across a llama.cpp server restart,
    so the serving session is part of the measurement;
  * `general.name` on a shipped Qwen3-8B says "AWQ-compatible Instruct" for a plain
    K-quant, so descriptive KV is not identity — bytes are.

So identity here is always a digest over bytes or over an explicit, written-down field
list, never a label. Three digests carry the weight:

  `sha256`                      the artifact's bytes (canonical model identity)
  `gguf_metadata_digest_v1`     the header, including per-tensor type AND offset, which
                                is what makes block geometry visible
  `runtime_digest`             the binaries, CUDA libs, build flags and driver

`ExecutionSystem` binds artifact + runtime + server flags + request config into one
digest; a run that cannot name that digest is not comparable to one that can.

The state machine (§ `TRANSITIONS`) is the R5 lesson generalised: a candidate walks
REGISTERED → TRAIN_COMPATIBLE → CONTRACT_FROZEN → DEV_EVALUATED → DEV_{QUALIFIED,
REJECTED} → TEST_UNLOCKED → TEST_EVALUATED and nowhere else. There is no reset path,
no environment variable that relocates the registry, and the log is append-only and
hash-chained, so "we accidentally looked at TEST twice" is a state a command cannot
reach rather than a promise a human keeps.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fis_platform.routing.learn import digest
from fis_platform.suite import git_head

__all__ = [
    "DIAGNOSTIC_STATES",
    "RUN_KINDS",
    "STATES",
    "TERMINAL_STATES",
    "TRANSITIONS",
    "ExecutionSystem",
    "GGUFFormatError",
    "GGUFHeader",
    "GenerationConfig",
    "IllegalTransition",
    "ModelArtifact",
    "R6Registry",
    "RegistryIntegrityError",
    "RuntimeIdentity",
    "ServerArgs",
    "TransitionRefused",
    "begin_run",
    "build_generation_config",
    "capture_runtime",
    "capture_server_args",
    "default_root",
    "end_run",
    "gguf_metadata_digest_payload_v1",
    "gguf_metadata_digest_v1",
    "gguf_summary",
    "read_gguf_header",
    "require_state",
    "sha256_file",
]

_ROOT = Path(__file__).resolve().parents[1]


def _now() -> str:
    """UTC, seconds resolution — the precision every other R-series record uses."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_file(path: Path | str, chunk: int = 1 << 24, progress: Any = None) -> str:
    """Streaming sha256 of a file. 16 MiB chunks so a 19 GB artifact never lands in RAM.

    `progress(bytes_done, size)` is called about once per GiB when given — hashing a
    19 GB file takes minutes and a silent command reads as a hang.
    """
    p = Path(path)
    size = p.stat().st_size
    h = hashlib.sha256()
    done = 0
    next_tick = 1 << 30
    with p.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
            done += len(block)
            if progress is not None and done >= next_tick:
                progress(done, size)
                next_tick += 1 << 30
    return h.hexdigest()


# --------------------------------------------------------------------------- GGUF

class GGUFFormatError(ValueError):
    """The file is not a GGUF v2/v3 header we can read. Never guessed around."""


# GGUF KV type ids (v2/v3).
_T_UINT8, _T_INT8, _T_UINT16, _T_INT16 = 0, 1, 2, 3
_T_UINT32, _T_INT32, _T_FLOAT32, _T_BOOL = 4, 5, 6, 7
_T_STRING, _T_ARRAY, _T_UINT64, _T_INT64, _T_FLOAT64 = 8, 9, 10, 11, 12

_SCALAR_FMT = {
    _T_UINT8: "<B", _T_INT8: "<b", _T_UINT16: "<H", _T_INT16: "<h",
    _T_UINT32: "<I", _T_INT32: "<i", _T_FLOAT32: "<f", _T_BOOL: "<B",
    _T_UINT64: "<Q", _T_INT64: "<q", _T_FLOAT64: "<d",
}

# Element kind per KV type — decides how a bulk array is length-prefix hashed.
_KIND = {
    _T_UINT8: "int", _T_INT8: "int", _T_UINT16: "int", _T_INT16: "int",
    _T_UINT32: "int", _T_INT32: "int", _T_UINT64: "int", _T_INT64: "int",
    _T_FLOAT32: "float", _T_FLOAT64: "float", _T_BOOL: "bool", _T_STRING: "string",
}

# ggml tensor type ids. Ids not listed render as `unknown_<id>` rather than being
# silently dropped: an unrecognised quant is exactly the thing worth seeing.
GGML_TYPE_NAMES: dict[int, str] = {
    0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 6: "Q5_0", 7: "Q5_1", 8: "Q8_0", 9: "Q8_1",
    10: "Q2_K", 11: "Q3_K", 12: "Q4_K", 13: "Q5_K", 14: "Q6_K", 15: "Q8_K",
    16: "IQ2_XXS", 17: "IQ2_XS", 18: "IQ3_XXS", 19: "IQ1_S", 20: "IQ4_NL", 21: "IQ3_S",
    22: "IQ2_S", 23: "IQ4_XS", 24: "I8", 25: "I16", 26: "I32", 27: "I64", 28: "F64",
    29: "IQ1_M", 30: "BF16", 34: "TQ1_0", 35: "TQ2_0", 39: "MXFP4", 41: "Q1_0", 42: "Q2_0",
}

DEFAULT_ALIGNMENT = 32

# Sanity caps. A corrupt length field must fail loudly instead of asking for 2^60 bytes.
_MAX_STRING = 1 << 30
_MAX_ARRAY = 1 << 28
_MAX_TENSORS = 1 << 22
_MAX_KV = 1 << 20
_MAX_DIMS = 8


def type_name(type_id: int) -> str:
    return GGML_TYPE_NAMES.get(type_id, f"unknown_{type_id}")


@dataclass
class GGUFHeader:
    """The header of a GGUF file. Tensor DATA is never read — only the metadata block
    and the tensor directory, which is a few MB even for a 19 GB artifact.

    `kv` preserves file order (dict insertion order), because the metadata digest and
    the bulk-array hashes are order-sensitive by design.
    """

    path: str
    version: int
    n_tensors: int
    n_kv: int
    kv: dict[str, Any]
    # key -> (kv type id, array element type id or None). Kept so a bulk array's element
    # kind comes from the file's declared type rather than from guessing at Python types.
    kv_types: dict[str, tuple[int, int | None]] = field(default_factory=dict)
    tensors: list[dict[str, Any]] = field(default_factory=list)
    alignment: int = DEFAULT_ALIGNMENT
    header_end: int = 0
    data_offset: int = 0
    file_size: int = 0


class _Cursor:
    """Buffered forward-only reader over the head of a file.

    Reading 150k tokenizer strings with one `read()` syscall each is minutes of
    overhead on a cold cache; one 4 MiB refill is milliseconds.
    """

    def __init__(self, fh: Any, chunk: int = 1 << 22) -> None:
        self._fh = fh
        self._chunk = chunk
        self._buf = b""
        self._off = 0
        self.pos = 0

    def read(self, n: int) -> bytes:
        if n < 0:
            raise GGUFFormatError(f"negative read of {n} bytes")
        while len(self._buf) - self._off < n:
            want = max(self._chunk, n - (len(self._buf) - self._off))
            more = self._fh.read(want)
            if not more:
                raise GGUFFormatError(
                    f"file ends inside the header (wanted {n} bytes at offset {self.pos})"
                )
            if self._off:
                self._buf = self._buf[self._off:]
                self._off = 0
            self._buf += more
        out = self._buf[self._off:self._off + n]
        self._off += n
        self.pos += n
        if self._off >= (1 << 21):
            self._buf = self._buf[self._off:]
            self._off = 0
        return out

    def scalar(self, type_id: int) -> Any:
        fmt = _SCALAR_FMT.get(type_id)
        if fmt is None:
            raise GGUFFormatError(f"unsupported KV type id {type_id}")
        raw = self.read(struct.calcsize(fmt))
        val = struct.unpack(fmt, raw)[0]
        return bool(val) if type_id == _T_BOOL else val

    def u32(self) -> int:
        return struct.unpack("<I", self.read(4))[0]

    def u64(self) -> int:
        return struct.unpack("<Q", self.read(8))[0]

    def string(self) -> str:
        n = self.u64()
        if n > _MAX_STRING:
            raise GGUFFormatError(f"implausible string length {n} at offset {self.pos - 8}")
        # errors='replace': a mangled byte in one tokenizer entry must not stop a run
        # from being identified. The bulk hash is over the raw bytes, so identity is
        # unaffected by the replacement.
        return self.read(n).decode("utf-8", errors="replace")


def _read_value(cur: _Cursor, type_id: int) -> tuple[Any, int | None]:
    """One KV value. Returns (value, array element type id or None)."""
    if type_id == _T_STRING:
        return cur.string(), None
    if type_id == _T_ARRAY:
        elem = cur.u32()
        count = cur.u64()
        if elem == _T_ARRAY:
            raise GGUFFormatError("nested arrays are not supported by this reader")
        if count > _MAX_ARRAY:
            raise GGUFFormatError(f"implausible array length {count}")
        if elem == _T_STRING:
            return [cur.string() for _ in range(count)], elem
        if elem not in _SCALAR_FMT:
            raise GGUFFormatError(f"unsupported array element type id {elem}")
        return [cur.scalar(elem) for _ in range(count)], elem
    return cur.scalar(type_id), None


def _align_up(value: int, alignment: int) -> int:
    if alignment <= 0:
        raise GGUFFormatError(f"general.alignment must be positive, got {alignment}")
    return value + (-value % alignment)


def read_gguf_header(path: Path | str) -> GGUFHeader:
    """Parse a GGUF v2/v3 header. Pure stdlib — no numpy, no gguf-py.

    Only the metadata block and the tensor directory are read, so this is a few MB of
    I/O on any artifact size. The dependency-free path matters because the digest this
    feeds is committed evidence: it has to be re-derivable years later without a
    matching `gguf` package release.
    """
    p = Path(path)
    size = p.stat().st_size
    with p.open("rb") as fh:
        cur = _Cursor(fh)
        magic = cur.read(4)
        if magic != b"GGUF":
            raise GGUFFormatError(f"{p}: magic is {magic!r}, not b'GGUF'")
        version = cur.u32()
        if version not in (2, 3):
            raise GGUFFormatError(f"{p}: GGUF version {version} — this reader handles v2/v3")
        n_tensors = cur.u64()
        n_kv = cur.u64()
        if n_tensors > _MAX_TENSORS or n_kv > _MAX_KV:
            raise GGUFFormatError(f"{p}: implausible counts n_tensors={n_tensors} n_kv={n_kv}")

        kv: dict[str, Any] = {}
        kv_types: dict[str, tuple[int, int | None]] = {}
        for _ in range(n_kv):
            key = cur.string()
            type_id = cur.u32()
            value, elem = _read_value(cur, type_id)
            kv[key] = value
            kv_types[key] = (type_id, elem)

        tensors: list[dict[str, Any]] = []
        for _ in range(n_tensors):
            name = cur.string()
            n_dims = cur.u32()
            if n_dims > _MAX_DIMS:
                raise GGUFFormatError(f"{p}: tensor {name!r} claims {n_dims} dimensions")
            dims = [cur.u64() for _ in range(n_dims)]
            t_id = cur.u32()
            offset = cur.u64()
            tensors.append({"name": name, "dims": dims, "type_id": t_id,
                            "type_name": type_name(t_id), "offset": offset})

        header_end = cur.pos

    alignment = kv.get("general.alignment", DEFAULT_ALIGNMENT)
    if not isinstance(alignment, int) or isinstance(alignment, bool):
        raise GGUFFormatError(f"{p}: general.alignment is {alignment!r}, not an integer")
    return GGUFHeader(
        path=str(p), version=version, n_tensors=n_tensors, n_kv=n_kv, kv=kv,
        kv_types=kv_types, tensors=tensors, alignment=alignment, header_end=header_end,
        data_offset=_align_up(header_end, alignment), file_size=size,
    )


def tensor_byte_sizes(header: GGUFHeader) -> list[int]:
    """Bytes each tensor occupies, as the delta to the next tensor's offset in FILE
    order (the last one runs to EOF). This measures what the file actually spends,
    padding included — which is the number that differs when two builds disagree about
    block geometry, and it needs no per-quant block-size table to compute."""
    offsets = [t["offset"] for t in header.tensors]
    end = header.file_size - header.data_offset
    return [(offsets[i + 1] if i + 1 < len(offsets) else end) - o for i, o in enumerate(offsets)]


_SUMMARY_KV = (
    "general.architecture", "general.name", "general.basename", "general.size_label",
    "general.finetune", "general.file_type", "general.quantization_version",
    "general.license", "general.license.name", "general.base_model.0.repo_url",
    "general.base_model.0.name", "general.base_model.0.organization",
    "general.quantized_by", "general.repo_url",
)


def gguf_summary(header: GGUFHeader) -> dict[str, Any]:
    """Human-readable header facts + the measured quant histogram.

    Informational by contract: `general.name` has already been caught lying about a
    quant (a plain K-quant shipped labelled "AWQ-compatible"), so nothing here is
    identity. `tensor_type_bytes` is the exception worth reading — it is measured from
    offsets, so it says what the file IS rather than what the filename claims.
    """
    kv = header.kv
    out: dict[str, Any] = {k: kv.get(k) for k in _SUMMARY_KV}
    arch = kv.get("general.architecture")
    if isinstance(arch, str):
        for suffix in ("block_count", "context_length", "embedding_length"):
            out[f"{arch}.{suffix}"] = kv.get(f"{arch}.{suffix}")
    tokens = kv.get("tokenizer.ggml.tokens")
    out["vocab_size"] = len(tokens) if isinstance(tokens, list) else None
    out["chat_template"] = "tokenizer.chat_template" in kv
    out["gguf_version"] = header.version
    out["alignment"] = header.alignment
    out["n_tensors"] = header.n_tensors
    out["n_kv"] = header.n_kv
    out["data_offset"] = header.data_offset
    out["file_size"] = header.file_size

    hist: dict[str, dict[str, int]] = {}
    for t, nbytes in zip(header.tensors, tensor_byte_sizes(header)):
        e = hist.setdefault(t["type_name"], {"count": 0, "bytes": 0})
        e["count"] += 1
        e["bytes"] += nbytes
    out["tensor_type_histogram"] = hist
    out["tensor_type_bytes"] = {k: v["bytes"] for k, v in hist.items()}
    out["total_tensor_bytes"] = sum(v["bytes"] for v in hist.values())
    return out


# The four arrays every tokenizer ships. They are megabytes long, so they are hashed
# rather than embedded — and they are hashed rather than dropped because a swapped
# tokenizer is a different model.
BULK_KV_KEYS = frozenset({
    "tokenizer.ggml.tokens", "tokenizer.ggml.scores",
    "tokenizer.ggml.token_type", "tokenizer.ggml.merges",
})
BULK_ARRAY_THRESHOLD = 64


def _bulk_stream(values: list[Any], kind: str) -> bytes:
    """Length-prefixed byte stream over an array, order preserved (see the recipe)."""
    parts: list[bytes] = []
    for v in values:
        if kind == "string":
            b = v.encode("utf-8") if isinstance(v, str) else bytes(v)
            parts.append(struct.pack("<Q", len(b)) + b)
        elif kind == "float":
            parts.append(struct.pack("<d", float(v)))
        elif kind == "bool":
            parts.append(struct.pack("<B", 1 if v else 0))
        else:
            parts.append(struct.pack("<q", int(v)))
    return b"".join(parts)


def gguf_metadata_digest_payload_v1(header: GGUFHeader) -> dict[str, Any]:
    """The exact preimage of `gguf_metadata_digest_v1` — kept separate so the digest
    can be audited (and diffed between two files) instead of merely recomputed."""
    bulk: dict[str, dict[str, Any]] = {}
    kv: dict[str, Any] = {}
    for key, value in header.kv.items():
        is_array = isinstance(value, list)
        oversized = is_array and len(value) > BULK_ARRAY_THRESHOLD
        if key in BULK_KV_KEYS or oversized:
            if not is_array:
                # A bulk key that is not an array is a malformed file, not a scalar we
                # should quietly digest as one.
                raise GGUFFormatError(f"{key!r} is a bulk key but its value is not an array")
            elem = header.kv_types.get(key, (None, None))[1]
            kind = _KIND.get(elem, "int") if elem is not None else "string"
            entry: dict[str, Any] = {
                "count": len(value), "kind": kind,
                "sha256": hashlib.sha256(_bulk_stream(value, kind)).hexdigest(),
            }
            if key not in BULK_KV_KEYS:
                entry["note"] = f"array KV with {len(value)} > {BULK_ARRAY_THRESHOLD} elements"
            bulk[key] = entry
        else:
            kv[key] = value
    return {
        "recipe": "gguf_metadata_digest_v1",
        "version": header.version,
        "alignment": header.alignment,
        "kv": kv,
        "bulk": bulk,
        "tensors": [[t["name"], list(t["dims"]), t["type_id"], t["offset"]]
                    for t in header.tensors],
        "data_offset": header.data_offset,
        "file_size": header.file_size,
    }


def gguf_metadata_digest_v1(header: GGUFHeader) -> str:
    """NORMATIVE recipe `gguf_metadata_digest_v1`.

        payload = {
          "recipe": "gguf_metadata_digest_v1",
          "version": <gguf version>, "alignment": <alignment used>,
          "kv":     every KV pair EXCEPT the bulk keys,
          "bulk":   {key: {"count", "kind", "sha256"}} for the four tokenizer arrays and
                    for any other array KV with more than 64 elements (those also carry
                    a "note"); sha256 is over the length-prefixed element stream, order
                    preserved: strings `<Q len> + utf8`, ints `<q>`, floats `<d>`,
                    bools `<B>`,
          "tensors": [[name, dims, type_id, offset], ...] in FILE ORDER,
          "data_offset", "file_size"
        }
        digest = sha256(json.dumps(payload, sort_keys=True, separators=(',',':'),
                                   ensure_ascii=True))

    Raw `json.dumps`, deliberately NOT `canonical_json`: canonical_json rounds floats to
    12 decimals and would fold two genuinely different rope/epsilon settings together,
    and it does not distinguish 1 from 1.0. Here the header is being fingerprinted, not
    a model artifact being compared numerically, so float repr and int/float identity
    are part of the fingerprint.

    `type_id` AND `offset` are in the tensor list on purpose. Two builds can emit the
    same tensor names, shapes and quant labels while disagreeing about block geometry
    (the upstream-vs-Prism Q2_0 QK 64/128 divergence); that disagreement is invisible in
    the names and unmistakable in the offsets.

    `allow_nan=False`: a non-finite float in the header would otherwise be serialised as
    the non-JSON token `NaN`, i.e. a digest over something no other reader can parse.
    """
    payload = gguf_metadata_digest_payload_v1(header)
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------ records

class _Record(BaseModel):
    """Base for every provenance record: `extra="forbid"`, a self-describing
    `record_digest`, and `verify()` that fails closed.

    The digest is filled in on construction when the caller did not supply one (so it
    can never be stale) and is NEVER recomputed on assignment — a record loaded from
    disk carries the digest that was written, and `verify()` is what decides whether
    the bytes still agree with it.
    """

    model_config = ConfigDict(extra="forbid")

    record_digest: str = ""

    def _derive(self) -> None:
        """Fill derived ids before the digest closes over them. Overridden below."""

    def digest_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        payload.pop("record_digest", None)
        return payload

    def compute_record_digest(self) -> str:
        return digest(self.digest_payload())

    @model_validator(mode="after")
    def _fill_record_digest(self) -> _Record:
        self._derive()
        if not self.record_digest:
            self.record_digest = self.compute_record_digest()
        return self

    def verify(self) -> _Record:
        expected = self.compute_record_digest()
        if self.record_digest != expected:
            raise ValueError(
                f"{type(self).__name__} record_digest {self.record_digest!r} does not match "
                f"its contents (expected {expected!r}) — refusing to trust it"
            )
        return self


ROLES = ("historical_small_control", "modern_small", "modern_strong", "efficiency",
         "strong_local_control")
Role = Literal["historical_small_control", "modern_small", "modern_strong", "efficiency",
               "strong_local_control"]
Engine = Literal["llama.cpp-upstream", "llama.cpp-prism"]


class ModelArtifact(_Record):
    """One weights file, pinned by bytes.

    `sha256` is the identity; everything descriptive (`quantization`, `license`,
    `base_model_lineage`) is a claim about it, recorded with the source of the claim
    (`license_source`) because in-GGUF metadata has been observed to be wrong or absent.
    `family` is the quant-family key the "at most one quant per family past DEV" guard
    counts on, so two quants of the same base model MUST share it.
    """

    artifact_id: str = ""
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    role: Role
    family: str = Field(min_length=1)
    base_model_repo: str
    quantizer_or_derivative_repo: str
    source_revision: str
    source_url: str
    filename: str
    format: Literal["gguf"] = "gguf"
    quantization: str
    quantization_measured: dict[str, int] = Field(default_factory=dict)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gguf_metadata_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    gguf_summary: dict[str, Any] = Field(default_factory=dict)
    license: str
    license_source: Literal["gguf", "model_card", "plan"]
    architecture: str
    base_model_lineage: str
    local_path: str
    registered_at: str = Field(default_factory=_now)
    notes: str | None = None

    def _derive(self) -> None:
        expected = f"{self.slug}@{self.sha256[:12]}"
        if not self.artifact_id:
            self.artifact_id = expected
        elif self.artifact_id != expected:
            raise ValueError(f"artifact_id {self.artifact_id!r} does not match {expected!r}")


class RuntimeIdentity(_Record):
    """The engine that will execute the weights: binaries, CUDA libs, build flags, driver.

    Hashing `llama-server` alone is blind — on this build it is a 17 kB launcher and the
    arithmetic lives in `libggml-cuda.so` / `libllama-server-impl.so`, so every `lib*.so*`
    beside it is hashed too and `binary_set_digest` covers the set.
    """

    runtime_id: str = ""
    engine: Engine
    git_remote: str | None = None
    git_rev: str = Field(pattern=r"^[0-9a-f]{7,40}$")
    git_describe: str | None = None
    git_dirty_files: list[str] = Field(default_factory=list)
    build_info_expected: str | None = None
    bin_dir: str = ""
    binaries: dict[str, str] = Field(default_factory=dict)
    binary_set_digest: str = ""
    cmake: dict[str, str | None] = Field(default_factory=dict)
    cuda_lib_dir: str = ""
    cuda_libs: dict[str, str] = Field(default_factory=dict)
    nvcc_version: str | None = None
    driver: dict[str, str | None] = Field(default_factory=dict)
    gpu_name: str | None = None
    os_release: str = ""
    # Informational, but read the note: the shipped RUNPATH points at a dead path, so the
    # value of LD_LIBRARY_PATH decides which cudart/cublas actually loads. Two runs with
    # different values are not the same runtime even at an identical binary_set_digest.
    ld_library_path_template: str = ""
    registered_at: str = Field(default_factory=_now)
    notes: str | None = None

    def _derive(self) -> None:
        if not self.binary_set_digest:
            self.binary_set_digest = digest(self.binaries)
        expected = f"{self.engine}-{self.git_rev[:7]}@{self.binary_set_digest[:12]}"
        if not self.runtime_id:
            self.runtime_id = expected
        elif self.runtime_id != expected:
            raise ValueError(f"runtime_id {self.runtime_id!r} does not match {expected!r}")

    @property
    def runtime_digest(self) -> str:
        """Same value as `record_digest`; named for what the rest of the system calls it."""
        return self.record_digest


class GenerationConfig(_Record):
    """The request side of the measurement: prompt, schema, decoding parameters.

    `response_format` is stored verbatim rather than re-derived at read time because it
    is a *compiled artifact* — llama.cpp turns it into a GBNF grammar, and the schema is
    passed through `to_gbnf_safe`, whose strip list is build-specific. A schema change
    that the verifier tolerates can still change decoding, so it belongs in the digest.
    """

    genconfig_id: str = ""
    evidence_mode: Literal["fixed_evidence"] = "fixed_evidence"
    prompt_ref: str
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_version: str
    workflow_version: str
    temperature: float = 0.0
    seed: int = 42
    max_tokens: int = Field(gt=0)
    response_format: dict[str, Any]
    schema_digest: str = ""
    extra_body: dict[str, Any] = Field(default_factory=dict)

    def _derive(self) -> None:
        if not self.schema_digest:
            self.schema_digest = digest(self.response_format)
        payload = self.digest_payload()
        payload.pop("genconfig_id", None)
        expected = f"gc@{digest(payload)[:12]}"
        if not self.genconfig_id:
            self.genconfig_id = expected
        elif self.genconfig_id != expected:
            raise ValueError(f"genconfig_id {self.genconfig_id!r} does not match {expected!r}")

    @property
    def generation_config_digest(self) -> str:
        return self.record_digest


# Flags that name WHERE the server is, not WHAT it computes. Dropped from `material` so
# a port change does not read as a different execution system.
_INFORMATIONAL_FLAGS = ("--host", "--port", "--alias", "-m", "--model", "--log-file")


def _material_args(argv: list[str]) -> list[str]:
    """`argv` minus the binary path and the informational flag/value pairs, order kept."""
    out: list[str] = []
    skip = False
    for i, tok in enumerate(argv):
        if i == 0:
            continue                      # the binary path; its identity is binary_set_digest
        if skip:
            skip = False
            continue
        if tok in _INFORMATIONAL_FLAGS:
            skip = True
            continue
        if any(tok.startswith(f"{flag}=") for flag in _INFORMATIONAL_FLAGS):
            continue
        out.append(tok)
    return out


class ServerArgs(_Record):
    """The llama.cpp server's full /proc cmdline, split into what it computes
    (`material`) and where it listens (dropped)."""

    argv: list[str] = Field(min_length=1)
    material: list[str] = Field(default_factory=list)
    server_args_digest: str = ""

    def _derive(self) -> None:
        if not self.material:
            self.material = _material_args(self.argv)
        if not self.server_args_digest:
            self.server_args_digest = digest(self.material)

    @property
    def ctx(self) -> int | None:
        """`-c` / `--ctx-size`, the one server flag that changes what fits in a prompt."""
        for i, tok in enumerate(self.material):
            if tok in ("-c", "--ctx-size") and i + 1 < len(self.material):
                try:
                    return int(self.material[i + 1])
                except ValueError:
                    return None
            if tok.startswith(("-c=", "--ctx-size=")):
                try:
                    return int(tok.split("=", 1)[1])
                except ValueError:
                    return None
        return None


class ExecutionSystem(_Record):
    """Artifact + runtime + server flags + request config, bound into one digest.

    This is the unit a result is comparable within. Every field is a digest or an id
    that resolves to one, so the record is small enough to stamp onto every trajectory's
    runtime_context and still name the whole stack.
    """

    artifact_id: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gguf_metadata_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_id: str
    runtime_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    server_args_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    server_args_material: list[str] = Field(default_factory=list)
    genconfig_id: str
    generation_config_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    ctx: int = Field(gt=0)

    @property
    def execution_system_digest(self) -> str:
        return self.record_digest


# ------------------------------------------------------------------------ capture

def _run(cmd: list[str], cwd: Path | None = None, timeout: float = 30.0) -> str | None:
    """Read-only shell-out. None on any failure — a missing tool is a missing field,
    never a crash halfway through capturing an identity."""
    try:
        r = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True,
                           text=True, timeout=timeout, check=True)
        return r.stdout.strip()
    except Exception:  # noqa: BLE001 — capture is best-effort by design
        return None


_CMAKE_KEYS = (
    "CMAKE_BUILD_TYPE", "CMAKE_CUDA_ARCHITECTURES", "GGML_CUDA", "GGML_CUDA_FA",
    "GGML_NATIVE", "GGML_CPU_REPACK", "GGML_CUDA_GRAPHS", "GGML_CUDA_FORCE_MMQ",
    "GGML_CUDA_FORCE_CUBLAS", "CUDAToolkit_VERSION", "CMAKE_CUDA_COMPILER_VERSION",
)

_CUDA_LIB_PATTERNS = ("libcudart.so.12*", "libcublas.so.12*", "libcublasLt.so.12*",
                      "libnvrtc.so.12*")


def _read_cmake_cache(path: Path) -> dict[str, str | None]:
    """The material build switches from a CMakeCache.txt. Everything else in that file
    is paths and compiler probes, which differ between machines that compute the same."""
    values: dict[str, str | None] = {k: None for k in _CMAKE_KEYS}
    if not path.exists():
        return values
    for line in path.read_text(errors="replace").splitlines():
        head, sep, val = line.partition("=")
        if not sep or ":" not in head:
            continue
        name = head.split(":", 1)[0].strip()
        if name in values:
            values[name] = val.strip()
    return values


def _driver_facts() -> tuple[dict[str, str | None], str | None]:
    """(driver dict, gpu name) from nvidia-smi.

    The three version strings are genuinely different numbers and have been confused
    before, so each is recorded raw and named for where it comes from:
      nvidia_smi_version  the `NVIDIA-SMI x` field of the header line;
      driver_kmd_version  `--query-gpu=driver_version` (the kernel-mode driver);
      cuda_umd_version    the header's `CUDA Version:` field (the user-mode CUDA).
    """
    driver: dict[str, str | None] = {"nvidia_smi_version": None, "driver_kmd_version": None,
                                     "cuda_umd_version": None}
    header = _run(["nvidia-smi"]) or ""
    m = re.search(r"NVIDIA-SMI\s+(\S+)", header)
    if m:
        driver["nvidia_smi_version"] = m.group(1)
    m = re.search(r"CUDA (?:UMD )?Version:\s*(\S+)", header)   # "CUDA UMD Version" on 610.x, "CUDA Version" before
    if m:
        driver["cuda_umd_version"] = m.group(1)
    gpu_name = None
    q = _run(["nvidia-smi", "--query-gpu=driver_version,name", "--format=csv,noheader"])
    if q:
        first = q.splitlines()[0]
        parts = [p.strip() for p in first.split(",", 1)]
        driver["driver_kmd_version"] = parts[0] or None
        gpu_name = parts[1] if len(parts) > 1 else None
    return driver, gpu_name


def capture_runtime(engine: str, llama_dir: Path | str, bin_dir: Path | str,
                    cuda_lib_dir: Path | str, build_info_expected: str | None = None,
                    *, notes: str | None = None) -> RuntimeIdentity:
    """Photograph the engine. Every operation is read-only: git queries, file hashes,
    `nvidia-smi`, `nvcc --version`. Nothing is built, started or written."""
    llama_dir, bin_dir, cuda_lib_dir = Path(llama_dir), Path(bin_dir), Path(cuda_lib_dir)

    git_rev = _run(["git", "rev-parse", "HEAD"], cwd=llama_dir)
    if not git_rev:
        raise ValueError(f"{llama_dir} is not a git checkout — the engine revision is the "
                         "one thing that cannot be reconstructed later")
    status = _run(["git", "status", "--porcelain"], cwd=llama_dir) or ""

    binaries: dict[str, str] = {}
    server = bin_dir / "llama-server"
    if server.exists():
        binaries[server.name] = sha256_file(server)
    for lib in sorted(bin_dir.glob("lib*.so*")):
        if lib.is_file():
            binaries[lib.name] = sha256_file(lib)

    cuda_libs: dict[str, str] = {}
    for pattern in _CUDA_LIB_PATTERNS:
        for lib in sorted(cuda_lib_dir.glob(pattern)):
            real = lib.resolve()
            if real.is_file():
                cuda_libs[real.name] = sha256_file(real)

    cache = next((c for c in (bin_dir.parent / "CMakeCache.txt", bin_dir / "CMakeCache.txt",
                              llama_dir / "build-cuda" / "CMakeCache.txt") if c.exists()),
                 bin_dir.parent / "CMakeCache.txt")
    nvcc = cuda_lib_dir.parent / "bin" / "nvcc"
    driver, gpu_name = _driver_facts()

    return RuntimeIdentity(
        engine=engine,
        git_remote=_run(["git", "remote", "get-url", "origin"], cwd=llama_dir),
        git_rev=git_rev,
        git_describe=_run(["git", "describe", "--tags", "--always"], cwd=llama_dir),
        git_dirty_files=[ln.strip() for ln in status.splitlines() if ln.strip()],
        build_info_expected=build_info_expected,
        bin_dir=str(bin_dir), binaries=binaries,
        cmake=_read_cmake_cache(cache),
        cuda_lib_dir=str(cuda_lib_dir), cuda_libs=cuda_libs,
        nvcc_version=_run([str(nvcc), "--version"]) if nvcc.exists() else None,
        driver=driver, gpu_name=gpu_name, os_release=os.uname().release,
        ld_library_path_template=f"{cuda_lib_dir}:{bin_dir}:",
        notes=notes,
    )


def build_generation_config(prompt_ref: str, max_tokens: int) -> GenerationConfig:
    """The request config, read OUT of the adapter rather than restated beside it.

    `temperature`, `seed` and `response_format` come from a real `build_body()` call on a
    dummy manifest, so the recorded config cannot drift from the body the runner actually
    sends: if someone changes the adapter's greedy defaults, this record changes with it
    and every digest that quotes it moves. Imports are local so `provenance` stays
    importable (and testable) without the gateway, httpx or the orchestrator.
    """
    from fis_platform.model_gateway.base import GenerationRequest, Message
    from fis_platform.model_gateway.local import LocalLlamaCppAdapter
    from schemas.common import ModelTier, Provider
    from schemas.investigator import InvestigationResult
    from schemas.model_manifest import ModelManifest
    from services.ai_orchestrator.investigate import PROMPT_VERSION, WORKFLOW_VERSION
    from services.ai_orchestrator.prompts import PROMPTS

    if prompt_ref not in PROMPTS:
        raise ValueError(f"unknown prompt {prompt_ref!r}; known: {sorted(PROMPTS)}")
    system = PROMPTS[prompt_ref]

    manifest = ModelManifest(
        ref="provenance-probe", tier=ModelTier.SPECIALIST, provider=Provider.LOCAL_LLAMACPP,
        model_id="provenance-probe", context_window=16384, max_output_tokens=max_tokens,
        base_url="http://127.0.0.1:0/v1", supports_structured_output=True, supports_seed=True,
    )
    req = GenerationRequest(
        model_ref="provenance-probe",
        messages=[Message(role="user", content="probe")],
        system=system,
        json_schema=InvestigationResult.model_json_schema(),
        max_tokens=max_tokens,
    )
    body = LocalLlamaCppAdapter(manifest).build_body(req)
    known = {"model", "messages", "max_tokens", "temperature", "seed", "response_format"}

    return GenerationConfig(
        prompt_ref=prompt_ref,
        prompt_sha256=hashlib.sha256(system.encode("utf-8")).hexdigest(),
        prompt_version=PROMPT_VERSION, workflow_version=WORKFLOW_VERSION,
        temperature=body["temperature"], seed=body["seed"], max_tokens=body["max_tokens"],
        response_format=body["response_format"],
        extra_body={k: v for k, v in body.items() if k not in known},
    )


def capture_server_args(port: int, proc: Path | str = "/proc") -> ServerArgs | None:
    """The running llama-server's full argv, matched the way the runner matches it
    (`evals/runner/run_eval.py:local_server_session`): a `llama-server` process whose
    cmdline contains `--port <port>`. None when nothing is listening."""
    root = Path(proc)
    matches: list[tuple[str, list[str]]] = []
    for pid in sorted(p.name for p in root.iterdir() if p.name.isdigit()):
        try:
            raw = (root / pid / "cmdline").read_bytes()
        except OSError:
            continue
        argv = [a for a in raw.decode(errors="replace").split("\0") if a]
        if not argv or Path(argv[0]).name != "llama-server":
            continue
        pairs = list(zip(argv, argv[1:]))
        if ("--port", str(port)) in pairs:
            matches.append((pid, argv))
    if not matches:
        return None
    if len(matches) > 1:
        raise TransitionRefused(
            f"{len(matches)} llama-server processes claim --port {port} ({[m[0] for m in matches]}) "
            "— refusing to guess which one is the execution system")
    return ServerArgs(argv=matches[0][1])


def llama_server_pids(proc: Path | str = "/proc") -> list[str]:
    """Every process whose argv[0] is llama-server — R6 requires exactly one resident."""
    root = Path(proc)
    out = []
    for pid in sorted(p.name for p in root.iterdir() if p.name.isdigit()):
        try:
            raw = (root / pid / "cmdline").read_bytes()
        except OSError:
            continue
        argv = [a for a in raw.decode(errors="replace").split("\0") if a]
        if argv and Path(argv[0]).name == "llama-server":
            out.append(pid)
    return out


def bind_running_server(port: int, runtime: RuntimeIdentity, proc: Path | str = "/proc") -> dict[str, Any]:
    """Prove the RUNNING server on `port` is the registered runtime: hash /proc/pid/exe and
    every mapped lib*.so* and require each to be in the runtime record with the same sha
    (libs the record does not name — libstdc++/libgomp/libgcc from the CUDA env — are hashed
    and reported, not refused, unless they are libggml*/libllama*/libcu*). Reads the server's
    LD_LIBRARY_PATH and refuses any LLAMA_ARG_* environment (llama-server reads those as
    arguments, invisible in /proc/cmdline). Fails closed on any mismatch."""
    root = Path(proc)
    pid = None
    for cand in sorted(p.name for p in root.iterdir() if p.name.isdigit()):
        try:
            argv = [a for a in (root / cand / "cmdline").read_bytes().decode(errors="replace").split("\0") if a]
        except OSError:
            continue
        if argv and Path(argv[0]).name == "llama-server" and ("--port", str(port)) in list(zip(argv, argv[1:])):
            pid = cand
            break
    if pid is None:
        raise TransitionRefused(f"no llama-server on port {port}")
    known = {**runtime.binaries, **runtime.cuda_libs}
    exe = os.readlink(root / pid / "exe")
    mapped = sorted({ln.split()[5] for ln in (root / pid / "maps").read_text().splitlines()
                     if len(ln.split()) >= 6 and ".so" in ln.split()[5]})
    checked, extra, mismatched = {}, {}, []
    bin_root = Path(runtime.bin_dir).resolve()
    cuda_root = Path(runtime.cuda_lib_dir).resolve().parent     # the CUDA env (…/cudaenv)
    for f in [exe] + mapped:
        real = Path(f).resolve()
        name = real.name
        in_runtime_tree = (f == exe or str(real).startswith((str(bin_root), str(cuda_root)))
                           or "llama.cpp" in str(real))
        if not (in_runtime_tree or "cuda" in str(real).lower()):
            continue
        h = sha256_file(real)
        if name in known:
            checked[name] = h
            if known[name] != h:
                mismatched.append(name)
        else:
            extra[name] = h
            # anything the runtime tree provides but the record does not name is a hole in the
            # record; the driver's user-mode libcuda (from /usr/lib/wsl or the system) is
            # identified by driver version in the record and is reported, not refused.
            if in_runtime_tree and name.startswith(("libggml", "libllama", "libcu")):
                mismatched.append(f"{name} (not in runtime record)")
    if mismatched:
        raise TransitionRefused(f"running server on port {port} is not the registered runtime "
                                f"{runtime.runtime_id}: {mismatched}")
    if Path(exe).resolve() != Path(runtime.bin_dir, "llama-server").resolve():
        raise TransitionRefused(f"running exe {exe} is not {runtime.bin_dir}/llama-server")
    env = {}
    try:
        for kv in (root / pid / "environ").read_bytes().decode(errors="replace").split("\0"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                env[k] = v
    except OSError:
        pass
    llama_env = {k: v for k, v in env.items() if k.startswith(("LLAMA_ARG_", "GGML_"))}
    if llama_env:
        raise TransitionRefused(f"server process carries argument-bearing environment {llama_env}")
    return {"pid": pid, "exe": exe, "checked": checked, "extra_libs": extra,
            "ld_library_path": env.get("LD_LIBRARY_PATH", "")}


# ------------------------------------------------------------------ state machine

REGISTERED = "REGISTERED"
TRAIN_COMPATIBLE = "TRAIN_COMPATIBLE"
CONTRACT_FROZEN = "CONTRACT_FROZEN"
DEV_EVALUATED = "DEV_EVALUATED"
DEV_QUALIFIED = "DEV_QUALIFIED"
DEV_REJECTED = "DEV_REJECTED"
TEST_UNLOCKED = "TEST_UNLOCKED"
TEST_EVALUATED = "TEST_EVALUATED"
WITHDRAWN = "WITHDRAWN"

# The ONLY legal edges. WITHDRAWN is reachable from REGISTERED / TRAIN_COMPATIBLE only —
# a candidate that turns out to be runtime-incompatible on TRAIN can leave, but nothing
# that has seen DEV or TEST may be quietly removed from the comparison afterwards.
TRANSITIONS: dict[str, tuple[str, ...]] = {
    REGISTERED: (TRAIN_COMPATIBLE, WITHDRAWN),
    TRAIN_COMPATIBLE: (CONTRACT_FROZEN, WITHDRAWN),
    CONTRACT_FROZEN: (DEV_EVALUATED,),
    DEV_EVALUATED: (DEV_QUALIFIED, DEV_REJECTED),
    DEV_QUALIFIED: (TEST_UNLOCKED,),
    DEV_REJECTED: (),
    TEST_UNLOCKED: (TEST_EVALUATED,),
    TEST_EVALUATED: (),
    WITHDRAWN: (),
}
STATES = tuple(TRANSITIONS)
TERMINAL_STATES = tuple(s for s, nxt in TRANSITIONS.items() if not nxt)

# "At or beyond DEV" for the one-quant-per-family guard: once a family has spent a DEV
# evaluation, a second quant of the same base model would be a second look at the same
# question with a different die.
DEV_OR_BEYOND = (DEV_EVALUATED, DEV_QUALIFIED, DEV_REJECTED, TEST_UNLOCKED, TEST_EVALUATED)
TEST_STATES = (TEST_UNLOCKED, TEST_EVALUATED)


class RegistryIntegrityError(SystemExit):
    """The log, HEAD or a record does not verify. Read paths fail closed on it."""


class TransitionRefused(SystemExit):
    """A guard said no. The log is unchanged."""


class IllegalTransition(TransitionRefused):
    """The requested edge is not in `TRANSITIONS` at all."""


def default_root() -> Path:
    """`<repo>/learning/registry/r6`. The canonical tree, named in exactly one place.

    There is deliberately no environment variable and no CLI flag that relocates the
    registry: a relocatable root is a reset button with extra steps. Tests construct
    `R6Registry(tmp_path)` explicitly instead.
    """
    return _ROOT / "learning" / "registry" / "r6"


REGISTRY_REL = Path("learning") / "registry" / "r6"


def dirty_paths_outside_registry() -> list[str]:
    """Tracked files modified since HEAD that are NOT the R6 registry's own bookkeeping.

    The registry's append-only files (ledger, phases, state logs, result files) are
    git-tracked and are written by the very runs and transitions being guarded, so
    "git status is empty" can never hold at the moment a run starts. The requirement that
    matters is that the CODE tree is exactly a commit; the registry may be ahead of it
    (contract § 14 amendment 1). Returns the offending paths, empty if the code tree is clean.
    """
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                             cwd=_ROOT, capture_output=True, text=True, timeout=10,
                             check=True).stdout
    except Exception:  # noqa: BLE001 — treated as dirty by the caller
        return ["(git unavailable)"]
    bad = []
    for line in out.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path.startswith(str(REGISTRY_REL) + "/"):
            bad.append(path)      # modified OR untracked (gitignored files never appear)
    return bad


def tree_state() -> tuple[str, bool, list[str]]:
    """(code_commit, code_tree_clean, dirty_paths). `code_commit` is `git_head()`
    (`<sha>` or `<sha>-dirty`); `code_tree_clean` is True iff there is a commit and every
    modified tracked path lies inside the R6 registry. A `-dirty` head with no listable
    dirty paths is treated as dirty (fail closed)."""
    code_commit = git_head()
    if not code_commit:
        return code_commit, False, ["(git unavailable)"]
    outside = dirty_paths_outside_registry()      # tracked-modified AND untracked, outside
    if outside == ["(git unavailable)"]:
        return code_commit, False, outside
    if code_commit.endswith("-dirty") and not outside:
        # `git_head` saw modified tracked files but every one is registry bookkeeping.
        return code_commit, True, []
    return code_commit, len(outside) == 0, outside


def registry_ahead_of_git_only_by_appends() -> list[str]:
    """Every tracked append-only file under the registry must have its committed content
    as a byte-prefix of the working copy, and every committed HEAD.json seq must be <= the
    working seq. Returns the violations (empty = fine). Detects the two resets a chained log
    cannot see by itself: a truncated log with a matching HEAD.json, and a `git checkout` /
    `git stash` that silently dropped uncommitted run lines."""
    problems: list[str] = []
    try:
        tracked = subprocess.run(["git", "ls-files", "--", str(REGISTRY_REL)], cwd=_ROOT,
                                 capture_output=True, text=True, timeout=10, check=True).stdout.split()
    except Exception:  # noqa: BLE001
        return ["(git unavailable)"]
    for rel in tracked:
        if not rel.endswith((".jsonl",)):
            continue
        try:
            committed = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_ROOT,
                                       capture_output=True, timeout=10, check=True).stdout
        except Exception:  # noqa: BLE001 — new file (not yet in HEAD): nothing to compare
            continue
        working_path = _ROOT / rel
        working = working_path.read_bytes() if working_path.exists() else b""
        if not working.startswith(committed):
            problems.append(f"{rel}: committed content is not a prefix of the working file")
    head_rel = str(REGISTRY_REL / "HEAD.json")
    if head_rel in tracked:
        try:
            committed_head = json.loads(subprocess.run(["git", "show", f"HEAD:{head_rel}"], cwd=_ROOT,
                                                       capture_output=True, text=True, timeout=10,
                                                       check=True).stdout or "{}")
        except Exception:  # noqa: BLE001
            committed_head = {}
        working_path = _ROOT / head_rel
        working_head = json.loads(working_path.read_text() or "{}") if working_path.exists() else {}
        for cid, ref in committed_head.items():
            cur = working_head.get(cid)
            if cur is None or int(cur.get("seq", 0)) < int(ref.get("seq", 0)):
                problems.append(f"HEAD.json: {cid} regressed or vanished vs the committed seq {ref.get('seq')}")
    return problems


def contract_blob_sha(path: str = "docs/R6_EXPERIMENT_CONTRACT.md") -> str | None:
    """git blob sha of the CONTRACT as committed at HEAD (None if git/file unavailable)."""
    try:
        return subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=_ROOT, capture_output=True,
                              text=True, timeout=10, check=True).stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def committed_contract_extends(frozen_blob: str, path: str = "docs/R6_EXPERIMENT_CONTRACT.md") -> bool:
    """True iff the contract committed at HEAD is byte-identical to the frozen blob or is
    the frozen blob plus appended text (the § 17 amendment log grows; nothing above it may
    change after the freeze)."""
    try:
        frozen = subprocess.run(["git", "cat-file", "-p", frozen_blob], cwd=_ROOT, capture_output=True,
                                timeout=10, check=True).stdout
        current = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=_ROOT, capture_output=True,
                                 timeout=10, check=True).stdout
    except Exception:  # noqa: BLE001
        return False
    return current.startswith(frozen)


def _append_line(path: Path, obj: dict[str, Any]) -> None:
    """The only writer of the append-only files. Opens "a" — never truncates, never
    rewrites a line that is already there."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, sort_keys=True) + "\n")


def _read_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def _dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _entry_to(entries: list[dict[str, Any]], state: str) -> dict[str, Any] | None:
    """The last TRANSITION entry into `state` (run entries do not change state)."""
    for e in reversed(entries):
        if e.get("kind") == "transition" and e.get("to") == state:
            return e
    return None


class R6Registry:
    """R6 experiment state on disk. `root` is an explicit constructor argument — the
    canonical tree is `default_root()` and nothing else may point this elsewhere.

        models/<artifact_id>.json           one weights file, pinned by sha256
        runtimes/<runtime_id>.json          one engine build
        genconfigs/<genconfig_id>.json      one request config
        candidates/<candidate_id>/
            identity.json                   artifact x runtime, digested
            state.jsonl                     append-only, hash-chained log
            dev_result.json                 written exactly once
            test_result.json                written exactly once
        HEAD.json                           {candidate_id: {seq, entry_digest}}
        ledger.jsonl                        append-only run ledger (start + end lines)
        phases.jsonl                        append-only wall-time timeline

    HEAD.json is the only rewritten file, and it holds no information the log does not:
    it exists so a truncated log is detected instead of read as "fewer things happened".
    """

    def __init__(self, root: Path | str, *, git_checks: bool = True) -> None:
        self.root = Path(root)
        # `git_checks=False` only for tmp registries in tests (no committed contract to bind
        # against); the CLI and the runner always run with the checks on.
        self.git_checks = bool(git_checks)

    # -------------------------------------------------------------- paths
    @property
    def models_dir(self) -> Path: return self.root / "models"
    @property
    def runtimes_dir(self) -> Path: return self.root / "runtimes"
    @property
    def genconfigs_dir(self) -> Path: return self.root / "genconfigs"
    @property
    def candidates_dir(self) -> Path: return self.root / "candidates"
    @property
    def head_file(self) -> Path: return self.root / "HEAD.json"
    @property
    def ledger_file(self) -> Path: return self.root / "ledger.jsonl"
    @property
    def phases_file(self) -> Path: return self.root / "phases.jsonl"

    def candidate_dir(self, candidate_id: str) -> Path: return self.candidates_dir / candidate_id
    def identity_file(self, cid: str) -> Path: return self.candidate_dir(cid) / "identity.json"
    def state_file(self, cid: str) -> Path: return self.candidate_dir(cid) / "state.jsonl"
    def dev_result_file(self, cid: str) -> Path: return self.candidate_dir(cid) / "dev_result.json"
    def test_result_file(self, cid: str) -> Path: return self.candidate_dir(cid) / "test_result.json"

    def candidate_ids(self) -> list[str]:
        on_disk = set()
        if self.candidates_dir.exists():
            on_disk = {p.name for p in self.candidates_dir.iterdir() if (p / "identity.json").exists()}
        named = set(self._read_head())
        missing = sorted(named - on_disk)
        if missing:
            raise RegistryIntegrityError(
                f"HEAD.json names candidates with no identity/log on disk: {missing} — a candidate "
                "cannot vanish; restore from git")
        return sorted(on_disk | named)

    # -------------------------------------------------------------- records
    def _put(self, path: Path, record: _Record, kind: str, ident: str) -> Path:
        record.verify()
        if path.exists():
            existing = json.loads(path.read_text())
            if existing.get("record_digest") == record.record_digest:
                return path                      # idempotent re-registration
            raise RegistryIntegrityError(
                f"{kind} {ident!r} is already registered with record_digest "
                f"{str(existing.get('record_digest'))[:12]}… and the new record digests to "
                f"{record.record_digest[:12]}… — refusing to overwrite it. Delete nothing; "
                f"register the changed thing under its own id."
            )
        _dump(path, record.model_dump(mode="json"))
        return path

    def put_artifact(self, rec: ModelArtifact) -> Path:
        return self._put(self.models_dir / f"{rec.artifact_id}.json", rec,
                         "artifact", rec.artifact_id)

    def put_runtime(self, rec: RuntimeIdentity) -> Path:
        return self._put(self.runtimes_dir / f"{rec.runtime_id}.json", rec,
                         "runtime", rec.runtime_id)

    def put_genconfig(self, rec: GenerationConfig) -> Path:
        return self._put(self.genconfigs_dir / f"{rec.genconfig_id}.json", rec,
                         "generation config", rec.genconfig_id)

    def get_artifact(self, artifact_id: str) -> ModelArtifact:
        path = self.models_dir / f"{artifact_id}.json"
        if not path.exists():
            raise RegistryIntegrityError(f"no artifact record at {path}")
        return ModelArtifact(**json.loads(path.read_text())).verify()   # type: ignore[return-value]

    def get_runtime(self, runtime_id: str) -> RuntimeIdentity:
        path = self.runtimes_dir / f"{runtime_id}.json"
        if not path.exists():
            raise RegistryIntegrityError(f"no runtime record at {path}")
        return RuntimeIdentity(**json.loads(path.read_text())).verify()  # type: ignore[return-value]

    def get_genconfig(self, genconfig_id: str) -> GenerationConfig:
        path = self.genconfigs_dir / f"{genconfig_id}.json"
        if not path.exists():
            raise RegistryIntegrityError(f"no generation config record at {path}")
        return GenerationConfig(**json.loads(path.read_text())).verify()  # type: ignore[return-value]

    # -------------------------------------------------------------- chain
    def _read_head(self) -> dict[str, Any]:
        if not self.head_file.exists():
            return {}
        return json.loads(self.head_file.read_text())

    def read_state(self, candidate_id: str) -> list[dict[str, Any]]:
        """The verified log. Every entry's digest is recomputed, every `prev` must match
        the previous entry, `seq` must be 1..n with no gaps, and HEAD.json must name the
        last entry — which is what makes a truncated log an error rather than a shorter
        history."""
        path = self.state_file(candidate_id)
        if not path.exists():
            raise RegistryIntegrityError(f"no state log for candidate {candidate_id!r} at {path}")
        entries = _read_lines(path)
        if not entries:
            raise RegistryIntegrityError(f"state log for {candidate_id!r} is empty")
        prev = ""
        for i, e in enumerate(entries, start=1):
            if e.get("seq") != i:
                raise RegistryIntegrityError(
                    f"{candidate_id}: entry {i} claims seq {e.get('seq')!r} — the log has a gap")
            if e.get("prev_entry_digest") != prev:
                raise RegistryIntegrityError(
                    f"{candidate_id}: entry seq {i} chains to "
                    f"{str(e.get('prev_entry_digest'))[:12]}… but seq {i - 1} digests to "
                    f"{prev[:12] or '(genesis)'}… — the log was rewritten")
            body = {k: v for k, v in e.items() if k != "entry_digest"}
            recomputed = digest(body)
            if recomputed != e.get("entry_digest"):
                raise RegistryIntegrityError(
                    f"{candidate_id}: entry seq {i} digests to {recomputed[:12]}… but records "
                    f"{str(e.get('entry_digest'))[:12]}… — the entry was edited")
            prev = e["entry_digest"]
        head = self._read_head().get(candidate_id)
        if head is None:
            raise RegistryIntegrityError(
                f"{candidate_id}: HEAD.json has no entry, but {len(entries)} log entries exist")
        if head.get("seq") != len(entries) or head.get("entry_digest") != prev:
            raise RegistryIntegrityError(
                f"{candidate_id}: HEAD.json points at seq {head.get('seq')} / "
                f"{str(head.get('entry_digest'))[:12]}… but the log ends at seq {len(entries)} / "
                f"{prev[:12]}… — the log was truncated or replaced")
        return entries

    def current_state(self, candidate_id: str) -> str:
        return self.read_state(candidate_id)[-1]["to"]

    def read_identity(self, candidate_id: str) -> dict[str, Any]:
        path = self.identity_file(candidate_id)
        if not path.exists():
            raise RegistryIntegrityError(f"no identity record at {path}")
        identity = json.loads(path.read_text())
        expected = digest({k: v for k, v in identity.items() if k != "identity_digest"})
        if identity.get("identity_digest") != expected:
            raise RegistryIntegrityError(
                f"{candidate_id}: identity.json digests to {expected[:12]}… but records "
                f"{str(identity.get('identity_digest'))[:12]}… — refusing to trust it")
        return identity

    def _append(self, candidate_id: str, kind: str, from_state: str | None, to_state: str,
                payload: dict[str, Any], code_commit: str, tree_clean: bool) -> dict[str, Any]:
        path = self.state_file(candidate_id)
        if not path.exists() and candidate_id in self._read_head():
            raise RegistryIntegrityError(
                f"{candidate_id}: HEAD.json names this candidate but its state log is missing — "
                "a deleted candidate cannot be re-created; restore the log from git")
        entries = self.read_state(candidate_id) if path.exists() else []
        entry = {
            "seq": len(entries) + 1,
            "kind": kind,
            "prev_entry_digest": entries[-1]["entry_digest"] if entries else "",
            "from": from_state,
            "to": to_state,
            "at": _now(),
            "code_commit": code_commit,
            "tree_clean": tree_clean,
            "payload": payload,
        }
        entry["entry_digest"] = digest(entry)
        _append_line(path, entry)
        head = self._read_head()
        head[candidate_id] = {"seq": entry["seq"], "entry_digest": entry["entry_digest"]}
        _dump(self.head_file, head)
        return entry

    # -------------------------------------------------------------- ledger / phases
    def read_ledger(self, candidate_id: str | None = None) -> list[dict[str, Any]]:
        lines = _read_lines(self.ledger_file)
        if candidate_id is None:
            return lines
        return [ln for ln in lines if ln.get("candidate_id") == candidate_id]

    def ledger_run_ids(self, candidate_id: str, split: str) -> list[str]:
        """Distinct run ids this candidate has STARTED on `split`, in order."""
        out: list[str] = []
        for ln in self.read_ledger(candidate_id):
            if ln.get("split") == split and ln.get("event") == "start" \
                    and ln.get("run_id") not in out:
                out.append(str(ln.get("run_id")))
        return out

    def record_phase(self, name: str, event: str, note: str | None = None) -> dict[str, Any]:
        """Append-only wall-time timeline. Reporting only — no state depends on it."""
        if event not in ("start", "end"):
            raise TransitionRefused(f"phase event must be start|end, got {event!r}")
        line = {"name": name, "event": event, "at": _now(), "code_commit": git_head(),
                "note": note}
        _append_line(self.phases_file, line)
        return line

    # -------------------------------------------------------------- candidates
    def register_candidate(self, slug: str, artifact: ModelArtifact, runtime: RuntimeIdentity,
                           family: str | None = None, role: str | None = None, *,
                           verify_bytes: bool = True) -> str:
        """Bind one artifact to one runtime and open its log at REGISTERED.

        `candidate_id` is derived from the two digests that decide what the numbers mean
        (artifact bytes, runtime), so the same pair cannot be registered twice under two
        names and quietly get two DEV looks. The artifact file itself is re-checked here:
        size always, sha256 unless `verify_bytes=False`, because "the file on disk is the
        file we hashed" is exactly the assumption every later digest rests on.
        """
        art_path = self.models_dir / f"{artifact.artifact_id}.json"
        rt_path = self.runtimes_dir / f"{runtime.runtime_id}.json"
        for other in self.candidate_ids():
            oth = self.read_identity(other)
            oth_art = self.get_artifact(oth["artifact_id"])
            if (oth_art.base_model_repo == artifact.base_model_repo
                    and oth.get("family") != (family or artifact.family)):
                raise TransitionRefused(
                    f"artifact {artifact.artifact_id} shares base_model_repo {artifact.base_model_repo!r} "
                    f"with candidate {other} but declares family {family or artifact.family!r} != "
                    f"{oth.get('family')!r} — the family key is what bounds one DEV look per base model")
        for path, rec, kind in ((art_path, artifact, "artifact"), (rt_path, runtime, "runtime")):
            if not path.exists():
                raise TransitionRefused(
                    f"{kind} {rec.record_digest[:12]}… is not in the registry ({path} missing) "
                    "— register the record before the candidate that cites it")
            stored = json.loads(path.read_text()).get("record_digest")
            if stored != rec.record_digest:
                raise TransitionRefused(
                    f"{kind} record at {path} digests to {str(stored)[:12]}… but the one passed "
                    f"here digests to {rec.record_digest[:12]}… — refusing")
        rec_family = family if family is not None else artifact.family
        rec_role = role if role is not None else artifact.role
        if rec_family != artifact.family or rec_role != artifact.role:
            raise TransitionRefused(
                f"candidate declares family/role ({rec_family!r}, {rec_role!r}) but the artifact "
                f"record says ({artifact.family!r}, {artifact.role!r}) — the family key is what "
                "the one-quant-per-family guard counts, so it may not be restated here")

        local = Path(artifact.local_path)
        if not local.exists():
            raise TransitionRefused(f"artifact file {local} does not exist")
        size = local.stat().st_size
        if size != artifact.size_bytes:
            raise TransitionRefused(
                f"{local} is {size} bytes, the record says {artifact.size_bytes} — refusing")
        if verify_bytes:
            actual = sha256_file(local)
            if actual != artifact.sha256:
                raise TransitionRefused(
                    f"{local} hashes to {actual[:12]}…, the record says {artifact.sha256[:12]}… "
                    "— refusing")

        candidate_id = f"{slug}@{digest({'artifact_sha256': artifact.sha256, 'runtime_digest': runtime.record_digest})[:12]}"
        if self.identity_file(candidate_id).exists():
            raise TransitionRefused(f"candidate {candidate_id!r} is already registered")
        for other in self.candidate_ids():
            ident = self.read_identity(other)
            if (ident.get("artifact_sha256"), ident.get("runtime_digest")) == \
                    (artifact.sha256, runtime.record_digest):
                raise TransitionRefused(
                    f"candidate {other!r} already binds this artifact to this runtime — one "
                    "(artifact, runtime) pair is one candidate")

        identity = {
            "candidate_id": candidate_id, "slug": slug, "family": rec_family, "role": rec_role,
            "artifact_id": artifact.artifact_id, "artifact_sha256": artifact.sha256,
            "gguf_metadata_digest": artifact.gguf_metadata_digest,
            "runtime_id": runtime.runtime_id, "runtime_digest": runtime.record_digest,
            "registered_at": _now(),
        }
        identity["identity_digest"] = digest(identity)
        _dump(self.identity_file(candidate_id), identity)
        code_commit, tree_clean, _ = tree_state()
        self._append(candidate_id, "transition", None, REGISTERED,
                     {"identity_digest": identity["identity_digest"], "slug": slug,
                      "family": rec_family, "role": rec_role},
                     code_commit, tree_clean)
        return candidate_id

    def family_members(self, family: str, states: tuple[str, ...],
                       exclude: str) -> list[tuple[str, str]]:
        """(candidate_id, state) for every OTHER candidate of `family` in `states`."""
        out = []
        for other in self.candidate_ids():
            if other == exclude:
                continue
            ident = self.read_identity(other)
            if ident.get("family") != family:
                continue
            state = self.current_state(other)
            if state in states:
                out.append((other, state))
        return out

    # -------------------------------------------------------------- transitions
    def transition(self, candidate_id: str, to: str, payload: dict[str, Any] | None = None, *,
                   require_clean_tree: bool = True) -> dict[str, Any]:
        """Move a candidate one legal edge, or refuse and leave the log byte-identical.

        Every guard runs before anything is written. The result files (`dev_result.json`,
        `test_result.json`) are written exactly once and only after the full payload has
        been validated, so a refused transition can never leave a half-recorded result
        behind for the next attempt to "confirm".
        """
        entries = self.read_state(candidate_id)
        identity = self.read_identity(candidate_id)
        current = entries[-1]["to"]
        if to not in TRANSITIONS:
            raise IllegalTransition(f"{to!r} is not a state; known: {list(STATES)}")
        legal = TRANSITIONS.get(current, ())
        if to not in legal:
            where = f"legal from {current}: {list(legal)}" if legal else f"{current} is terminal"
            raise IllegalTransition(
                f"{candidate_id}: {current} -> {to} is not a legal transition ({where})")

        code_commit, tree_clean, dirty = tree_state()
        if require_clean_tree and not tree_clean:
            raise TransitionRefused(
                f"{candidate_id}: refusing {current} -> {to} at code_commit "
                f"{code_commit or '(git unavailable)'} (dirty outside the registry: {dirty}) — "
                "a state change that cannot name the exact code that produced it is not "
                "reproducible evidence. Commit first.")

        payload = dict(payload or {})
        stored, side_effects = self._validate_payload(candidate_id, entries, identity,
                                                      current, to, payload)
        for path, obj in side_effects:
            _dump(path, obj)
        return self._append(candidate_id, "transition", current, to, stored,
                            code_commit, tree_clean)

    # -------------------------------------------------------------- payload guards
    def _validate_payload(self, cid: str, entries: list[dict[str, Any]],
                          identity: dict[str, Any], current: str, to: str,
                          payload: dict[str, Any]
                          ) -> tuple[dict[str, Any], list[tuple[Path, Any]]]:
        """Validate `payload` for the edge `current -> to`, fully, before anything is
        written. Returns (payload as it will be logged, files to write)."""
        stored = dict(payload)
        side: list[tuple[Path, Any]] = []
        train = _entry_to(entries, TRAIN_COMPATIBLE)
        contract = _entry_to(entries, CONTRACT_FROZEN)

        if to == TRAIN_COMPATIBLE:
            _require(payload, ("execution_system", "train_run_ids", "pilot_record_digest",
                               "calibration"), to)
            es = _as_execution_system(payload["execution_system"], to)
            if es.artifact_id != identity["artifact_id"] or es.runtime_id != identity["runtime_id"]:
                raise TransitionRefused(
                    f"{cid}: execution system names artifact {es.artifact_id!r} / runtime "
                    f"{es.runtime_id!r}, the candidate is {identity['artifact_id']!r} / "
                    f"{identity['runtime_id']!r}")
            if es.artifact_sha256 != identity["artifact_sha256"] or \
                    es.runtime_digest != identity["runtime_digest"]:
                raise TransitionRefused(
                    f"{cid}: execution system digests do not match the candidate identity")
            runs = payload["train_run_ids"]
            if not isinstance(runs, list) or not runs:
                raise TransitionRefused(f"{cid}: train_run_ids must be a non-empty list")
            off = [r for r in runs if "train" not in str(r).lower()]
            if off:
                raise TransitionRefused(
                    f"{cid}: {off} are not TRAIN run ids (a TRAIN run id must say 'train')")
            if not str(payload["pilot_record_digest"]):
                raise TransitionRefused(f"{cid}: pilot_record_digest must be non-empty")
            if not isinstance(payload["calibration"], dict):
                raise TransitionRefused(f"{cid}: calibration must be an object")
            if "execution_system_digest" in payload and \
                    payload["execution_system_digest"] != es.record_digest:
                raise TransitionRefused(
                    f"{cid}: execution_system_digest in the payload does not digest its own "
                    "execution_system")
            stored["execution_system_digest"] = es.record_digest

        elif to == CONTRACT_FROZEN:
            _require(payload, ("contract_path", "contract_revision", "contract_commit",
                               "gates_digest", "execution_system_digest"), to)
            if not re.fullmatch(r"[0-9a-f]{40}", str(payload["contract_revision"])):
                raise TransitionRefused(
                    f"{cid}: contract_revision must be the 40-hex git blob sha of the contract "
                    f"file, got {payload['contract_revision']!r} — a commit is not a content "
                    "digest, and the contract is what DEV is judged against")
            if not re.fullmatch(r"[0-9a-f]{7,40}", str(payload["contract_commit"])):
                raise TransitionRefused(f"{cid}: contract_commit must be 7-40 hex")
            frozen = (train or {}).get("payload", {}).get("execution_system_digest")
            _require_equal(payload, "execution_system_digest", frozen, cid, to,
                           "the execution system frozen at TRAIN_COMPATIBLE")
            clash = self.family_members(identity["family"], (CONTRACT_FROZEN,) + DEV_OR_BEYOND, cid)
            if clash:
                other, state = clash[0]
                raise TransitionRefused(
                    f"{cid}: candidate {other!r} of family {identity['family']!r} is already at "
                    f"{state} — only ONE quant per family may be frozen for DEV; withdraw the "
                    "loser at TRAIN_COMPATIBLE first (contract § 7)")
            blob = contract_blob_sha(str(payload["contract_path"])) if self.git_checks else payload["contract_revision"]
            if blob != payload["contract_revision"]:
                raise TransitionRefused(
                    f"{cid}: contract_revision {str(payload['contract_revision'])[:12]}… is not the "
                    f"blob committed at HEAD for {payload['contract_path']} ({(blob or '?')[:12]}…) — "
                    "commit the contract, then freeze")

        elif to == DEV_EVALUATED:
            _require(payload, ("dev_run_id", "dev_result", "contract_revision",
                               "execution_system_digest"), to)
            run_id = str(payload["dev_run_id"])
            if "dev" not in run_id.lower():
                raise TransitionRefused(f"{cid}: {run_id!r} is not a DEV run id")
            frozen = (contract or {}).get("payload", {})
            _require_equal(payload, "contract_revision", frozen.get("contract_revision"),
                           cid, to, "the contract frozen at CONTRACT_FROZEN")
            _require_equal(payload, "execution_system_digest",
                           frozen.get("execution_system_digest"), cid, to,
                           "the execution system frozen at TRAIN_COMPATIBLE")
            result = payload["dev_result"]
            if not isinstance(result, dict):
                raise TransitionRefused(f"{cid}: dev_result must be an object")
            path = self.dev_result_file(cid)
            if path.exists():
                raise TransitionRefused(
                    f"{cid}: {path} already exists — DEV is evaluated once, and a second "
                    "result would be a second look at the same split")
            clash = self.family_members(identity["family"], DEV_OR_BEYOND, cid)
            if clash:
                other, state = clash[0]
                raise TransitionRefused(
                    f"{cid}: candidate {other!r} of family {identity['family']!r} is already at "
                    f"{state} — at most ONE quant per family may spend a DEV evaluation, "
                    "otherwise the family gets two draws at the same question")
            dev_runs = self.ledger_run_ids(cid, "dev")
            if dev_runs != [run_id]:
                raise TransitionRefused(
                    f"{cid}: the run ledger records DEV runs {dev_runs} but this transition "
                    f"claims {run_id!r} — exactly one DEV run, and it must be the one that ran")
            self._require_complete_run(cid, run_id, int(payload.get("expected_cases", 48)))
            stored.pop("dev_result", None)
            stored["dev_result_digest"] = digest(result)
            side.append((path, result))

        elif to in (DEV_QUALIFIED, DEV_REJECTED):
            _require(payload, ("gate_evaluation", "gates_digest", "dev_result_digest",
                               "contract_revision"), to)
            if not isinstance(payload["gate_evaluation"], dict):
                raise TransitionRefused(f"{cid}: gate_evaluation must be an object")
            frozen = (contract or {}).get("payload", {})
            _require_equal(payload, "gates_digest", frozen.get("gates_digest"), cid, to,
                           "the gates frozen at CONTRACT_FROZEN")
            _require_equal(payload, "contract_revision", frozen.get("contract_revision"),
                           cid, to, "the contract frozen at CONTRACT_FROZEN")
            self._check_dev_result_digest(cid, entries, payload, to)
            ge = payload["gate_evaluation"]
            wanted = to == DEV_QUALIFIED
            if ge.get("qualified") is not wanted:
                raise TransitionRefused(
                    f"{cid}: gate_evaluation.qualified={ge.get('qualified')!r} does not support "
                    f"{to} — the verdict is the gate function's, not the operator's")
            if ge.get("gates_digest") != frozen.get("gates_digest"):
                raise TransitionRefused(
                    f"{cid}: gate_evaluation was produced under gates {str(ge.get('gates_digest'))[:12]}…, "
                    f"not the frozen {str(frozen.get('gates_digest'))[:12]}…")
            # Re-derive the verdict from the once-written dev_result.json when it carries the
            # gate inputs — the stored evaluation may not disagree with the stored metrics.
            result = json.loads(self.dev_result_file(cid).read_text())
            if isinstance(result, dict) and "metrics" in result and identity.get("role"):
                from fis_platform.r6_gates import evaluate_gates
                recomputed = evaluate_gates(identity["role"], result["metrics"], result.get("reference"))
                if recomputed["qualified"] is not wanted:
                    raise TransitionRefused(
                        f"{cid}: re-applying the frozen gates to dev_result.json gives "
                        f"qualified={recomputed['qualified']}, not {wanted}")

        elif to == TEST_UNLOCKED:
            _require(payload, ("test_run_id", "dev_result_digest", "contract_revision",
                               "execution_system_digest", "artifact_sha256_now"), to)
            run_id = str(payload["test_run_id"])
            if "test" not in run_id.lower() and not run_id.endswith("-96"):
                raise TransitionRefused(f"{cid}: {run_id!r} is not a TEST run id")
            frozen = (contract or {}).get("payload", {})
            _require_equal(payload, "contract_revision", frozen.get("contract_revision"),
                           cid, to, "the contract frozen at CONTRACT_FROZEN")
            _require_equal(payload, "execution_system_digest",
                           frozen.get("execution_system_digest"), cid, to,
                           "the execution system frozen at TRAIN_COMPATIBLE")
            self._check_dev_result_digest(cid, entries, payload, to)
            if payload["artifact_sha256_now"] != identity["artifact_sha256"]:
                raise TransitionRefused(
                    f"{cid}: the artifact now hashes to "
                    f"{str(payload['artifact_sha256_now'])[:12]}… but the candidate was "
                    f"registered on {identity['artifact_sha256'][:12]}… — the file moved under "
                    "the experiment; TEST stays sealed")
            clash = self.family_members(identity["family"], TEST_STATES, cid)
            if clash:
                other, state = clash[0]
                raise TransitionRefused(
                    f"{cid}: candidate {other!r} of family {identity['family']!r} is already at "
                    f"{state} — one TEST look per family")

        elif to == TEST_EVALUATED:
            _require(payload, ("test_run_id", "test_result"), to)
            unlock = _entry_to(entries, TEST_UNLOCKED) or {}
            expected = unlock.get("payload", {}).get("test_run_id")
            _require_equal(payload, "test_run_id", expected, cid, to,
                           "the run id the TEST unlock was spent on")
            result = payload["test_result"]
            if not isinstance(result, dict):
                raise TransitionRefused(f"{cid}: test_result must be an object")
            path = self.test_result_file(cid)
            if path.exists():
                raise TransitionRefused(f"{cid}: {path} already exists — TEST is scored once")
            self._require_complete_run(cid, str(payload["test_run_id"]),
                                       int(payload.get("expected_cases", 96)))
            stored.pop("test_result", None)
            stored["test_result_digest"] = digest(result)
            side.append((path, result))

        elif to == WITHDRAWN:
            _require(payload, ("reason",), to)
            if not str(payload["reason"]).strip():
                raise TransitionRefused(
                    f"{cid}: withdrawing needs a reason — an unexplained disappearance from the "
                    "comparison is indistinguishable from a quietly dropped bad result")

        return stored, side

    def _require_complete_run(self, cid: str, run_id: str, expected_cases: int) -> None:
        """The ledger must hold a start AND an end line for `run_id`, and the end line must
        report every planned case done — a partial DEV/TEST is not an evaluation."""
        lines = [ln for ln in self.read_ledger(cid) if ln.get("run_id") == run_id]
        starts = [ln for ln in lines if ln.get("event") == "start"]
        ends = [ln for ln in lines if ln.get("event") == "end"]
        if not starts:
            raise TransitionRefused(f"{cid}: no ledger start line for {run_id!r}")
        if not ends:
            raise TransitionRefused(f"{cid}: run {run_id!r} has no ledger end line — it did not finish")
        done = sum(int(e.get("cases_done", 0)) for e in ends)   # a resumed run ends more than once
        planned = int(starts[0].get("planned_cases", 0))
        if done != expected_cases or planned != expected_cases:
            raise TransitionRefused(
                f"{cid}: run {run_id!r} planned {planned} and completed {done} cases; "
                f"a full evaluation is {expected_cases} — partial runs are not recorded as results")

    def _check_dev_result_digest(self, cid: str, entries: list[dict[str, Any]],
                                 payload: dict[str, Any], to: str) -> None:
        """The claimed DEV digest must match BOTH the file on disk (recomputed now) and
        the digest logged at DEV_EVALUATED — the two together catch a rewritten file and
        a mis-quoted digest separately."""
        path = self.dev_result_file(cid)
        if not path.exists():
            raise TransitionRefused(f"{cid}: {path} does not exist — nothing to judge")
        recomputed = digest(json.loads(path.read_text()))
        logged = (_entry_to(entries, DEV_EVALUATED) or {}).get("payload", {}).get(
            "dev_result_digest")
        if recomputed != logged:
            raise RegistryIntegrityError(
                f"{cid}: {path} digests to {recomputed[:12]}… but DEV_EVALUATED logged "
                f"{str(logged)[:12]}… — the DEV result was rewritten after it was recorded")
        _require_equal(payload, "dev_result_digest", recomputed, cid, to,
                       "the DEV result on disk")


def _require(payload: dict[str, Any], keys: tuple[str, ...], to: str) -> None:
    missing = [k for k in keys if k not in payload]
    if missing:
        raise TransitionRefused(f"{to} payload is missing {missing}")


def _require_equal(payload: dict[str, Any], key: str, expected: Any, cid: str, to: str,
                   what: str) -> None:
    got = payload.get(key)
    if got != expected:
        raise TransitionRefused(
            f"{cid}: {to} payload {key}={_short(got)} does not equal {what} "
            f"({_short(expected)}) — refusing")


def _short(value: Any) -> str:
    text = str(value)
    return repr(text if len(text) <= 20 else text[:12] + "…")


def _as_execution_system(raw: Any, to: str) -> ExecutionSystem:
    if not isinstance(raw, dict):
        raise TransitionRefused(f"{to} payload execution_system must be an object")
    try:
        return ExecutionSystem(**raw).verify()      # type: ignore[return-value]
    except ValueError as exc:
        raise TransitionRefused(f"{to} payload execution_system does not verify: {exc}") from exc


# ------------------------------------------------------------------ runner interface

_SPLITS = ("train", "dev", "test")
RUN_KINDS = ("eval", "diagnostic")

# The one M0-authorized extension (docs/current/NEXT_STEP_M0.md § 5): states a
# `diagnostic` run may execute in. TRAIN's states, PLUS the terminal TEST_EVALUATED —
# because the question a diagnostic answers ("why did the frozen system truncate?")
# only exists once the system is frozen and evaluated. Nothing in between: a
# diagnostic at DEV_EVALUATED/TEST_UNLOCKED would be a side-channel look while a
# split decision is still open, which is exactly what the machine forbids.
DIAGNOSTIC_STATES = (REGISTERED, TRAIN_COMPATIBLE, CONTRACT_FROZEN, TEST_EVALUATED)


def require_state(registry: R6Registry, candidate_id: str, split: str, run_id: str,
                  resume: bool = False, *, kind: str = "eval",
                  purpose: str | None = None) -> dict[str, Any]:
    """The runner's fail-closed precondition, called BEFORE any model is loaded.

    This is the only thing standing between "the harness is configured wrong" and a TEST
    look nobody meant to spend. It is a pure read: it verifies the chain, checks the
    state and the ledger, and returns the identity plus the frozen execution system for
    the caller to stamp into every trajectory's runtime_context. It writes nothing, so
    calling it twice costs nothing.

      train  REGISTERED / TRAIN_COMPATIBLE / CONTRACT_FROZEN (a stability probe after
             the freeze is still TRAIN, so it stays legal)
      dev    CONTRACT_FROZEN exactly — before the freeze there is nothing to be judged
             against, after DEV_EVALUATED the split is spent
      test   TEST_UNLOCKED exactly, on the run id the unlock was spent on

    kind="diagnostic" (M0, docs/current/NEXT_STEP_M0.md § 5): TRAIN-split-only,
    additionally permitted at the terminal TEST_EVALUATED, mandatory non-empty
    `purpose`, run id must say "diag". Recorded through begin_run/end_run as ledger
    lines only — no state transition, no chain entry, no effect on promotability.
    """
    if split not in _SPLITS:
        raise TransitionRefused(f"split must be one of {list(_SPLITS)}, got {split!r}")
    if kind not in RUN_KINDS:
        raise TransitionRefused(f"run kind must be one of {list(RUN_KINDS)}, got {kind!r}")
    if kind == "diagnostic":
        if split != "train":
            raise TransitionRefused(
                f"diagnostic runs are TRAIN-only (got split {split!r}) — a diagnostic that "
                "touched DEV or TEST would be an unledgered look at a decision split")
        if not (isinstance(purpose, str) and purpose.strip()):
            raise TransitionRefused(
                "diagnostic runs require a non-empty purpose tag (e.g. 'M0-truncation-diag') "
                "— an unexplained diagnostic is indistinguishable from an unrecorded rerun")
        if "diag" not in run_id.lower():
            raise TransitionRefused(
                f"diagnostic run id {run_id!r} must say 'diag' — run ids are how the ledger "
                "tells run kinds apart")
    entries = registry.read_state(candidate_id)
    identity = registry.read_identity(candidate_id)
    state = entries[-1]["to"]

    if split == "test":
        shaped = "test" in run_id.lower() or run_id.endswith("-96")
    else:
        shaped = split in run_id.lower()
    if not shaped:
        raise TransitionRefused(
            f"run id {run_id!r} does not name its split ({split}) — run ids are how the ledger "
            "and every later report tell splits apart")
    for line in registry.read_ledger():
        if line.get("run_id") == run_id and line.get("candidate_id") != candidate_id:
            raise TransitionRefused(
                f"run id {run_id!r} is already recorded for candidate "
                f"{line.get('candidate_id')!r} — one run id, one candidate")

    if split in ("dev", "test"):
        problems = registry_ahead_of_git_only_by_appends() if registry.git_checks else []
        if problems:
            raise TransitionRefused(
                "registry files are not append-only relative to the committed tree: "
                f"{problems} — a reset (git checkout/stash, truncation) is not a legal state")
        clash = registry.family_members(identity["family"], (CONTRACT_FROZEN,) + DEV_OR_BEYOND,
                                        candidate_id)
        for other, _st in clash:
            raise TransitionRefused(
                f"{candidate_id}: {other!r} of family {identity['family']!r} is at {_st} — one "
                "quant per family reaches DEV/TEST")
        for other in registry.candidate_ids():
            if other != candidate_id and registry.read_identity(other).get("family") == identity["family"]:
                if registry.ledger_run_ids(other, split):
                    raise TransitionRefused(
                        f"{candidate_id}: {other!r} of the same family already has a {split} run "
                        "in the ledger")
    if split == "train":
        if kind == "diagnostic":
            if state not in DIAGNOSTIC_STATES:
                raise TransitionRefused(
                    f"{candidate_id} is at {state}: diagnostic TRAIN inference is allowed "
                    f"only at {list(DIAGNOSTIC_STATES)} — no non-terminal DEV/TEST state "
                    "may be bypassed")
        elif state not in (REGISTERED, TRAIN_COMPATIBLE, CONTRACT_FROZEN):
            raise TransitionRefused(
                f"{candidate_id} is at {state}: TRAIN inference is allowed only at "
                f"{[REGISTERED, TRAIN_COMPATIBLE, CONTRACT_FROZEN]}")
    elif split == "dev":
        if state != CONTRACT_FROZEN:
            raise TransitionRefused(
                f"{candidate_id} is at {state}, not {CONTRACT_FROZEN}: DEV runs only against a "
                "frozen contract, and only once")
        prior = registry.ledger_run_ids(candidate_id, "dev")
        if prior and not (resume and prior == [run_id]):
            raise TransitionRefused(
                f"{candidate_id} has already run DEV as {prior} — a second DEV run is a second "
                "look at the selection split (pass resume=True only to finish the SAME run id)")
    else:
        if state != TEST_UNLOCKED:
            raise TransitionRefused(
                f"{candidate_id} is at {state}, not {TEST_UNLOCKED}: TEST is sealed until the "
                "unlock is recorded")
        unlock = _entry_to(entries, TEST_UNLOCKED) or {}
        expected = unlock.get("payload", {}).get("test_run_id")
        if run_id != expected:
            raise TransitionRefused(
                f"{candidate_id}: the TEST unlock was spent on {expected!r}, not {run_id!r}")
        prior = registry.ledger_run_ids(candidate_id, "test")
        if prior and not (resume and prior == [run_id]):
            raise TransitionRefused(
                f"{candidate_id} has already run TEST as {prior} — exactly once")

    execution_system = (_entry_to(entries, TRAIN_COMPATIBLE) or {}).get("payload", {}).get(
        "execution_system")
    contract = (_entry_to(entries, CONTRACT_FROZEN) or {}).get("payload", {})
    if split in ("dev", "test") and contract.get("contract_revision") and registry.git_checks:
        if not committed_contract_extends(contract["contract_revision"], contract.get("contract_path", "docs/R6_EXPERIMENT_CONTRACT.md")):
            raise TransitionRefused(
                f"{candidate_id}: the contract committed at HEAD is not the frozen revision "
                f"{contract['contract_revision'][:12]}… (or that revision plus appended § 17 "
                "amendments) — the rules changed after the freeze")
    prior_start = None
    if resume:
        for ln in registry.read_ledger(candidate_id):
            if ln.get("run_id") == run_id and ln.get("event") == "start":
                prior_start = ln
    return {
        "prior_start": prior_start,
        "candidate_id": candidate_id,
        "state": state,
        "split": split,
        "run_id": run_id,
        "resume": bool(resume),
        "kind": kind,
        "purpose": purpose,
        "identity": identity,
        "execution_system": execution_system,
        "execution_system_digest": (execution_system or {}).get("record_digest"),
        "contract_revision": contract.get("contract_revision"),
        "gates_digest": contract.get("gates_digest"),
    }


def begin_run(registry: R6Registry, candidate_id: str, split: str, run_id: str,
              planned_cases: int, extra: dict[str, Any] | None = None, *,
              kind: str = "eval", purpose: str | None = None) -> dict[str, Any]:
    """Record that a run STARTED, in both the candidate's chain and the global ledger.

    Both, not one: the chain says what this candidate has done, and the ledger is what
    the DEV/TEST "exactly once" guards read — a run that dies mid-way still leaves its
    start line, which is what makes an unnoticed second attempt impossible.
    Call `require_state` first; this does not re-derive the split rules.

    kind="diagnostic" (M0): the run is recorded in the GLOBAL LEDGER ONLY, tagged with
    its kind and mandatory purpose. No chain entry is appended, so the candidate's
    state log and HEAD.json stay byte-identical — a diagnostic observes a frozen
    system, it is not an event in that system's history of decisions
    (docs/current/NEXT_STEP_M0.md § 5/§ 8: HEAD/state byte-identical across M0's runs).
    """
    if kind not in RUN_KINDS:
        raise TransitionRefused(f"run kind must be one of {list(RUN_KINDS)}, got {kind!r}")
    entries = registry.read_state(candidate_id)
    state = entries[-1]["to"]
    started_at = _now()
    code_commit, tree_clean, _ = tree_state()
    if kind == "diagnostic":
        if not (isinstance(purpose, str) and purpose.strip()):
            raise TransitionRefused(
                "diagnostic runs require a non-empty purpose tag (e.g. 'M0-truncation-diag')")
        line = {"candidate_id": candidate_id, "split": split, "run_id": run_id,
                "event": "start", "run_kind": "diagnostic", "purpose": purpose,
                "planned_cases": planned_cases, "started_at": started_at,
                "code_commit": code_commit, "state_at_run": state}
        if extra and extra.get("local_server_session"):
            line["local_server_session"] = str(extra["local_server_session"])
        _append_line(registry.ledger_file, line)
        return line
    payload = {"split": split, "run_id": run_id, "planned_cases": planned_cases,
               "started_at": started_at, **(extra or {})}
    entry = registry._append(candidate_id, "run", state, state, payload, code_commit, tree_clean)
    line = {"candidate_id": candidate_id, "split": split, "run_id": run_id, "event": "start",
            "planned_cases": planned_cases, "started_at": started_at, "code_commit": code_commit}
    if extra and extra.get("local_server_session"):
        line["local_server_session"] = str(extra["local_server_session"])   # resume must not mix sessions
    _append_line(registry.ledger_file, line)
    return entry


def end_run(registry: R6Registry, candidate_id: str, run_id: str, cases_done: int,
            wall_s: float, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """The run's second ledger line. Nothing is edited — a finished run is a start line
    plus an end line, so an interrupted run stays visible as a start with no end."""
    starts = [ln for ln in registry.read_ledger(candidate_id)
              if ln.get("run_id") == run_id and ln.get("event") == "start"]
    if not starts:
        raise TransitionRefused(
            f"{candidate_id}: no start line for run {run_id!r} — a run cannot end before it began")
    line = {"candidate_id": candidate_id, "split": starts[-1].get("split"), "run_id": run_id,
            "event": "end", "cases_done": cases_done, "wall_s": round(float(wall_s), 3),
            "finished_at": _now(), "code_commit": git_head(), **(extra or {})}
    if starts[-1].get("run_kind"):        # a diagnostic's end line names its kind too
        line["run_kind"] = starts[-1]["run_kind"]
        if starts[-1].get("purpose"):
            line["purpose"] = starts[-1]["purpose"]
    _append_line(registry.ledger_file, line)
    return line
