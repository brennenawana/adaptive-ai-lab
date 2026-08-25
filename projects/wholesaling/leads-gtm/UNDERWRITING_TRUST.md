# Underwriting Trust Assessment — What the Test Discipline Does and Does Not Prove

> From the code survey of the underwriting/valuation half (2026-08-25).
> Scoped to the question the lead-sale pivot forces: **can the numbers we would
> sell be trusted, and on what evidence?** Sections 1–7/9–10 (mechanics) live
> in [`UNDERWRITING_MECHANICS.md`](UNDERWRITING_MECHANICS.md); this file is the
> trust verdict.

## Verdict in one line

**The solver is rigorously proven to obey its own ruleset given inputs, and is
structurally silent on whether the inputs are right** — and the only
end-to-end reality check ever run (FL, n=6) found a systematic input error of
**5×–6.7×** that the entire 330-case corpus cannot see by construction.

## What IS trustworthy (and it is genuinely strong)

This is the one area of the repo with real test discipline, and it is better
than first reported:

- **Routing invariants: 26 IDs** raised via `check_case`
  (`backend/tests/pricing/pricing_invariants.py:284`) plus `SANITY-DETERMINISM`
  (`:714`). **Valuation: 11 IDs.** **Chain: 3 more**
  (`pricing_chain.py:213-250`). Five invariants were deliberately retired
  2026-06-11 and documented in-file (`pricing_invariants.py:50-52`).
- **Corpora**: 330 pricing cases = 170 hand-structured + 160 generated at seed
  20260610 (`pricing_harness.py:682-691`); the structured half enumerates every
  routing branch plus boundary cases (DOM `{None,0,149,150,151,400}`, price
  `{84_999…120_001}`, equity `{0.19,0.20,0.21}`, unit `{4,5}`, 9 garbage, 2
  DLBA). 139 valuation cases = 19 structured + 120 generated at seed 20260611.
- **Nine distinct seeds** across the discipline (incl. 424242 explicitly to
  guard seed overfitting, and four oracle sweeps of 630 cases each).
  `hypothesis` was explicitly rejected in favor of seeded determinism
  (`test_pricing_generative.py:4-5`).
- **A real differential oracle**: `tests/oracle/` shares **no code** with
  `app.underwriting`/`app.routing`, implements **closed-form algebra where
  production bisects** (`ruleset_oracle.py:17-38`), and is itself guarded by 25
  parametrized cases against a 200-iteration brute-force bisection.
- **CI gating is structurally hard to evade**: `backend/pyproject.toml:66-70`
  defines no `markers` key, so with `--strict-markers` any `@pytest.mark.slow`
  would be a **collection error, not a skip** — a marker gate on these suites
  is impossible in the current config. Zero `skip`/`xfail`/`importorskip` in
  either directory; single invocation on every PR (`ci.yml:62-63`).

## What it does NOT prove — the gap that decides the pivot

**The pricing harness supplies carrying costs directly to the solver.**
`monthly_taxes` / `monthly_insurance` come from a hard-coded per-market table
(`pricing_harness.py:49-58`; Detroit `(137.5, 100.0)`, fallback
`list_price × 0.02 / 12`), and the harness calls the pure router, not
`app/workers/routing.py`. Consequences:

- The entire area-cost resolution path — `underwriting/area_costs.py`, the
  committed millage/insurance CSVs, and the `HOLD_AREA_COSTS_MISSING` gate —
  is **never exercised** by the pricing suite.
- **The FL sample run's single largest defect — taxes + insurance understated
  5×–6.7× on every property — is structurally invisible to the 330-case
  corpus.** The version manifest *declares* those files (`underwriting_version.py:106-123`),
  so a change is recorded; nothing in `tests/pricing` would *catch* it.
- Same shape one level up: the harness supplies `rent`, `arv`, and `rehab` as
  scalars. Only `pricing_chain.py` composes valuation→routing for real, at 250
  generated cases (seed 4242).

