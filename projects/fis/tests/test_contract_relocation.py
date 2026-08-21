"""The R6 contract provenance-relocation mechanism (owner decision D6, 2026-08-21).

The 2026-08 repository restructuring moved the frozen R6 contract — byte-identical,
pure `git mv` — from its freeze-time path `docs/R6_EXPERIMENT_CONTRACT.md` to the FIS
project boundary at `projects/fis/R6_EXPERIMENT_CONTRACT.md`. The hash-chained
CONTRACT_FROZEN payloads seal the historical locator and can never be rewritten;
`provenance.CONTRACT_PATH_RELOCATIONS` is the explicit, audited, one-hop mapping the
verifier uses to find the same bytes at their current canonical location.

These tests are the required demonstrations for that mechanism, run against the REAL
committed registry and git history (read-only — nothing here writes, transitions, or
consumes a look):

  * the sealed historical payload still verifies end-to-end through relocation;
  * the frozen blob still byte-prefix-extends the moved contract at HEAD;
  * the old path is gone; the new path carries the identical blob;
  * GATES and its digest are byte-unchanged (the digested historical path string
    included);
  * unknown relocations fail closed;
  * substituting the relocation target fails verification (content binds, not path);
  * a wrong frozen blob fails verification (content binds, not location);
  * canonical paths pass through the resolver untouched — new freezes never depend
    on relocation logic.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIS_ROOT))

from fis_platform import provenance  # noqa: E402
from fis_platform.r6_gates import GATES, GATES_DIGEST  # noqa: E402

HISTORICAL_LOCATOR = "docs/R6_EXPERIMENT_CONTRACT.md"
CANONICAL = provenance.R6_CONTRACT_PATH


def _sealed_contract_frozen() -> dict:
    """The CONTRACT_FROZEN payload of a real, terminal R6 candidate — sealed data."""
    state = (FIS_ROOT / "learning" / "registry" / "r6" / "candidates"
             / "bonsai-27b@ddd13c20e0e8" / "state.jsonl")
    for line in state.read_text().splitlines():
        entry = json.loads(line)
        if entry.get("to") == "CONTRACT_FROZEN":
            return entry["payload"]
    raise AssertionError("no CONTRACT_FROZEN entry in the committed bonsai state log")


def _head_blob(path: str) -> str:
    return subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=10,
                          check=True).stdout.strip()


def test_sealed_payload_verifies_through_relocation():
    sealed = _sealed_contract_frozen()
    assert sealed["contract_path"] == HISTORICAL_LOCATOR   # the record is untouched
    assert provenance.committed_contract_extends(
        sealed["contract_revision"], sealed["contract_path"]) is True


def test_old_path_gone_new_path_carries_the_identical_blob():
    assert not (REPO_ROOT / HISTORICAL_LOCATOR).exists()
    assert (REPO_ROOT / CANONICAL).exists()
    # the resolver maps the sealed locator onto the same committed blob
    assert provenance.contract_blob_sha(HISTORICAL_LOCATOR) == _head_blob(CANONICAL)
    # and the frozen revision is a byte-prefix of that blob's content (§ 17 appends only)
    sealed = _sealed_contract_frozen()
    frozen_bytes = subprocess.run(["git", "cat-file", "-p", sealed["contract_revision"]],
                                  cwd=REPO_ROOT, capture_output=True, timeout=10,
                                  check=True).stdout
    assert (REPO_ROOT / CANONICAL).read_bytes().startswith(frozen_bytes)


def test_gates_and_their_digest_are_byte_unchanged():
    sealed = _sealed_contract_frozen()
    assert GATES_DIGEST == sealed["gates_digest"]
    # the digested dict still carries the historical path string as sealed data
    assert GATES["contract"] == "docs/R6_EXPERIMENT_CONTRACT.md § 11"


def test_unknown_relocation_fails_closed():
    ghost = "docs/NO_SUCH_CONTRACT.md"
    assert provenance.resolve_contract_path(ghost) == ghost          # no search fallback
    assert provenance.contract_blob_sha(ghost) is None
    sealed = _sealed_contract_frozen()
    assert provenance.committed_contract_extends(sealed["contract_revision"], ghost) is False


def test_relocation_target_substitution_fails_verification(monkeypatch):
    # An attacker (or a careless migration) re-points the mapping at another committed
    # file: the frozen blob no longer prefixes the resolved content -> refused.
    monkeypatch.setitem(provenance.CONTRACT_PATH_RELOCATIONS, HISTORICAL_LOCATOR,
                        "projects/fis/SUITE_V3_RELEASE_CONTRACT.md")
    sealed = _sealed_contract_frozen()
    assert provenance.committed_contract_extends(
        sealed["contract_revision"], HISTORICAL_LOCATOR) is False


def test_wrong_frozen_blob_fails_verification():
    # Content binding, independent of location: a blob of some other committed file
    # does not prefix the contract at the canonical path.
    other_blob = _head_blob("projects/fis/SUITE_V3_RELEASE_CONTRACT.md")
    assert provenance.committed_contract_extends(other_blob, CANONICAL) is False


def test_canonical_paths_pass_through_untouched():
    # New/current freezes record canonical paths; the resolver must be identity for
    # them — relocation is only for audited historical locators.
    assert provenance.resolve_contract_path(CANONICAL) == CANONICAL
    assert provenance.contract_blob_sha() == _head_blob(CANONICAL)   # default is canonical
    for target in provenance.CONTRACT_PATH_RELOCATIONS.values():
        assert target not in provenance.CONTRACT_PATH_RELOCATIONS    # one hop, no chains
