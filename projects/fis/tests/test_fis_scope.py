"""Scoped FIS clean-tree semantics (owner decision D3, 2026-08-21).

Since the 2026-08 restructuring the FIS project lives inside the Adaptive AI Lab
monorepo at projects/fis/. Its provenance dependency closure — code, registries,
tracked evidence, infra, project docs, the relocated R6 contract, the TEST-look
mirror — is entirely inside that tree, so:

    fis_tree_clean  = no unsanctioned changes inside the FIS tree
    fis_dirty_paths = unsanctioned modified paths inside the FIS tree
    -dirty          = stamped iff tracked modifications exist inside the FIS tree

Uncommitted edits elsewhere in the lab (playbook/, research/, lab governance) must
NOT make an unchanged FIS execution system read as scientifically dirty; edits
inside the FIS tree must still refuse/stamp exactly as before. Both
`suite.git_head()` and `provenance.dirty_paths_outside_registry()` use the same
`-- .` pathspec under their package root, so the recorded commit identity and the
dirty-path guard cannot disagree.

These tests run against REAL git in a temporary repository shaped like the lab
(`<repo>/playbook/…` beside `<repo>/projects/fis/…`), monkeypatching only the
modules' `_ROOT` anchor — no fake subprocess, no live-repo mutation.
"""

import subprocess
import sys
from pathlib import Path

FIS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIS_ROOT))

from fis_platform import provenance, suite  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          cwd=repo, capture_output=True, text=True, timeout=10,
                          check=True).stdout


def _lab_repo(tmp_path: Path) -> Path:
    """A minimal lab-shaped repo: lab-level file + FIS tree + registry bookkeeping."""
    repo = tmp_path / "lab"
    fis = repo / "projects" / "fis"
    (fis / "learning" / "registry" / "r6").mkdir(parents=True)
    (repo / "playbook").mkdir()
    (repo / "playbook" / "00_CHAPTER.md").write_text("generic method\n")
    (fis / "module.py").write_text("x = 1\n")
    (fis / "learning" / "registry" / "r6" / "ledger.jsonl").write_text('{"seq": 1}\n')
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")
    return repo


def _scoped(monkeypatch, repo: Path):
    fis = repo / "projects" / "fis"
    monkeypatch.setattr(provenance, "_ROOT", fis)
    monkeypatch.setattr(suite, "_ROOT", fis)
    return fis


def test_lab_edits_outside_the_fis_tree_do_not_dirty_fis(tmp_path, monkeypatch):
    repo = _lab_repo(tmp_path)
    _scoped(monkeypatch, repo)
    (repo / "playbook" / "00_CHAPTER.md").write_text("edited generic method\n")   # tracked edit
    (repo / "NOTES.md").write_text("untracked lab scratch\n")                     # untracked file
    assert provenance.dirty_paths_outside_registry() == []
    head = suite.git_head()
    assert head and not head.endswith("-dirty")
    commit, clean, dirty = provenance.tree_state()
    assert clean is True and dirty == [] and not commit.endswith("-dirty")


def test_edits_inside_the_fis_tree_still_refuse_and_stamp_dirty(tmp_path, monkeypatch):
    repo = _lab_repo(tmp_path)
    fis = _scoped(monkeypatch, repo)
    (fis / "module.py").write_text("x = 2\n")                                     # tracked edit
    assert provenance.dirty_paths_outside_registry() == ["projects/fis/module.py"]
    assert suite.git_head().endswith("-dirty")
    _commit, clean, dirty = provenance.tree_state()
    assert clean is False and dirty == ["projects/fis/module.py"]


def test_untracked_files_inside_the_fis_tree_count_as_dirty_paths(tmp_path, monkeypatch):
    repo = _lab_repo(tmp_path)
    fis = _scoped(monkeypatch, repo)
    (fis / "scratch.json").write_text("{}\n")
    # untracked inside scope: refused by the run guard (untracked-files=all) even
    # though the telemetry head (untracked-files=no) stays undecorated — tree_state
    # reconciles in the fail-closed direction.
    assert provenance.dirty_paths_outside_registry() == ["projects/fis/scratch.json"]
    _commit, clean, dirty = provenance.tree_state()
    assert clean is False and dirty == ["projects/fis/scratch.json"]


def test_registry_bookkeeping_is_still_sanctioned(tmp_path, monkeypatch):
    repo = _lab_repo(tmp_path)
    fis = _scoped(monkeypatch, repo)
    ledger = fis / "learning" / "registry" / "r6" / "ledger.jsonl"
    ledger.write_text(ledger.read_text() + '{"seq": 2}\n')                        # append
    assert provenance.dirty_paths_outside_registry() == []
    # the head is -dirty (the ledger is tracked) but every dirty path is bookkeeping:
    commit, clean, dirty = provenance.tree_state()
    assert clean is True and dirty == [] and commit.endswith("-dirty")


def test_scope_is_the_whole_repo_when_fis_is_the_repo_root(tmp_path, monkeypatch):
    # Future extraction shape: projects/fis/ becomes its own repository root — the
    # pathspec scope then IS the whole repo and nothing weakens.
    repo = tmp_path / "fis-standalone"
    (repo / "learning" / "registry" / "r6").mkdir(parents=True)
    (repo / "module.py").write_text("x = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")
    monkeypatch.setattr(provenance, "_ROOT", repo)
    monkeypatch.setattr(suite, "_ROOT", repo)
    (repo / "module.py").write_text("x = 2\n")
    assert provenance.dirty_paths_outside_registry() == ["module.py"]
    assert suite.git_head().endswith("-dirty")
