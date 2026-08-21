# CASE-010: Pilot Optimism Collapse

> [Index](../README.md) · [Examples](README.md)

Real empirical case from the FIS project (Fintech Integration Sandbox), a realistic
synthetic fintech-operations laboratory used to develop this playbook's methodology.

**Source:** INT-CASE-010 · **Date range:** 2026-08-15 – 2026-08-20
**Cited by:** [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

---

## Situation

FIS's first head-to-head comparison ("E2" local vs "E4" frontier) ran on
2026-08-15, before the full 288-scenario corpus existed. Both arms ran the
identical `FIXED_EVIDENCE` bundle — the same evidence handed to both models,
isolating reasoning ability from retrieval — over a 12-case pilot (one scenario
per class, 12 classes). Pilot runs are cheap and fast to iterate on, and the
corpus was still being built out to its eventual 96-case TEST size.

## Decision faced

The 12-case pilot showed the local model (Qwen3-8B, greedy decode) identifying
root cause correctly 41.7% of the time but choosing the correct operational action
only 8.3% of the time (1/12) — and not randomly: the same action name
(`replay_webhook`) was chosen for a settlement mapping error, a risk hold, and a
compound KYC failure. The question this case answers: was that 12-case headline —
and the "diagnosis is a materially easier problem than remedy selection" reading
it supported — strong enough to characterize the local model's capability gap and
justify committing the next several days of work (corpus scale-out, a 96-case
confirmation, and an entire prompt-engineering program, "E6"/"E6b") to closing
exactly that gap?

## Evidence

The pilot's own caveat, recorded in the log before any scaling occurred: *"n=12
(one per class). A single case moves any rate by 8.3 points."*

Pilot (n=12) vs confirmation (n=96), same local arm, same evidence mode:

| Metric | n=12 (pilot) | n=96 (confirmation) | Δ |
|---|---|---|---|
| Strict all-pass | 8.3% | 5.2% | −3.1 pp |
| Root-cause accuracy | 41.7% | 29.2% | **−12.5 pp** |
| Next-action accuracy | 8.3% | 13.5% | +5.2 pp |
| Verifier pass | 83.3% | 64.6% | −18.7 pp |
| Forbidden claims (total) | (not recorded at n=12) | 0 | — |

A second, independent guard against small-margin false positives ran five weeks
later in the same experimental line ("E6b", 2026-08-15, dev split n=48): four
prompt variants were compared against a control (C) to see whether any recovered
citation-evidence recall. A decision rule was fixed **before** the fourth variant
(H) was run: *adopt H only if evidence recall ≥ C + 5 points AND root cause ≥ C −
3 points.*

| Variant | Root cause | Evidence recall | Strict all-pass |
|---|---|---|---|
| C (control) | 62.5% | 70.8% | 35.4% |
| H | 56.3% (**−6.3**) | 64.9% (**−5.9**) | **39.6%** |

H failed the pre-registered rule on both primary metrics — yet had the single
highest all-pass rate of any variant tested, a two-case margin on n=48. The log
records the result plainly: H's all-pass "is precisely the number that would have
been cherry-picked without the rule." A 2026-08-20 methodology-synthesis pass
later retroactively validated the rule's design point: at FIS's suite sizes, a
paired-difference MDE analysis put DEV(48)'s resolving power at roughly 16–22
percentage points — a two-case (~4-pp) swing sits far inside that noise floor. The
synthesis states this directly: *"the '+2-case fluke' adoption rule is
quantitatively validated."* The same synthesis records that pre-registered
adoption rules of this kind caught at least two cherry-picks across the project
(E6b's H variant; a separate model-selection verdict, "R3b").

## What happened

The n=12 pilot's headline number was optimistic: root-cause accuracy fell 12.5
points, from 41.7% to 29.2%, once the sample grew eightfold — a single case at
n=12 had been worth 8.3 points, exactly as flagged in advance. But the pilot's
*qualitative* finding survived: at n=96, diagnosis (29.2%) still ran roughly twice
the rate of remedy selection (13.5%), the same 2:1 shape observed at n=12 — the
structural gap the pilot pointed at was real even though its magnitude was not.
One metric even moved in the opposite direction from what the pilot's noise alone
would predict (next-action accuracy rose, not fell), and one failure mode was
invisible at n=12 by construction: citation discipline degraded materially at
scale (verifier pass 83.3% → 64.6%, 37 unsupported claims appearing only once
harder cases entered the sample).

Discipline ran in the opposite direction too, the same session: the frontier arm
("E4") was deliberately **not** re-run at n=96 on this corpus, because an
event-sourcing migration was about to regenerate every scenario and invalidate the
comparison regardless. Spending frontier budget and rate-limit headroom on a
baseline about to be discarded was recorded as waste, not caution.

Five weeks into the same experimental line, the same discipline caught a second,
different failure shape: not an underpowered point estimate read as truth, but a
best-looking metric chosen after the fact. E6b's four dev variants were compared
against control C, and H — the variant with the highest raw all-pass rate —
failed the two metrics the adoption rule had been built around *before* H's
result existed. The rule rejected H. Nothing about H's all-pass number was wrong
as a measurement; what made it dangerous was that, absent a rule fixed in advance,
it was the exact number a post-hoc read would have reached for.

## The generic lesson

1. State, before running a pilot, what one flipped case is worth (100/n
   percentage points) and treat any low-n pilot headline as directional only —
   never as adoption evidence. A pilot can legitimately motivate the next
   experiment; it cannot stand in for it.
2. When scaling from a pilot to a powered confirmation, expect the point estimate
   to move. Only claims about *direction or shape* (e.g., "diagnosis is easier
   than remedy selection") are validated by a pilot; magnitude claims wait for the
   split sized to resolve them — see [MDE](../GLOSSARY.md#mde).
3. Before comparing several candidates, fix the
   [elimination](../GLOSSARY.md#elimination-rule)/adoption rule — which metric(s),
   what threshold, in which direction — **before** running the comparison that
   will decide between them. Choosing the winning metric after seeing results is
   fishing; only a rule fixed in advance can separate a real effect from a margin
   the suite cannot resolve.
4. When a candidate that fails the pre-registered rule is nonetheless the
   best-looking result on some other, non-pre-registered metric, that is the
   situation the rule exists to catch — not evidence the rule was miscalibrated.
   Record the discarded metric for the audit trail; do not act on it.
5. Avoiding wasted measurement is the same discipline in the other direction:
   treating a not-yet-final artifact (a corpus about to be regenerated, a suite
   about to be superseded) as provisional, and not spending scarce measurement
   budget confirming a number that further work will invalidate anyway.

Encoded in: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
([pre-registration](../GLOSSARY.md#pre-registration),
[one-look discipline](../GLOSSARY.md#one-look-discipline),
[elimination rule](../GLOSSARY.md#elimination-rule)); `templates/EXPERIMENT_CONTRACT.md`
§1 (prediction register) and §8 (candidate selection & elimination rules — "no
candidate withdrawn below the pilot's own MDE"); `templates/PREDICTION_LEDGER.md`.

## What would NOT have worked

- **Planning around the 12-case pilot's point estimate.** 41.7% root-cause
  accuracy was 12.5 points optimistic against the 96-case confirmation — a swing
  larger than most of the effects the project was designed to detect.
- **Selecting E6b's variant H for its all-pass rate.** The record is explicit that
  this would have been "precisely the number that would have been cherry-picked
  without the rule," on a decline in both metrics the rule was pre-registered to
  check.
- **Re-running the frontier arm at n=96 "to be thorough" before the corpus
  migration.** The comparison would have been invalidated within days regardless;
  the spend would have bought nothing but a discarded number.

## References

- INT-CASE-010 (this case; source of record: `experiment-log.md` E2/E6b entries)
- [EXT-STATS-001] Miller, "Adding Error Bars to Evals" (arXiv:2411.00640) —
  the paired-difference MDE reasoning that retroactively validates the "+2-case
  fluke" rule
- [EXT-STOPPING-002] Lan–DeMets adaptive-design / DSMB pre-specification
  (clinical-trial practice) — the adaptation rule is pre-registered and executed
  mechanically rather than by investigator judgment, the same shape as E6b's
  decision rule
- [NV-MODELOPTRESEARCH-001] NVIDIA Model Optimizer Researcher Guide — binomial
  margin-of-error table by sample size, corroborating that small-n point estimates
  carry wide, easily unstated error bars

---

[Index](../README.md) · [Examples](README.md)
