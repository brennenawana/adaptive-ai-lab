#!/usr/bin/env python3
"""Render references/SOURCES.md from references/sources.yaml, and validate the ledger.

sources.yaml is the record of record; SOURCES.md is generated — never hand-edit it.
Usage:  python3 render_sources.py [--check]
  --check   validate only (exit 1 on problems), don't rewrite SOURCES.md
Deterministic: same input → same output. Requires PyYAML.
"""
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
YAML_PATH = HERE.parent / 'sources.yaml'
OUT_PATH = HERE.parent / 'SOURCES.md'

REQUIRED = ['id', 'org', 'title', 'type', 'maturity', 'classification',
            'evidence_strength', 'claims', 'chapters', 'freshness']
CLASSES = ['FOLLOW', 'ADAPT', 'REFERENCE', 'DEPRECATED', 'CASE']
CLASS_BLURB = {
    'FOLLOW': 'Mature methodology — follow by the book, within the stated scope and as-of date.',
    'ADAPT': 'Mechanics sound, decision layer missing — adapt per references/VENDOR_RECIPE_NOTES.md.',
    'REFERENCE': 'Consult, do not depend on.',
    'DEPRECATED': 'Do not adopt. Recorded to prevent re-adoption; supersession is recorded, never deleted.',
    'CASE': 'Internal empirical case studies — narratives live in examples/.',
}


def load():
    data = yaml.safe_load(YAML_PATH.read_text())
    return data['sources']


def validate(rows):
    problems = []
    seen = set()
    for r in rows:
        rid = r.get('id', '<missing id>')
        if rid in seen:
            problems.append(f'duplicate id: {rid}')
        seen.add(rid)
        for f in REQUIRED:
            if r.get(f) in (None, '', []):
                problems.append(f'{rid}: missing required field {f!r}')
        if r.get('classification') not in CLASSES:
            problems.append(f"{rid}: bad classification {r.get('classification')!r}")
        if r.get('freshness') == 'volatile' and r.get('classification') in ('FOLLOW', 'ADAPT') \
                and not r.get('last_verified'):
            problems.append(f'{rid}: volatile FOLLOW/ADAPT source with no last_verified')
    return problems


def render(rows):
    by_class = {c: [] for c in CLASSES}
    for r in rows:
        by_class[r['classification']].append(r)
    for c in by_class:
        by_class[c].sort(key=lambda r: r['id'])

    L = []
    L.append('# Sources')
    L.append('')
    L.append('> Part of the **Adaptive AI Systems Playbook** · [Index](../README.md)')
    L.append('>')
    L.append('> GENERATED from [`sources.yaml`](sources.yaml) by `tools/render_sources.py` —')
    L.append('> do not edit by hand. The YAML file is the record of record; chapters cite')
    L.append('> stable IDs; this page is the human-readable rendering.')
    L.append('')
    n = len(rows)
    L.append(f'{n} sources. Verdict counts: ' + ' · '.join(
        f"{c} {len(by_class[c])}" for c in CLASSES))
    L.append('')
    for c in CLASSES:
        L.append(f'## {c}')
        L.append('')
        L.append(f'*{CLASS_BLURB[c]}*')
        L.append('')
        L.append('| ID | Source | Claims we cite it for | Strength | Freshness | Verified |')
        L.append('|---|---|---|---|---|---|')
        for r in by_class[c]:
            title = r['title']
            url = r.get('url')
            link = f'[{title}]({url})' if url and str(url).startswith('http') else title
            if url and not str(url).startswith('http'):
                link = f'{title} (`{url}`)'
            org = r.get('org', '')
            claims = str(r.get('claims', '')).replace('|', '/')
            L.append(f"| {r['id']} | **{org}** — {link} | {claims} | "
                     f"{r.get('evidence_strength','')} | {r.get('freshness','')} | "
                     f"{r.get('last_verified') or '—'} |")
        L.append('')

    L.append('## Deprecation / supersession watchlist')
    L.append('')
    L.append('Standing section: things that were current, no longer are, and still get')
    L.append('recommended by stale material. Check here before adopting any vendor recipe.')
    L.append('')
    L.append('| ID | What | Trap |')
    L.append('|---|---|---|')
    for r in by_class['DEPRECATED']:
        notes = str(r.get('notes', '')).replace('|', '/')
        L.append(f"| {r['id']} | {r['title']} | {notes} |")
    L.append('')
    L.append('Additional standing traps recorded on active sources: the hosted OpenAI Evals')
    L.append('platform sunsets 2026-11-30 (EXT-EVAL-002); NVIDIA NeMo Evaluator docs `/latest/`')
    L.append('redirects to `/nightly/` with no pinned tree (NV-EVALSDK-001); the Model')
    L.append('Optimizer quantization *decision page* omits NVFP4 while the same repo recommends')
    L.append('it elsewhere (NV-MODELOPTQUANT-001 vs NV-MODELOPTQAD-001) — date-weight vendor')
    L.append('decision pages against the vendor\'s own current practice.')
    L.append('')
    return '\n'.join(L) + '\n'


def main():
    rows = load()
    problems = validate(rows)
    if problems:
        print('sources.yaml validation FAILED:', file=sys.stderr)
        for p in problems:
            print(' -', p, file=sys.stderr)
        return 1
    if '--check' in sys.argv:
        expected = render(rows)
        if OUT_PATH.exists() and OUT_PATH.read_text() == expected:
            print(f'OK: {len(rows)} sources; SOURCES.md up to date')
            return 0
        print('SOURCES.md is stale or missing — run render_sources.py to regenerate',
              file=sys.stderr)
        return 1
    OUT_PATH.write_text(render(rows))
    print(f'wrote {OUT_PATH} ({len(rows)} sources)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
