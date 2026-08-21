#!/usr/bin/env python3
"""Release validation for the Adaptive AI Systems Playbook (build scaffolding).

Checks (each prints PASS/FAIL + details; exit 1 if any FAIL):
  1. inventory   — every required file exists
  2. portability — banned project strings outside examples/CASE-* (with allowlist)
  3. skeleton    — chapters 00-13 carry the 13-section skeleton
  4. links       — relative markdown links resolve; no links into ../docs
  5. citations   — every [SRC-ID] cited exists in sources.yaml
  6. sources     — sources.yaml valid + SOURCES.md up to date (render --check)
  7. anchors     — GLOSSARY.md#anchor links resolve to real headings
"""
import re, subprocess, sys
from pathlib import Path

PB = Path(__file__).resolve().parents[2]  # playbook/

CHAPTERS = [
    '00_PRINCIPLES_AND_SCOPE.md', '01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md',
    '02_EXECUTION_SYSTEM_MODEL.md', '03_EVALUATION_FOUNDATION.md',
    '04_EXPERIMENT_DESIGN_AND_STATISTICS.md', '05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md',
    '06_INFERENCE_PERFORMANCE_AND_CAPACITY.md', '07_OPTIMIZATION_AND_INTERVENTION_LADDER.md',
    '08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md', '09_TRAINING_AND_DATA.md',
    '10_DEPLOYMENT_AND_OPERATIONS.md', '11_ECONOMICS_HARDWARE_AND_CLOUD.md',
    '12_OBSERVABILITY_LEARNING_AND_PROMOTION.md', '13_GOVERNANCE_PROVENANCE_AND_SECURITY.md',
    '14_DECISION_TREES_AND_CHECKLISTS.md',
]
FRONT = ['README.md', 'QUICKSTART.md', 'GLOSSARY.md', 'VERSION', 'CHANGELOG.md']
TEMPLATES = ['PROJECT_PROFILE.md', 'EXPERIMENT_CONTRACT.md', 'EVAL_SUITE_RELEASE_CONTRACT.md',
             'PERFORMANCE_AUTOPSY.md', 'TEST_LOOK_LEDGER.md', 'COMPUTE_DEMAND_LEDGER.md',
             'PREDICTION_LEDGER.md', 'OPERATIONAL_HANDOFF.md', 'METHOD_DECISION_RECORD.md']
REFERENCES = ['sources.yaml', 'SOURCES.md', 'STATISTICS_FORMULAS.md', 'VENDOR_RECIPE_NOTES.md']
CASES = [f'CASE-{i:03d}' for i in range(1, 13)]
SYNTH = [f'SYNTH-{i:02d}' for i in range(1, 11)]
SKELETON = ['1. Purpose', '2. Inputs', '3. Decisions', '4. Normative principles',
            '5. Default procedure', '6. Project adaptation parameters',
            '7. Decision gates', '8. Metrics and formulas', '9. Failure modes',
            '10. Vendor recipes', '11. Worked examples', '12. Outputs', '13. Sources']

# Banned outside examples/CASE-* and planning/. (pattern, allow_predicate(file, line))
def _vendor_ok(line: str) -> bool:
    l = line.lower()
    return ('nemotron' in l and ('nvidia' in l or 'nemotron 3' in l or 'nemotron-cc' in l
            or 'nemotroncc' in l or 'nv-' in l or 'blogs.nvidia.com' in l
            or 'developer.nvidia.com' in l or 'huggingface.co' in l or 'lightning' in l))

