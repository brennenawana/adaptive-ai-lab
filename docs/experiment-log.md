# Experiment Log

Append-only. Each entry records what was run, what was found, and — importantly —
what was **not** changed as a result, so later readers can tell a principled
decision from a convenient one.

---

## 2026-08-15 — Platform stood up, first E2/E4 comparison (n=12)

### Configuration

| | |
|---|---|
| Local specialist | Qwen3-8B Q4_K_M, llama.cpp CUDA, greedy (temp 0, seed 42), `--parallel 1` |
| Frontier | Claude Opus 5 via subscription CLI, `--safe-mode --tools ""` |
| Evidence mode | `FIXED_EVIDENCE` both arms — identical bundle, so the difference measured is reasoning, not tool strategy |
| Split | test, 1 scenario per class |
| Verifier | schema, citation format, citation resolves to a call, cited ids observed, action code known, confidence calibration |

### Results (n=12 — directional only)

| Metric | E2 local 8B | E4 frontier |
|---|---|---|
| Strict all-pass | 8.3% | 50.0% |
| Root-cause accuracy | 41.7% | 83.3% |
| Next-action accuracy | 8.3% (1/12) | 75.0% (9/12) |
| Verifier pass | 83.3% | 100% |
| P95 latency | 101 s | 56 s |
| Reference cost / success | $0.00 | $0.1778 |

### Principal finding

The local model's failure is **not uniformly distributed**. It identifies the root
cause in 41.7% of cases but selects the correct operational action in 1 of 12 —
and not randomly: `replay_webhook` was chosen for a settlement mapping error, a
risk hold, and a compound KYC failure. That is anchoring on a salient action name,
not reasoning from cause to remedy.

A single accuracy figure would have hidden this entirely. It is the clearest
argument so far for the guide's per-dimension scoring.

**Implication for the ladder:** this reads as a prompt/schema gap (the model is
never shown which actions are plausible for a case category), which sits *above*
LoRA. E6 should be run before E7 is even considered.

### Harness defects found by running it

All three would have been misread as model weakness:

1. **llama.cpp GBNF converter rejects `minLength`/`maxLength`** — 400 on every
   local call. Fixed by stripping length constraints for grammar compilation only;
   the verifier still enforces them. Grammar guarantees shape, verifier guarantees
   semantics.
2. **Verifier rejected citations naming the tool** (`tool://get_ledger_entries/le_1`)
   rather than the service — failed 11 of 12 *correct* citations. Now accepts both.
3. **Fixed-evidence plan never called `get_webhook_history`** — required evidence
   was structurally unreachable for S01, S02, S06, S10. Plan is now two-phase:
   entity lookups, then provider-ref-driven event lookups.

Fixing (2) and (3) moved E2 root-cause accuracy 16.7% → 41.7%. **That gap was
infrastructure, not the model** — a direct instance of what the Discovery
Controller exists to prevent.

### Deliberately NOT changed

- **The action rubric was not widened.** Two E4 answers look defensible but scored
  wrong (S09 `contact_identity_vendor` when the vendor genuinely did change schema;
  S10 `inspect_mapping_version`). The rubric was written on the merits before any
  results existed. Adjusting it now would be tuning against the test set. Logged as
  a `BAD_RUBRIC` candidate for review **before** the next frozen suite version, not
  after seeing more scores.

### Caveats

- n=12 (one per class). A single case moves any rate by 8.3 points.
- E4 runs at 100% cloud dependence by construction — E5 is where the interesting
  cost/quality tradeoff appears.
- Frontier arm is not bit-reproducible: the subscription CLI exposes no
  temperature or seed. The local arm is. Recorded on the model manifest as
  `supports_seed`.

---

## 2026-08-15 — Corpus scaled to 288 scenarios

96 test / 48 dev / 144 train, all 12 classes in each split.

### Two bugs found by scaling

1. **Entity id collisions.** Ids were a per-scenario counter plus 3 random digits;
   across ~96 scenarios that collided (birthday problem). Ids now embed the seed.
2. **`scenario_id` collided across splits.** It was `seed % 100_000`, so train seed
   1,000,000 and test seed 3,000,000 both rendered `S01-00000` — the same primary
   key for a training and a test scenario. This would have silently defeated the
   disjoint seed ranges that exist specifically to prevent leakage. Now uses the
   full 7-digit seed.

Neither was reachable by a single-scenario test. Added `test_generator_uniqueness.py`,
which builds a multi-split corpus and asserts global uniqueness of every id space
including `provider_ref` (a collision there would splice one scenario's webhook
evidence into another's investigation).

**Prior n=12 results are not comparable to anything generated after this change** —
the corpus was regenerated with new ids.

---

## Open questions

- Does showing the model a category→plausible-actions table fix the action gap? (E6)
- Does runbook retrieval help, or is the evidence bundle already sufficient? (E3)
- At what escalation threshold does hybrid routing retain E4 accuracy at materially
  lower cloud dependence? (E5)
- Is the residual local failure evidence-selection or reasoning? The fixed-evidence
  mode isolates this: with evidence held constant, remaining errors are reasoning.