**Goldens pin drift, not correctness.** Stated openly in-file: the literals
"were derived by running the shipped engine once"
(`test_pricing_golden.py:6-7`, `test_underwriting_golden.py:3-4`). Independent
correctness pressure comes only from the ruleset docstrings and the oracle.

**`BACKTESTED` is 0** and the weekly accuracy gate has no committed
measurement — so no claim about real-world valuation accuracy is currently
evidenced.

**The flip lane has the thinnest differential coverage** — ~53 distressed cash
structures of 630 sweep cases reach checks F1–F5, versus ~333 turnkey and ~359
SF. Flip is the **ARV-and-rehab-dependent** path, i.e. the one most exposed to
the least reliable inputs, and it gets the least pressure.

## Secondary trust caveats (recorded, lower stakes)

1. **The known-failure ratchet is currently inert.** `KNOWN_FAILURE_CLUSTERS`
   is `{}`, so `test_known_clusters_still_reproduce` and its valuation twin
   compute `stale = {} - seen = {}` and assert nothing. The *enforcement* half
   is live; the *ratchet* half only bites once a bug is ledgered.
2. **That ledger is a code-level allowlist** (`partition_known`, `:752`), not a
   pytest marker — invisible to `pytest -m` / `--collect-only`. A future entry
   can silently tolerate a whole `(invariant, deal_type)` cluster with no red
   in CI.
3. **Doc/code drift inside the invariant module**: `pricing_invariants.py:44`
   documents `T2-COC-AT-BAR`; the code raises `T2-COC-ON-DIAL` (`:634`).
   `T2-TEMPERATURE`, `T2-OFFERABLE`, `T2-SELLER-FLOOR` are live but missing
   from the header index (`:13-49`).
4. **No hash/digest on either corpus** — `version: 1` is a hand-written literal
   (`pricing_harness.py:700`); freezing is enforced by list-of-dict equality
   against the seeded generator. There is **no regeneration script and no CI
   job** for regeneration; the only documented path is a `python -c` one-liner
   in a docstring (`:687-689`), and `write_valuation_corpus_v1` has no
   documented invocation at all.
5. **Two factor-register tests are source-text greps**
   (`test_factor_register.py:121,131`) — they assert string literals appear in
   `app/workers/routing.py`; a behavior-preserving rename fails them, and a
   refactor that preserves the string while breaking the wiring passes.
6. **Zero margin** at `test_pricing_unpriceable.py:173`: asserts
   `len(cases) >= 16` against exactly 16 tagged corpus cases.
7. **Path fragility**: `tests/pricing/` works only because it has no
   `__init__.py` (pytest prepend mode); `tests/oracle/` has one and hand-rolls
   a path insert. Nothing in config asserts either.
8. **`test_bench_pricing.py` is not underwriting** despite its name — it tests
   OpenRouter token/image cost parsing (`app.vision.bench.pricing`). Exclude it
   from underwriting-coverage counts.

## Implication for the lead product

The trust boundary sits exactly where the product boundary now sits. A buyer
does not purchase "the solver obeyed its ruleset"; they purchase **ARV, rehab,
carrying costs, and a price**. Every one of those is an *input* to the proven
math, and inputs are the unproven half:

| Number a buyer sees | Proven by the suite? | Actual evidence |
|---|---|---|
| Strategy/price given inputs | **Yes** — 26+11+3 invariants, oracle, 9 seeds | Strong |
| ARV | No | `BACKTESTED` 0; accuracy gate unmeasured |
| Rehab (from condition tier) | No | 1.8% of book vision-derived; rest heuristic |
| Taxes + insurance | **No — actively wrong once measured** | FL n=6: understated 5×–6.7× on every property |
| Rent | No | LLM-extracted, ungated lane, no eval |

**The first eval for the lead product should therefore target inputs, not the
solver.** Building a solver eval would re-prove what is already the
best-evidenced thing in the repo while leaving the measured 5×–6.7× error
untouched.