BANNED = [
    (re.compile(r'\bFIS\b'), None),
    (re.compile(r'Fintech Integration Sandbox'), None),
    (re.compile(r'\bfintech\b', re.I), lambda f, l: 'ICAIF' in l or 'LLM Output Drift' in l),
    (re.compile(r'\bQwen', re.I), None),
    # Vendor-ledger files are definitionally about vendor products (NVIDIA Nemotron etc.)
    (re.compile(r'\bNemotron', re.I),
     lambda f, l: _vendor_ok(l) or f.name in ('sources.yaml', 'SOURCES.md', 'VENDOR_RECIPE_NOTES.md')),
    (re.compile(r'\bBonsai\b'), None),
    (re.compile(r'\bGPT-OSS\b', re.I), None),
    (re.compile(r'\bSuite v[0-9]'), None),
    (re.compile(r'\b(R[4-9]|E6b?|M0|M-STAT|H0|D0)\b'), lambda f, l: 'H0:' in l or 'H0 ' in l),  # allow stats null-hypothesis H0
    (re.compile(r'\bS(0[1-9]|1[0-2])\b'), lambda f, l: 'S3' in l or 'quantile' in l.lower()),
    (re.compile(r'RTX 5080|RTX 5090|RTX 3090|RTX 4090|DGX Spark', re.I),
     lambda f, l: f.name == 'VENDOR_RECIPE_NOTES.md' or f.name == 'SOURCES.md' or f.name == 'sources.yaml'),
    (re.compile(r'\b(5433|4222|8082)\b'), None),
    (re.compile(r'\bNATS\b'), None),
    (re.compile(r'ground_truth\b'), None),
    (re.compile(r'adaptive-ai-lab|/home/wall'), None),
    (re.compile(r'N_eff\s*[≈~]=?\s*22'), None),
    (re.compile(r'\blearning\.(registry|case_scores|trajectories)'), None),
]

LINK_RE = re.compile(r'\[[^\]]*\]\(([^)#\s]+)?(#[^)\s]*)?\)')
CITE_RE = re.compile(r'\[((?:NV|EXT|INT)-[A-Z0-9-]+-\d{3})\]')

# Build scaffolding at playbook/ root: committed planning artifacts, not shipped
# playbook content (their own STATUS headers say PLANNING ARTIFACT). Excluded from
# shipped-content checks; excluded from extraction at 1.0 alongside planning/.
SCAFFOLDING = {'PLAYBOOK_BUILD_PLAN.md', 'SOURCE_MAP_DRAFT.md', 'PASS2_AUTHORING_SPEC.md'}

def shipped_files():
    out = []
    for p in sorted(PB.rglob('*')):
        if p.is_dir():
            continue
        rel = p.relative_to(PB)
        if rel.parts[0] == 'planning' or (len(rel.parts) == 1 and rel.name in SCAFFOLDING):
            continue
        out.append(p)
    return out

def is_case(p: Path) -> bool:
    # CASE files are the sanctioned home of project material; examples/README.md is
    # the case library's index and must identify the source project (justified
    # navigation reference per the authoring spec). WALKTHROUGH/SYNTH stay generic.
    return p.parent.name == 'examples' and (p.name.startswith('CASE-') or p.name == 'README.md')

