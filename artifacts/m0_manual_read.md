# M0 — the pre-declared manual read of every treatment outcome (WP-B)

> The record the report's § 2.3 refers to. Performed AFTER the frozen rubric ran
> (rubric verdicts are primary and were never overridden); source texts are in
> `learning.trajectories` by the treatment trace ids in `m0_paired_probe.csv`.
> The reader was the executing agent; the still-truncated tails were read in full,
> excerpts below are verbatim tail fragments (TRAIN content, private repo).

## The 9 rescues (class a) — deterministic scorer pass; no manual override

| case | out-tokens | manual note |
|---|---|---|
| S02-1001001 | 10990 | all_pass; completed 2.8k tokens past the old cap |
| S02-1002001 | 11368 | all_pass |
| S05-1002004 | 8846 | all_pass; narrowest rescue margin (+654 tokens) |
| S06-1001005 | 8946 | all_pass |
| S08-1002007 | 9247 | all_pass |
| S10-1000009 | 10652 | all_pass |
| S10-1001009 | 11573 | all_pass; widest margin (+3381) |
| S11-1002010 | 11181 | all_pass |
| S12-1000011 | 9052 | all_pass |

## The 1 wrong-complete (class b)

**S11-1000010** (11386 tokens, stop): scorer dims — `root_cause_correct=True`,
`next_action_acceptable=True`, `verifier_passed=True`, `forbidden_claim_made=False`,
`unsupported_claims=0`, **`required_evidence_recall=0.5 < 0.8`**. Manual reading:
the diagnosis and action are right; the answer under-cites required evidence.
A citation-discipline miss, not a reasoning failure. Rubric class (b) stands.

## The 5 still-truncated (class c) — manual read AGREES with the rubric on all 5

| case | reasoning ch | content ch | dup | tail-novelty | manual reading of the tail |
|---|---|---|---|---|---|
| S07-1000006 | 40510 | 344 | 0.18 | 0.76 | deliberating output-schema details ("Need final only JSON") — answer construction, cut at the SLOT ceiling (12201 = 16384 − 4183-token prompt) |
| S07-1001006 | 45691 | 0 | 0.21 | 0.73 | drafting the facts array WITH tool citations inside reasoning (`"source": "tool://get_ledger_entries/…"`) — mid-answer in all but field placement |
| S07-1002006 | 42366 | 1414 | 0.16 | 0.84 | choosing between acceptable next actions — post-diagnosis deliberation |
| S11-1001010 | 38191 | 3647 | 0.17 | 0.73 | eliminating final alternative hypotheses, then "Now final JSON. Ensure valid." |
| S12-1001011 | 47296 | 1850 | 0.24 | 0.66 | calibrating the confidence field of an already-chosen answer |

Common shape: all 12 ontology hypotheses surveyed, new evidence tokens still
appearing in the tail, zero degenerate indicators fired, and 4 of 5 already
emitting the JSON answer. These are convergent, near-terminal generations — the
kind the next cap increment plausibly converts — not loops.

Disagreements with the rubric: **none.**
