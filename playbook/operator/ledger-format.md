# Engagement home and ledger formats

> DRAFT — pending field trial; see README.md in this directory.

## The engagement home

One engagement, one private home, **next to the code it concerns and
never inside the playbook repo**:

```
<engagement-home>/
├── ENGAGEMENT_STATE.json    # derived snapshot (the ledger wins)
├── ledger.jsonl             # append-only record of record
├── profile/                 # filled PROJECT_PROFILE.md
├── artifacts/               # contracts, autopsies, MDRs, reports —
│                            #   instantiated from playbook/templates/
├── inbox/                   # notes queued mid-work; surfaced on greeting
└── runs/                    # experiment outputs, per the active contracts
```

Client engagements: their own folder or private repo per client — client
data never mixes across engagements or into the playbook. Lab-internal
engagements: `projects/<name>/` in the lab repo, as today.

## ledger.jsonl — the record of record

Append-only, **decision-level, written at act time** — never keystroke
level, never batch-reconstructed. One JSON object per line:

```json
{"v": 1, "ts": "2026-09-01T18:00:00Z", "type": "gate",
 "position": "03§7 gate 1", "actor": "operator-agent",
 "summary": "Reachability ceiling measured at 0.96; gate PASSED.",
 "detail": {"artifact": "artifacts/suite-v1/integrity.json"}}
```

| type | When | Extra keys in `detail` |
|---|---|---|
| `session` | Session start/end, engagement open/close | — |
| `decision` | Owner chose (or defaulted) between options | `options`, `chosen`, `by` ("owner" or "default") |
| `gate` | A chapter §7 gate evaluated | `outcome` (PASSED / FAILED / INAPPLICABLE + evidence), `artifact` |
| `artifact` | Something produced or frozen in `artifacts/` | `path`, `hash` when frozen |
| `deviation` | Anything done differently from the written procedure | `what`, `why`, `approved_by` |
| `spend` | Money/tokens/GPU-time committed | `amount`, `unit`, `against` (which contract cap) |
| `handoff` | Work delegated to a packaged tool | `tool`, `owns`, later a matching `artifact` row on return |
| `note` | Anything worth keeping that fits nothing above | — |

Rules: rows are never edited or deleted (corrections are new rows
referencing the old by timestamp); secret values never appear; every row
a human might read aloud is written in plain words.

## ENGAGEMENT_STATE.json — the derived snapshot

```json
{"v": 1, "engagement": "client-x-retrieval",
 "playbook_path": "<absolute path to your playbook checkout>",
 "playbook_version": "0.1.1",
 "position": "07§5.1 rung 2 — diagnostic half-run",
 "next_action": "finish rung-2 probe per 07§5.2, then gate row",
 "environment_fingerprint": {"models": {}, "harness": "", "endpoints": []},
 "derived_from_row_ts": "2026-09-01T18:00:00Z",
 "updated_utc": "2026-09-01T18:01:00Z"}
```

Regenerated whenever it disagrees with the ledger — the same rule as the
budget meter: totals (here, positions) are recomputed from the append-only
file, never trusted from memory. `playbook_version` pins which corpus
version governs the engagement (see the resume protocol in START.md).

## inbox/

One file per note — `YYYYMMDD-HHMM-<slug>.md` with date, source, and the
owner's words unedited. Surfaced at every session start; a note that
becomes work gets a `decision` row and moves into `artifacts/` or the
plan; a note declined gets a row saying so. Nothing queued is ever lost
silently.

## Distillation rule

Every narrative — status updates, the closing ENGAGEMENT_REPORT, evidence
submitted for adjudication — is **distilled from ledger rows and cites
them**. If a claim has no row, the claim waits until the row exists.