def main():
    failures = []

    # 1. inventory
    missing = []
    for f in FRONT + CHAPTERS:
        if not (PB / f).exists(): missing.append(f)
    for f in TEMPLATES:
        if not (PB / 'templates' / f).exists(): missing.append(f'templates/{f}')
    for f in REFERENCES:
        if not (PB / 'references' / f).exists(): missing.append(f'references/{f}')
    ex = PB / 'examples'
    for stem in CASES + SYNTH:
        if not list(ex.glob(stem + '_*.md')): missing.append(f'examples/{stem}_*.md')
    if not list(ex.glob('WALKTHROUGH_*.md')): missing.append('examples/WALKTHROUGH_*.md')
    if not (ex / 'README.md').exists(): missing.append('examples/README.md')
    print(('FAIL' if missing else 'PASS') + f' [1 inventory] missing={missing}')
    if missing: failures.append('inventory')

    # 2. portability
    hits = []
    for p in shipped_files():
        if p.suffix not in ('.md', '.yaml', '.py') or is_case(p):
            continue
        for i, line in enumerate(p.read_text(errors='replace').splitlines(), 1):
            for pat, allow in BANNED:
                if pat.search(line) and not (allow and allow(p, line)):
                    hits.append(f'{p.relative_to(PB)}:{i}: {pat.pattern[:30]} :: {line.strip()[:100]}')
    print(('FAIL' if hits else 'PASS') + f' [2 portability] {len(hits)} hits')
    for h in hits[:40]: print('   ', h)
    if hits: failures.append('portability')

    # 3. skeleton
    bad = []
    for f in CHAPTERS[:-1]:  # 14 exempt
        p = PB / f
        if not p.exists(): continue
        text = p.read_text()
        for s in SKELETON:
            if not re.search(rf'^##\s+{re.escape(s)}', text, re.M):
                bad.append(f'{f}: missing section "{s}"')
    print(('FAIL' if bad else 'PASS') + f' [3 skeleton] {len(bad)} problems')
    for b in bad[:30]: print('   ', b)
    if bad: failures.append('skeleton')

    # 4. links
    badlinks = []
    for p in shipped_files():
        if p.suffix != '.md': continue
        for i, line in enumerate(p.read_text(errors='replace').splitlines(), 1):
            for m in LINK_RE.finditer(line):
                target = m.group(1)
                if not target or target.startswith(('http://', 'https://', 'mailto:')):
                    continue
                if target.startswith('../docs') or '/docs/' in target:
                    badlinks.append(f'{p.relative_to(PB)}:{i}: link into docs/: {target}')
                    continue
                t = (p.parent / target).resolve()
                if not t.exists():
                    badlinks.append(f'{p.relative_to(PB)}:{i}: broken link: {target}')
    print(('FAIL' if badlinks else 'PASS') + f' [4 links] {len(badlinks)} problems')
    for b in badlinks[:40]: print('   ', b)
    if badlinks: failures.append('links')

    # 5. citations
    import yaml
    ledger = yaml.safe_load((PB / 'references/sources.yaml').read_text())
    known = {r['id'] for r in ledger['sources']}
    unknown = []
    cited = set()
    for p in shipped_files():
        if p.suffix != '.md': continue
        for m in CITE_RE.finditer(p.read_text(errors='replace')):
            cited.add(m.group(1))
            if m.group(1) not in known:
                unknown.append(f'{p.relative_to(PB)}: unknown source id [{m.group(1)}]')
    print(('FAIL' if unknown else 'PASS') + f' [5 citations] {len(cited)} distinct ids cited; {len(unknown)} unknown')
    for u in sorted(set(unknown))[:30]: print('   ', u)
    if unknown: failures.append('citations')
    uncited = sorted(known - cited)
    print(f'     (info) uncited sources: {len(uncited)}')

    # 6. sources render check
    r = subprocess.run([sys.executable, str(PB / 'references/tools/render_sources.py'), '--check'],
                       capture_output=True, text=True)
    ok6 = r.returncode == 0
    print(('PASS' if ok6 else 'FAIL') + f' [6 sources] {r.stdout.strip() or r.stderr.strip()}')
    if not ok6: failures.append('sources')

    # 7. glossary anchors
    gl = (PB / 'GLOSSARY.md').read_text()
    anchors = set()
    for m in re.finditer(r'^###\s+(.+)$', gl, re.M):
        a = m.group(1).strip().lower()
        a = re.sub(r'[^a-z0-9\s-]', '', a).replace(' ', '-')
        anchors.add(a)
    badanch = []
    for p in shipped_files():
        if p.suffix != '.md': continue
        for i, line in enumerate(p.read_text(errors='replace').splitlines(), 1):
            for m in re.finditer(r'\(([^)\s]*GLOSSARY\.md)#([^)\s]+)\)', line):
                if m.group(2) not in anchors:
                    badanch.append(f'{p.relative_to(PB)}:{i}: bad glossary anchor #{m.group(2)}')
    print(('FAIL' if badanch else 'PASS') + f' [7 anchors] {len(badanch)} problems')
    for b in badanch[:30]: print('   ', b)
    if badanch: failures.append('anchors')

    print()
    print('OVERALL:', 'PASS' if not failures else f'FAIL ({", ".join(failures)})')
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
