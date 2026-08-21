"""`TrainedArtifact` — the provenance record for a self-produced weights file (master
plan §9 field list; M_STAT_IMPLEMENTATION_MAP.md §10; FT-rig prerequisite for R8).

Schema/provenance work only: nothing here trains anything, and no record is ever
written into `learning/registry/r6` — every registry here is a temporary one under
`tmp_path`, exactly like `test_r6_state_machine.py`.

What each group defends:

  record    the pydantic shape: content-addressed `artifact_id`, "at least one of
            adapter/merged", the 64-hex digest fields, self-digesting `verify()`
            (the `_Record` idiom every other provenance record in this module uses).
  registry  `put_trained_artifact` refuses a lineage that does not resolve: the base
            artifact must already be REGISTERED, and every claimed-compatible
            runtime must already be registered too — the same discipline
            `register_candidate` applies to artifact/runtime before binding.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.provenance import (
    ModelArtifact,
    R6Registry,
    RegistryIntegrityError,
    RuntimeIdentity,
    TrainedArtifact,
    TransitionRefused,
)


@pytest.fixture
def reg(tmp_path: Path) -> R6Registry:
    return R6Registry(tmp_path / "registry", git_checks=False)


def _base_artifact(tmp_path: Path, slug: str = "qwen35-9b-q4km") -> ModelArtifact:
    blob = f"weights-of-{slug}".encode()
    path = tmp_path / f"{slug}.gguf"
    path.write_bytes(blob)
    return ModelArtifact(
        slug=slug, role="modern_small", family="qwen35.9b",
        base_model_repo="base/qwen35.9b", quantizer_or_derivative_repo="unsloth/x",
        source_revision="99a1b218", source_url=f"https://example/{slug}.gguf",
        filename=path.name, quantization="Q4_K_M", size_bytes=len(blob),
        sha256=hashlib.sha256(blob).hexdigest(), gguf_metadata_digest="b" * 64,
        license="apache-2.0", license_source="gguf", architecture="qwen35",
        base_model_lineage="Qwen3.5-9B", local_path=str(path),
    )


def _runtime() -> RuntimeIdentity:
    return RuntimeIdentity(engine="llama.cpp-upstream",
                           git_rev="9b05354ec6fb58b4e665e9a39ebc40285c015638",
                           binaries={"llama-server": "c" * 64},
                           registered_at="2026-08-18T00:00:00+00:00")


def _trained(**over: Any) -> TrainedArtifact:
    fields: dict[str, Any] = {
        "slug": "ft-probe", "base_artifact_id": "qwen35-9b-q4km@" + "a" * 12,
        "dataset_digest": "a" * 64,
        "dataset_provenance": "own-trace: local-model trajectories from R6-x-train, "
                              "scored against FIS's own ground truth",
        "training_method": "qlora", "hyperparameters": {"lr": 2e-4, "epochs": 1},
        "seeds": [42], "adapter_sha256": "b" * 64, "merged_sha256": None,
        "training_pipeline_digest": "c" * 64, "conversion_pipeline_digest": None,
        "quantization": None, "quantization_config": None,
        "result_sha256": "d" * 64, "result_filename": "adapter.safetensors",
        "size_bytes": 12345, "compatible_runtime_ids": ["llama.cpp-upstream-9b05354@" + "e" * 12],
    }
    fields.update(over)
    return TrainedArtifact(**fields)


# ------------------------------------------------------------------ (a) the record shape

def test_artifact_id_is_derived_from_slug_and_result_sha256():
    rec = _trained()
    assert rec.artifact_id == "ft-probe@" + "d" * 12
    with pytest.raises(ValueError, match="artifact_id"):
        _trained(artifact_id="something-else@000000000000")


def test_at_least_one_of_adapter_or_merged_is_required():
    with pytest.raises(ValueError, match="at least one of adapter_sha256 or merged_sha256"):
        _trained(adapter_sha256=None, merged_sha256=None)
    # either alone is fine
    assert _trained(adapter_sha256=None, merged_sha256="f" * 64).artifact_id
    assert _trained(adapter_sha256="b" * 64, merged_sha256=None).artifact_id
    # both is fine too
    assert _trained(adapter_sha256="b" * 64, merged_sha256="f" * 64).artifact_id


@pytest.mark.parametrize("field, value", [
    ("dataset_digest", "not-hex"),
    ("dataset_digest", "a" * 63),
    ("adapter_sha256", "not-hex"),
    ("merged_sha256", "not-hex"),
    ("result_sha256", "z" * 64),
])
def test_hex_digest_fields_are_shape_checked(field, value):
    with pytest.raises(ValueError):
        _trained(**{field: value})


def test_seeds_must_be_a_non_empty_list():
    with pytest.raises(ValueError):
        _trained(seeds=[])


def test_base_artifact_id_and_dataset_provenance_must_be_non_empty():
    with pytest.raises(ValueError):
        _trained(base_artifact_id="")
    with pytest.raises(ValueError):
        _trained(dataset_provenance="")


def test_compatible_runtime_ids_must_be_a_non_empty_list():
    with pytest.raises(ValueError):
        _trained(compatible_runtime_ids=[])


def test_size_bytes_must_be_positive():
    with pytest.raises(ValueError):
        _trained(size_bytes=0)


def test_extra_fields_are_forbidden():
    with pytest.raises(ValueError):
        _trained(unexpected_field="nope")


def test_verify_detects_tampering():
    rec = _trained()
    rec.verify()
    rec.training_method = "full-finetune"
    with pytest.raises(ValueError, match="record_digest"):
        rec.verify()


def test_a_record_loaded_from_json_keeps_the_digest_it_was_written_with():
    original = _trained()
    payload = original.model_dump(mode="json")
    assert TrainedArtifact(**payload).verify() is not None
    payload["notes"] = "quietly edited"
    with pytest.raises(ValueError, match="record_digest"):
        TrainedArtifact(**payload).verify()


# ------------------------------------------------------------------ (b) registry lineage

def test_put_trained_artifact_refuses_an_unregistered_base_artifact(reg, tmp_path):
    rec = _trained()
    with pytest.raises(TransitionRefused, match="does not name a registered artifact"):
        reg.put_trained_artifact(rec)


def test_put_trained_artifact_refuses_an_unregistered_compatible_runtime(reg, tmp_path):
    base = _base_artifact(tmp_path)
    reg.put_artifact(base)
    rec = _trained(base_artifact_id=base.artifact_id)
    with pytest.raises(TransitionRefused, match="no runtime record"):
        reg.put_trained_artifact(rec)


def test_put_trained_artifact_succeeds_once_lineage_resolves(reg, tmp_path):
    base = _base_artifact(tmp_path)
    reg.put_artifact(base)
    runtime = _runtime()
    reg.put_runtime(runtime)
    rec = _trained(base_artifact_id=base.artifact_id, compatible_runtime_ids=[runtime.runtime_id])
    path = reg.put_trained_artifact(rec)
    assert path.exists()
    got = reg.get_trained_artifact(rec.artifact_id)
    assert got.artifact_id == rec.artifact_id
    assert got.base_artifact_id == base.artifact_id
    assert got.compatible_runtime_ids == [runtime.runtime_id]


def test_put_trained_artifact_is_idempotent_for_the_identical_record(reg, tmp_path):
    base = _base_artifact(tmp_path)
    reg.put_artifact(base)
    runtime = _runtime()
    reg.put_runtime(runtime)
    rec = _trained(base_artifact_id=base.artifact_id, compatible_runtime_ids=[runtime.runtime_id])
    reg.put_trained_artifact(rec)
    reg.put_trained_artifact(rec)                     # same bytes: no error


def test_put_trained_artifact_refuses_to_silently_overwrite_a_different_record(reg, tmp_path):
    base = _base_artifact(tmp_path)
    reg.put_artifact(base)
    runtime = _runtime()
    reg.put_runtime(runtime)
    rec = _trained(base_artifact_id=base.artifact_id, compatible_runtime_ids=[runtime.runtime_id])
    reg.put_trained_artifact(rec)
    changed = _trained(base_artifact_id=base.artifact_id,
                       compatible_runtime_ids=[runtime.runtime_id], notes="re-labelled")
    with pytest.raises(RegistryIntegrityError, match="refusing to overwrite"):
        reg.put_trained_artifact(changed)


def test_get_trained_artifact_refuses_an_unknown_id(reg, tmp_path):
    with pytest.raises(RegistryIntegrityError, match="no trained artifact record"):
        reg.get_trained_artifact("nope@000000000000")


def test_trained_dir_lives_under_the_registry_root_not_the_canonical_tree(reg, tmp_path):
    assert reg.trained_dir == reg.root / "trained"
    assert "learning/registry/r6" not in str(reg.trained_dir)


# ------------------------------------------------------------------ (c) CLI

def test_cli_register_trained_artifact_and_show(reg, tmp_path):
    from scripts import r6_registry

    base = _base_artifact(tmp_path)
    reg.put_artifact(base)
    runtime = _runtime()
    reg.put_runtime(runtime)
    rec = _trained(base_artifact_id=base.artifact_id, compatible_runtime_ids=[runtime.runtime_id])
    payload_path = tmp_path / "trained.json"
    payload_path.write_text(rec.model_dump_json())

    ns = r6_registry.build_parser().parse_args(
        ["register-trained-artifact", "--json", str(payload_path)])
    assert ns.func(ns, reg) == 0
    got = reg.get_trained_artifact(rec.artifact_id)
    assert got.artifact_id == rec.artifact_id

    show_ns = r6_registry.build_parser().parse_args(["show", "--trained", rec.artifact_id])
    assert show_ns.func(show_ns, reg) == 0
