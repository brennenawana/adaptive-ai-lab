"""Workspace layers: wiki/ (persistent, never rolled back), skills/ (gated),
raw/ (immutable traces). File names match the paper's App. E.2 wiki structure."""

import difflib
import re
import shutil
from pathlib import Path

INDEX_SEED = "# Pattern Index\n\n(no patterns yet)\n"
LOG_SEED = "# Evolution Log\n"
IMPACT_SEED = "# Skill Impact History\n"


def init_workspace(run_dir: Path) -> None:
    (run_dir / "wiki" / "patterns").mkdir(parents=True, exist_ok=True)
    (run_dir / "skills").mkdir(exist_ok=True)
    (run_dir / "raw").mkdir(exist_ok=True)
    (run_dir / "workdirs").mkdir(exist_ok=True)
    for name, seed in [("index.md", INDEX_SEED), ("log.md", LOG_SEED),
                       ("skill-impact.md", IMPACT_SEED)]:
        p = run_dir / "wiki" / name
        if not p.exists():
            p.write_text(seed)


def wiki_context(run_dir: Path) -> str:
    parts = []
    for rel in ["wiki/index.md", "wiki/log.md"]:
        parts.append(f"=== {rel} ===\n{(run_dir / rel).read_text()}")
    for p in sorted((run_dir / "wiki" / "patterns").glob("*.md")):
        parts.append(f"=== wiki/patterns/{p.name} ===\n{p.read_text()}")
    return "\n\n".join(parts)


def _safe_name(name: str, suffix: str = ".md") -> str:
    name = Path(name).name
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
    if not name.endswith(suffix):
        name += suffix
    return name


def apply_patch_ops(text: str, edits: list) -> tuple[str, list]:
    notes = []
    for e in edits or []:
        op = e.get("op")
        content = e.get("content", "")
        target = e.get("target", "")
        if op == "append":
            text = text.rstrip("\n") + "\n" + content + "\n"
        elif op == "replace":
            if target and target in text:
                text = text.replace(target, content, 1)
            else:
                notes.append(f"replace target not found: {target[:60]!r}")
        elif op == "insert_after":
            if target and target in text:
                i = text.index(target) + len(target)
                text = text[:i] + "\n" + content + text[i:]
            else:
                notes.append(f"insert_after target not found: {target[:60]!r}")
        else:
            notes.append(f"unknown op: {op!r}")
    return text, notes


def apply_maintainer_ops(run_dir: Path, ops: dict, iteration: int) -> list:
    notes = []
    pat_dir = run_dir / "wiki" / "patterns"
    for item in ops.get("create_patterns") or []:
        name = _safe_name(item.get("name", "unnamed"))
        (pat_dir / name).write_text(item.get("content", ""))
    for item in ops.get("update_patterns") or []:
        name = _safe_name(item.get("name", ""))
        p = pat_dir / name
        if not p.exists():
            notes.append(f"update target missing: {name}")
            continue
        text, n = apply_patch_ops(p.read_text(), item.get("edits"))
        p.write_text(text)
        notes.extend(n)
    if isinstance(ops.get("update_index"), str):
        (run_dir / "wiki" / "index.md").write_text(ops["update_index"])
    if isinstance(ops.get("append_log"), str):
        with (run_dir / "wiki" / "log.md").open("a") as f:
            f.write(f"\n## [iter {iteration}] {ops['append_log']}\n")
    return notes


# --- skills layer ------------------------------------------------------------

def skills_text(skills_dir: Path) -> str:
    parts = []
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        md = d / "SKILL.md"
        if md.exists():
            parts.append(f"### Skill: {d.name}\n\n{md.read_text()}")
    if not parts:
        return ""
    return "## Available Skills\n\n" + "\n\n".join(parts)


def _tree_text(skills_dir: Path) -> dict:
    out = {}
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        for f in sorted(d.glob("*.md")):
            out[f"{d.name}/{f.name}"] = f.read_text()
    return out


def apply_proposal(skills_dir: Path, proposal: dict) -> tuple[bool, str, list]:
    """Apply create/patch to a skills dir in place. Returns (changed, diff, notes)."""
    before = _tree_text(skills_dir)
    notes = []
    action = proposal.get("action")
    if action == "create":
        name = _safe_name(proposal.get("name", "unnamed_skill"), suffix="")
        d = skills_dir / name
        d.mkdir(exist_ok=True)
        (d / "SKILL.md").write_text(proposal.get("skill_md", ""))
        (d / "PURPOSE.md").write_text(proposal.get("purpose_md", ""))
    elif action == "patch":
        name = _safe_name(proposal.get("name", ""), suffix="")
        md = skills_dir / name / "SKILL.md"
        if not md.exists():
            return False, "", [f"patch target skill missing: {name}"]
        text, n = apply_patch_ops(md.read_text(), proposal.get("edits"))
        md.write_text(text)
        notes.extend(n)
    else:
        return False, "", [f"no-op action: {action!r}"]

    after = _tree_text(skills_dir)
    diff_parts = []
    for key in sorted(set(before) | set(after)):
        a = before.get(key, "").splitlines(keepends=True)
        b = after.get(key, "").splitlines(keepends=True)
        if a != b:
            diff_parts.extend(difflib.unified_diff(a, b, f"a/{key}", f"b/{key}"))
    return bool(diff_parts), "".join(diff_parts), notes


def stage_candidate(run_dir: Path) -> Path:
    cand = run_dir / "candidate_skills"
    if cand.exists():
        shutil.rmtree(cand)
    shutil.copytree(run_dir / "skills", cand)
    return cand


def promote_candidate(run_dir: Path) -> None:
    skills = run_dir / "skills"
    shutil.rmtree(skills)
    shutil.copytree(run_dir / "candidate_skills", skills)


def record_skill_impact(run_dir: Path, *, iteration: int, proposal: dict,
                        val_score, best_before: float, outcome: str,
                        diff: str) -> None:
    entry = [
        f"\n## Iteration {iteration} — {proposal.get('action')} "
        f"`{proposal.get('name', '-')}` — **{outcome}**",
        f"- validation score: {val_score} (best before: {best_before:.4f})",
    ]
    if diff:
        entry += ["", "```diff", diff.rstrip("\n"), "```"]
    with (run_dir / "wiki" / "skill-impact.md").open("a") as f:
        f.write("\n".join(entry) + "\n")
