# Statistics Formulary

> Part of the **Adaptive AI Systems Playbook** v0.1.1 · [Index](../README.md) ·
> Governing chapter: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

Reference file, not a chapter — no independent authority. Chapter 04 states
*when* to reach for each formula and what decision it feeds; this file gives
the derivation, symbols, and failure modes.

**Precedence — one total order, the same in every file of this playbook:**
`00 (principles) > chapters > GLOSSARY (definitions) > references (derivations)`.
References sit last: where this file disagrees with chapter 04, chapter 04 wins
and this file has a bug; where a *term* is at stake, GLOSSARY governs its
definition — but a definition never grants a permission a principle withholds.

Every entry carries **assumptions**, the **formula** with symbols and units
defined, a **worked example** using invented, round, explicitly-labeled
*illustrative* numbers (no number here is a measured result — those live in
[`examples/`](../examples/README.md)), and **when this breaks**.

**Notation is local to each section** — the same letter (`k`, `n`, `p`) means
different things in different formulas (`k` = clusters in §2/§3b, passes in §6,
repetitions in §8; `n` = items in §1, anchor items in §13); read the symbol
table you're using, don't carry a meaning across sections.

| § | What it answers |
|---|---|
| [1](#1-standard-error-for-binary-scores) | How wide is the interval around one pass rate? |
| [2](#2-clustered-ses-icc-design-effect-effective-n) | How much independent evidence does a clustered suite actually carry? |
| [3](#3-minimum-detectable-effect-mde) | What is the smallest difference this design can resolve? |
| [4](#4-paired-difference-ses-vs-two-sample-ses) | What does same-item pairing buy? |
| [5](#5-power-for-two-proportions-reference-form) | Two independent cohorts — how many items per arm? |
| [6](#6-curtailment-arithmetic) | When may a run stop early without breaking inference? |
| [7](#7-sequential-rule-admissibility) | Is an i.i.d.-calibrated sequential rule usable here at all? |
| [8](#8-passk-unbiased-estimator-vs-passk-reliability) | Capability under retry vs. reliability under repetition. |
| [9](#9-routing-break-even) | At what offload share does a router pay — including misroute cost? |
| [10](#10-rent-vs-buy-break-even-h) | Own or rent the hardware? |
| [11](#11-binomial-margin-of-error-by-sample-size) | How big a sample for a given margin, before any data? |
| [12](#12-prediction-ledger-scoring) | Is the forecasting process calibrated? |
| [13](#13-cohens-κ-and-its-confidence-interval) | How much anchor data does a trustworthy judge-agreement number need? |
| [14](#14-outcome-measurement-error-and-attenuation) | What does a noisy grader do to the effect and to required N? |

---

## 1. Standard error for binary scores

**Assumptions:** outcomes are independent draws (no
[clustering](../GLOSSARY.md#clustering-unit) — see §2 if they are); the score
is genuinely binary at the unit being averaged.

```
SE(p̂) = √( p̂·(1 − p̂) / n )
95% CI ≈ p̂ ± 1.96 · SE(p̂)
```
`n` = items scored (count); `p̂` = sample pass rate (proportion).

**Why the unit has to match what you measured.** Valid only when the average
is over 0/1 pass indicators at the level treated as one trial. Two common
misuses: averaging continuous rubric scores with this formula instead of
`SE = s/√n` on the real sample variance `s²`; and averaging a metric that is
actually a mean-of-strata-means, which silently assumes independence §2
usually contradicts.

**Worked example (illustrative).** `n=200`, `p̂=0.62`:
`SE = √(0.62×0.38/200) = 0.0343` → 95% CI ≈ **[55.3%, 68.7%]**.

**When this breaks:** non-binary scores scored as Bernoulli; clustered
outcomes (understates SE, go to §2); `p̂` near 0/1 with small `n` (use exact
Clopper–Pearson, not this Wald interval, once `n·p̂` or `n·(1−p̂)` < ~10.

Evidence: [EXT-STATS-001].

---

## 2. Clustered SEs, ICC, design effect, effective N

**Assumptions:** outcomes correlate within a
[clustering unit](../GLOSSARY.md#clustering-unit) (scenario class, document,
template, session); cluster sizes roughly balanced (unbalanced correction
below).

**ICC via one-way ANOVA on per-cluster indicators.** `k` clusters, cluster
`j` size `m_j` (average `m`), mean `x̄_j`, grand mean `x̄`, item outcomes `x_ij`:

```
MSB = Σ_j m_j·(x̄_j − x̄)² / (k − 1)
MSW = Σ_j Σ_i (x_ij − x̄_j)² / (N − k)
ICC = (MSB − MSW) / (MSB + (m − 1)·MSW)
DEFF = 1 + (m − 1)·ICC          N_eff = N / DEFF
```
For binary data, cluster `j`'s within-SS has closed form `m_j·x̄_j·(1−x̄_j)`.
`ICC=0` recovers `DEFF=1`, `N_eff=N`. Never assume it — estimate it.

**The paired-difference form.** When the analysis unit is a per-item
difference `d_i = x_i^A − x_i^B` (the usual case, §4), estimate ICC on the
`d_i` series with the same machinery — **not** the same number as either
arm's marginal ICC.

**Worked example (illustrative).** 4 clusters × 5 items, `N=20`.
Marginal, pass counts A=4,B=2,C=5,D=1 (rates .80,.40,1.0,.20; grand mean .60):
```
MSB = 5·[.04+.04+.16+.16]/3 = 0.667      MSW = (0.8+1.2+0+0.8)/16 = 0.175
ICC = (0.667−0.175)/(0.667+4×0.175) ≈ 0.36
DEFF = 1+4×0.36 = 2.44   →  N_eff = 20/2.44 ≈ 8.2
```
Paired-difference, per-item `d_i` within cluster (A:`[1,1,0,0,0]`,
B:`[1,0,0,0,0]`, C:`[1,1,1,0,0]`, D:`[0,0,0,0,−1]`; means .40,.20,.60,−.20):
```
MSB = 5·[.0225+.0025+.1225+.2025]/3 = 0.583   MSW = 4.00/16 = 0.25
ICC_diff = (0.583−0.25)/(0.583+1.0) ≈ 0.21
DEFF_diff = 1.84   →  N_eff_diff = 20/1.84 ≈ 10.9
```
The two ICCs (0.36 vs 0.21) differ — clustering in raw scores and in
differences is not the same quantity. Estimate ICC on the actual analysis
unit; do not borrow a marginal-arm ICC for a paired analysis.

**When this breaks:** unbalanced clusters — use Fleiss's
`m₀=(N−Σm_j²/N)/(k−1)` in place of `m`; small `k` (as above) gives a
high-variance ICC estimate — for estimating ICC itself, more clusters beats more
items per cluster (§3b has the power analog and its saturation limit); multiple
simultaneous clustering dimensions — identify
the coarsest binding unit or move to a mixed-effects model; negative ICC
estimates from small `k` — cap at 0 and investigate.

Evidence: [EXT-STATS-001]; [SCENARIO: SCENARIO-02].

---

## 3. Minimum detectable effect (MDE)

### 3a. McNemar discordant-pair form

**Assumptions:** paired binary outcomes, same items, two arms; only
discordant pairs (arms disagree) carry information.

**MDE ≤ discordance rate.** `n₁₀`=A-pass/B-fail, `n₀₁`=B-pass/A-fail,
`n_d=n₁₀+n₀₁`, `pd=n_d/N`, raw difference `δ=(n₁₀−n₀₁)/N`. Since `n₁₀≤n_d`
and `n₀₁≥0`: **`|δ| ≤ n_d/N = pd`**. No design detects a difference larger
than the rate the arms actually disagree — a concordant item (both pass or
both fail) contributes nothing regardless of a true capability gap; more
volume of non-discriminating items doesn't raise the ceiling.

**Vendor power table — read the units and the assumption first** (exact
binomial test, live as of 2026-08-21, 80% power, α=.05)
[FOLLOW: NV-EVALSDK-001]:

| Discordant pairs `n_d` | 10 | 50 | 100 | 500 | 1,000 |
|---|---|---|---|---|---|
| MDE on the overall pass-rate difference `δ` | ~28pp | ~12.5pp | ~8.8pp | ~3.9pp | ~2.8pp |

**Units:** the MDE row is in *overall pass-rate-difference* units (`δ` as
defined above, points of the full-suite rate) — **not** in discordant-split
units (`q` against 0.5, which is what the exact binomial test itself operates
on; the same designs in `q` units are far coarser).

**Implied assumption:** MDE is not a function of `n_d` alone. From the
identity `N = n_d/pd`,
```
MDE ≈ (z_α/2 + z_β) · pd/√n_d  ≡  (z_α/2 + z_β) · √(pd / N_eff)
```
so every entry above silently pins a *discordance rate*: all five columns
imply `pd ≈ 0.32`, equivalently `N ≈ 3.16·n_d`. (Cross-check: `pd=0.32` at
`N≈316` gives `2.80×√(0.32/316) ≈ 8.9pp`, the table's 100-pair column.)
**Do not read this table at other discordance rates** — a design that
disagrees more often needs more items for the same MDE, and borrowing a row
across discordances pre-registers an MDE the design cannot deliver, which
later reads an unresolvable margin as "above MDE."

**Compute your own `pd × N_eff` grid instead** (α=.05, 80% power, so
`z_α/2+z_β = 2.80`; illustrative round inputs; a cell where MDE > `pd` is
incoherent by §3c and marked):

| `pd` (row) / `N_eff` (col) | 50 | 100 | 200 | 500 |
|---|---|---|---|---|
| 0.10 | 12.5pp *(> pd — infeasible)* | 8.9pp | 6.3pp | 4.0pp |
| 0.20 | 17.7pp | 12.5pp | 8.9pp | 5.6pp |
| 0.32 | 22.4pp | 15.8pp | 11.2pp | 7.1pp |
| 0.45 | 26.6pp | 18.8pp | 13.3pp | 8.4pp |

Use the grid for pre-data sizing only; **reproduce the vendor's exact
binomial test on your own `pd` for a real decision** — the closed form above
is the normal approximation to it.

**Design-sizing approximation** (`heuristic`, not the vendor's exact-test
method), in *discordant-split* units: treat `q=n₁₀/n_d` as a proportion
against null 0.5:
```
n_d ≈ (z_α/2 + z_β)² / (4·(q − 0.5)²)
```
This answers "how many discordant pairs," not "how many items" — convert with
`N = n_d/pd` before writing an item count into a contract.

### 3b. Cluster-robust paired-t form

**Assumptions:** clustering material (§2's ICC ≉ 0, against the materiality
bar §7 requires you to state); analysis unit is per-cluster mean paired
difference `d̄_j`.

```
MDE ≈ (t_α/2,df + t_β,df) · SD(d̄_j) / √k        df = k − 1
```
`k`=clusters; `SD(d̄_j)`=SD of the `k` cluster means. `Var(d̄_j) = σ_b² + σ_w²/m`
(between-cluster variance plus the within-cluster contribution): adding items
inside a cluster (`m↑`) shrinks the second term toward zero, so replication does
buy power — but only down to the between-cluster floor `σ_b`, at which point
**only cluster count `k` reduces the MDE further** (`√k` alone sits in the
denominator once the floor binds). Equivalently, `N_eff = km/(1+(m−1)·ICC)` is
increasing in `m` for ICC < 1 with diminishing returns, saturating at `k/ICC` as
`m → ∞` (and equal to exactly `k` when ICC = 1); it is linear and unbounded in
`k`. Under material clustering, prefer independent clusters; replications help
until they don't.

**Worked example (illustrative).** `k=10`, `SD(d̄_j)=0.12`, α=.05 two-sided
(`t_.025,9=2.262`), 80% power (`t_.20,9≈0.883`):
```
MDE ≈ (2.262+0.883)×0.12/√10 = 3.145×0.12/3.162 ≈ 0.119 → ~12 points
```
With 10 clusters the MDE stays large however many items each cluster holds, once
within-cluster noise is averaged down to the between-cluster floor.

### 3c. MDE ≤ discordance, restated

Not McNemar-specific: any paired comparison's detectable effect is bounded
by how often the arms actually differ on the same items; cluster-robust
correction (§3b) changes how much power a given discordance buys, not the
bound itself. Every contract states its MDE; below-MDE margins are
[INCONCLUSIVE](../GLOSSARY.md#inconclusive), never a difference or equivalence.

**When this breaks:** treating the normal approximation (3a) as the exact
result; borrowing a vendor row at a discordance rate other than the one it
assumes; running McNemar without checking clustering first — under
clustering McNemar is secondary and *anti-conservative* (overstates power
by treating discordant pairs as independent), §3b is primary; reading a
sub-MDE margin as "roughly the same" or "clearly different";
**judge- or annotator-graded outcomes** — every form here assumes the
per-item outcome is observed without error, so a noisy grader attenuates the
difference and inflates the required `N_eff` beyond what these formulas
return (§14 gives the correction; §13 gives the reliability input).

Evidence: [EXT-STATS-001]; [NV-EVALSDK-001].

---

## 4. Paired-difference SEs vs. two-sample SEs

**Assumptions:** "paired" means the literal same item, under an otherwise
frozen [execution system](../GLOSSARY.md#execution-system), scored by both
arms.

```
Var(d̄) = [σ_A² + σ_B² − 2·ρ·σ_A·σ_B] / n            (paired)
Var(X̄_A − X̄_B) = σ_A²/n_A + σ_B²/n_B                (two-sample)
```
`ρ` = correlation between arms' per-item outcomes (item-difficulty
correlation). Equal variances, equal `n`: variance ratio is exactly `(1−ρ)`:
```
Paired SE = Two-sample SE × √(1 − ρ)
```
`ρ>0` (harder items are harder for every arm — typical) means pairing
**tightens the SE for free**; same-item comparisons must claim it.

**Worked example (illustrative).** `σ_A=σ_B=0.45`, `n=100`, `ρ=0.40`:
```
Two-sample SE = √(0.45²/100 + 0.45²/100) = 0.0636
Paired SE     = √(2×0.45²×0.60/100)      = 0.0493   (ratio ≈0.775, ~22.5% tighter)
```
Required `n` scales with SE², so pairing at `ρ=0.40` needs only `(1−ρ)=0.60`
of the two-sample items for equal power — ~40% fewer items.

**When this breaks:** same-*name* items treated as paired when harness
context/ordering/retrieval differed per arm; assuming `ρ>0` without
measuring it (`ρ≤0` widens paired SE relative to two-sample); using the
two-sample formula (§5) on genuinely paired data (wastes free power, does
not inflate false positives).

Evidence: [EXT-STATS-001].

---

## 5. Power for two proportions (reference form)

**Assumptions:** genuinely independent samples (disjoint items or cohorts —
same-item designs use §4 instead); no clustering (else substitute `N_eff`).

```
n per arm ≈ 2·p̄·(1 − p̄)·(z_α/2 + z_β)² / δ²      p̄=(p₁+p₂)/2, δ=p₁−p₂
δ_MDE      ≈ (z_α/2 + z_β) · √(2·p̄·(1 − p̄) / n)
```

**Worked example (illustrative).** `p̄≈0.75`, `n=150`/arm, α=.05, 80% power:
```
δ_MDE ≈ 2.80×√(2×0.1875/150) = 2.80×0.05 = 0.14 → ~14 points
```

**When this breaks:** same-item designs run through this instead of §4
(leaves free power unclaimed); clustered items ignored (substitute `N_eff`
first); `p̄` far from 0.5 with small `n` (pooled-variance approximation
least accurate near the extremes — use exact methods).

Evidence: [EXT-STATS-001].

---

## 6. Curtailment arithmetic

### 6a. Certainty curtailment

**Assumptions:** pre-registered bar `b` (0–1), planned total `N`; the
[consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance)
framework is in force — curtailment fires into a named consequence, never
a silent stop.

```
HALT when: k + r < ⌈b·N⌉
```
`k`=passes so far; `r`=items remaining; `⌈b·N⌉`=bar as an integer count.
`k+r` is the best possible final total (every remaining item passing).

**Proof it cannot inflate the arm's own type-I error.** Deterministic
arithmetic, not inference: `k` is fixed, `k+r` is the maximum achievable
total by construction. If `k+r < ⌈b·N⌉`, failure is certain over *every*
possible completion — regardless of ordering, independence, or any
distributional assumption. The rule fires only when the outcome is already
fixed, so halting produces the identical decision completion would have —
zero added false-positive/negative probability. Contrast an i.i.d.-calibrated
sequential test (§7), which draws a *probabilistic* conclusion under a
modeling assumption that can be violated; curtailment asserts no probability,
so it has no calibration to break.

**Worked example (illustrative).** `b=0.60`, `N=50`. After 30 items, `k=12,
r=20`: `32≥⌈30⌉` → continue. After 40 items, `k=14, r=10`: `24<30` → **HALT**,
escalate, report the interval `[14,24]/50 = [28%,48%]`.

### 6b. Why partial point estimates are compositionally biased

`k/(items executed)` after a curtailed halt is biased two ways: curtailment
fires only on arms already trending below bar, so the executed prefix is
not representative of a full-`N` run; and if execution order is
stratum-blocked rather than
[round-robin](../GLOSSARY.md#round-robin-ordering), the prefix over/under-
represents specific strata independent of the first bias. **Licensed report:
the certain interval `[k, k+r]/N`**, plus which items never ran — never a
single point value.

### 6c. The paired-comparison firewall

If arm B is curtailed early while A runs to completion, and a McNemar
comparison is then computed on only the items both arms have, the dropped
items are not random — they're the last-scheduled strata. McNemar's
statistic depends only on discordant pairs (`n₁₀`,`n₀₁`); dropping specific
strata shifts which pairs are discordant whenever failure rates vary by
stratum, moving the p-value in a direction scheduling determined, not new
information. **Rule: a curtailed arm's results never enter a paired
comparison, ranking, or leaderboard** — only the interval (6b) and a
standalone descriptive report are licensed. The argument is first-principles
(above); it has been *demonstrated on a real comparison in a counterfactual
replay* [SCENARIO: SCENARIO-01] — curtailing one arm and recomputing the paired test
on the items both arms retained moved the p-value materially, by composition
alone. No live instance of a curtailed arm entering a paired comparison is
recorded: the rule exists so there never is one.

### 6d. Count-to-k curtailed exact counting

For a tolerance "at most `m` violations in `n` items": halt at violation
`m+1`, escalate to the named consequence. A **count, not a hypothesis
test** — no error-rate claim, so no clustering calibration to break
(contrast §7); correctness doesn't depend on execution order, only how
*early* it fires does (round-robin makes an early halt representative
rather than a scheduling artifact).

**Worked example (illustrative).** Tolerance: at most 2 violations in 40.
Halt at the 3rd violation, whichever case that is — no distributional
assumption needed.

**When this breaks (6a–6d):** treating curtailment as a hypothesis test
(attaching a p-value to the halt itself); reporting a curtailed arm's point
rate as if it were the true rate; letting a curtailed arm into any paired
comparison; curtailing on a metric other than the pre-registered one;
adopting curtailment for speed rather than decision quality — a speed
rationale for a stopping rule is [REJECTED].

Evidence: this playbook's own machinery, corroborated by the pre-specification
consensus [EXT-STOPPING-002]; [SCENARIO: SCENARIO-01].

---

## 7. Sequential-rule admissibility

**What this checks:** whether an i.i.d.-calibrated sequential stopping rule
(SPRT, group-sequential/spending-function designs, always-valid confidence
sequences) is admissible at all — not an assumption to make, one to verify.

**The mechanism.** These rules' type-I error guarantee (≤α at any stopping
time) assumes each observation is an independent draw conditional on the
null. When outcomes [cluster](../GLOSSARY.md#clustering-unit) and execution
order groups same-cluster items (blocked/stratum-ordered — all of one class,
then the next), the running tally at an early look reflects far fewer
independent pieces of evidence than its raw count implies, but the boundary
calculation still divides by the raw count. Nominal α inflates: the boundary
is crossed under the null more often than calibration promises, because one
early cluster's correlated result masquerades as many independent
confirmations.

**Why blocked ordering is the worst case.** An early run under blocking
observes only a few clusters; if whole clusters deviate together (the
definition of clustering), the test sees an apparent long streak that is
one correlated draw repeated `m` times — and boundary-crossing rules are
maximally fooled by early streaks.
[Round-robin ordering](../GLOSSARY.md#round-robin-ordering) makes every
prefix touch a representative slice of every cluster, so the running
statistic's effective sample size tracks its raw count much more closely at
every look — this doesn't eliminate the clustering problem (final inference
still needs the DEFF correction, §2) but removes blocking's worst-case
amplification for a rule making claims *during* the run.

**The independence check, run before adopting any such rule** — a pre-data
obligation, recorded in the frozen contract's statistical plan (04 §7)
alongside ICC, DEFF and MDE, with a named owner:

1. Identify the clustering unit(s) (§2).
2. Estimate ICC on pilot data, on the analysis unit the rule will read.
3. Confirm execution order is interleaved/round-robin, not blocked.
4. If clustering is material and blocking can't be avoided, use curtailed
   exact counting (§6) instead — it asserts no probabilistic guarantee, so
   it is immune to this failure mode.
5. Even with low clustering and confirmed interleaving, simulate the
   realized α **on your own cluster structure and execution order** before
   trusting the nominal boundary. The motivating case study measured a
   realized error rate of roughly twice nominal under material clustering
   with blocked ordering [SCENARIO: SCENARIO-01]; the multiplier depends on ICC,
   cluster count, and boundary shape — simulate for your own design, never
   assume a figure (including that one).

**[PARAMETER] Materiality threshold for step 4.** "Material" is a design
decision, not a universal constant: state it as a design-effect bar on the
analysis unit — a defensible starting point is `DEFF ≥ 1.2` (i.e.
`ICC ≥ 0.2/(m−1)` at average cluster size `m`) — and calibrate it against
what a lost item of effective N costs this decision. Record the chosen bar in
the contract; do not leave it to the reader of the result.

**[PARAMETER] Pass criterion for step 5.** **PASS = simulated realized α ≤
1.2 × nominal**, simulated under the null on the project's own cluster
structure and planned execution order, with the **simulation script and its
seed recorded in the contract**. Anything above the bar → the rule is
**inadmissible**; fall back to curtailed exact counting (§6). The `1.2`
multiplier is itself a project parameter — choose it from what one
inflated false positive costs the decision (a Tier-3 decision should hold a
tighter bar than an exploratory one) and record the chosen value; what is
*not* optional is that the check has a stated number, a recorded artifact,
and a consequence. A check with no threshold cannot be passed or failed, and
a detection without a consequence is not a control.

**[REJECTED]** (condition: outcomes cluster within ordered execution
groups) — i.i.d.-calibrated sequential rules [EXT-STOPPING-001] are
inadmissible without a **passed** check as defined above (threshold stated,
simulation and seed recorded, consequence executed on failure).
Pre-registering the rule and letting it execute rather than investigator
judgment [EXT-STOPPING-002] fixes *which rule runs*, not whether that rule's
calibration assumption holds on this data — it does not by itself rescue
admissibility.

**What remains admissible:** curtailed exact counting (§6), always,
regardless of clustering; a sequential rule, once outcomes are confirmed
independent or the clustering unit is exhausted at the between-look level —
measured, not assumed.

Evidence: [EXT-STOPPING-001] (`contested` under clustered execution);
[EXT-STOPPING-002] (`consensus` for which rule runs, not a calibration
substitute); [SCENARIO: SCENARIO-01] (the one measured α-inflation instance, from a
replay); [SCENARIO: SCENARIO-02] (the clustering structure that causes it).

---

## 8. pass@k unbiased estimator vs. pass^k reliability

**Assumptions:** `n` independent attempts sampled per task (`n≥k`), `c`
correct; pass^k additionally requires the `k` combined attempts be genuinely
independent (fresh session/context).

**pass@k** (Chen et al., unbiased): probability at least one of a random
size-`k` subset of the `n` attempts is correct:
```
pass@k = 1 − C(n−c, k) / C(n, k)          (C(n−c,k)=0 when k > n−c, so pass@k = 1: certain pass)
```
Computed exactly from all `n` attempts — not by re-sampling `k`-subsets
(higher variance, biased at small `n`). Large-`n` limit:
`pass@k → 1 − (1−p)^k`, `p` = single-attempt pass probability.

**pass^k** (reliability under repetition): probability `k` independent
attempts on the *same* task all succeed: `pass^k = p^k`. **`p` is per task**
— pass^k is measured as the share of tasks succeeding on all `k` independent
attempts, never as (aggregate pass rate)^k. Substituting a suite-wide rate
*understates* pass^k whenever task difficulty varies (by Jensen,
`E[p_i^k] ≥ (E[p_i])^k`), and the gap widens with `k` and with the spread of
difficulty — the opposite direction from the correlated-failure error below,
and just as wrong. pass@k answers "does
at least one of k tries succeed" (capability under retry); pass^k answers
"do all k succeed" (reliability under unattended repetition). They diverge
sharply as `p` moves from 1 or `k` grows.

**Collapse illustration (illustrative `p`, `k=3`/`k=8`):**

| p | pass@3 | pass^3 | pass^8 |
|---|---|---|---|
| 0.95 | 99.99% | 85.7% | — |
| 0.85 | 99.7% | 61.4% | 27.2% |
| 0.70 | 97.3% | 34.3% | — |
| 0.60 | 93.6% | 21.6% | — |

At `p=0.85`, pass@3 rounds to "capable at essentially every task," while
pass^8 — an unattended 8-step workflow at the same per-step reliability —
succeeds barely a quarter of the time. A reliability claim reports pass^k on
a declared subset, never pass@k alone.

**When this breaks:** marketing high pass@k as a reliability claim; computing
pass@k by re-sampling instead of the exact estimator; raising an *aggregate*
pass rate to the `k`-th power instead of averaging per-task pass^k (see
above); reporting pass^k from too few tasks without a confidence interval
(§1/§11); assuming attempt independence when session state/caching carries
information between "independent" attempts.

Evidence: [EXT-AGENT-001].

---

## 9. Routing break-even

**Assumptions:** a gate/router decision (feature-based or classifier-style)
runs before inference spend, then the item resolves on exactly one tier —
not the weak-first-always-attempt cascade this playbook defaults to
(chapter 08), whose cost algebra differs (below).

```
avg_cost(s) = C_gate + s·C_weak + (1 − s)·C_strong
s* = C_gate / (C_strong − C_weak)          [break-even offload share]
```
`C_gate`=routing/judging cost per item; `C_weak`/`C_strong`=cost to resolve
an item per tier; `s`=offload share (fraction resolved by weak tier).
[ADAPT: EXT-SWITCHYARD-001] for the formula; the cost/accuracy figures
reported alongside it in the source are conditioned on a specific model
pairing and do not generalize.

**False-negative cost extension** (`inference`, first-principles, not
independently sourced). Compute-only break-even ignores misrouting cost.
`e` = the gate's false-negative rate **among offloaded items** (items kept at
the weak tier that should have escalated — an escalated item cannot produce a
gate false negative, so this cost accrues only on the `s` share); `L` = priced
cost of a silently-shipped failure (per
[consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance)):
```
avg_cost(s) = C_gate + s·C_weak + (1 − s)·C_strong + s·e·L
s* = C_gate / (C_strong − C_weak − e·L)      [break-even vs. always-strong]
```
Setting `e=0` recovers the compute-only form. A leakier gate or costlier
failure eats the per-item saving `C_strong − C_weak` and so raises the offload
bar; once `e·L ≥ C_strong − C_weak` the denominator is zero or negative and
**no offload share breaks even** — each offloaded item costs more in expected
failure than it saves in compute, and the gate should not ship.

**Worked example (illustrative).** `C_weak=$0.02`, `C_strong=$0.30`,
`C_gate=$0.01`:
```
Compute-only:          0.01 / (0.30 − 0.02)        ≈ 3.6%
With e=0.05, L=$2.00:  0.01 / (0.28 − 0.05×2.00)
                     = 0.01 / 0.18                 ≈ 5.6%
```
Pricing the false-negative cost raised the bar by a factor of about 1.6
(3.6% → 5.6%), and would raise it without bound as `e·L` approaches the
`$0.28` per-item saving — which is why
routing economics must carry it wherever misroutes are consequential, and why
the honest question is *how close `e·L` sits to the per-item saving*, not
whether the bar moved.

**`s*` is a bound, not a sweep.** `e` and `s` move together as the gate
threshold moves: loosening the gate to offload more also admits harder items,
raising `e`. Evaluate `s*` at the `(s, e)` pair your chosen threshold actually
produces (measure both on the same held-out slice), and re-evaluate after any
threshold change — a break-even computed at one threshold does not license an
offload share reached at another.

**When this breaks:** reporting only compute-only break-even for a
consequential decision; charging `e·L` to every item instead of the offloaded
share (inflates the bar — the error direction that kills routing projects that
actually pay); measuring `e` on the whole population instead of on offloaded
items only; treating `s*` as stable (provider prices shift it — re-measure);
a population-average `s*` hiding where routing pays vs. loses by task type
(segment, chapter 08); ignoring gate latency in an SLA-bound
setting; applying this formula unmodified to a weak-first-always-attempt
cascade — there `C_weak` is sunk on every item, requiring the variant with
`C_weak` added as a fixed per-item cost.

---

## 10. Rent-vs-buy break-even (H*)

**Assumptions:** ownership and rental deliver equivalent capability over the
comparison window; power draw and rental rate are measured under
representative sustained load, not nameplate or idle figures.

```
H* = (P − S) / (L · 52 · (R − TDP_kW · e))
```
`P`=purchase price ($); `S`=salvage value at end of life ($); `L`=ownership
lifetime (years); `R`=market rental rate ($/hr); `TDP_kW`=sustained power
draw (kW); `e`=electricity price ($/kWh); `H*`=break-even usage (hours/week —
above it, own; below it, rent).

**Derivation.** Ownership cost over `L` years at `H` hrs/week:
`(P−S) + L·52·H·TDP_kW·e`. Rental cost for the same usage: `L·52·H·R`. Solve
for `H` at equality.

**Worked example (illustrative).** `P=$2,000`, `S=$400`, `L=3`, `R=$0.60/hr`,
`TDP_kW=0.35`, `e=$0.15/kWh`:
```
R − TDP_kW·e = 0.60 − 0.0525 = 0.5475
H* = 1600 / (3×52×0.5475) = 1600/85.41 ≈ 18.7 hours/week
```

**Honest-utilization warning.** `H*` thresholds *sustained, representative*
demand, not busy-percentage within one run — near-100% utilization during
one intense week can coexist with near-zero average weekly demand. Drive the
decision from a [demand ledger](../GLOSSARY.md#demand-ledger) tracking actual
hours/month (including honest zero/not-run periods), never from a single
run's peak utilization [SCENARIO: SCENARIO-05]. Understating `TDP_kW` biases `H*`
low, making ownership look easier to justify than it is (the dangerous
direction); overstating it biases toward renting (the safe direction if you
must estimate rather than measure).

**When this breaks:** mid-life hardware failure shortens real `L` below
plan; `R` from a single volatile-market snapshot (re-verify at order time,
chapter 11); no time-value-of-money discounting on `P`; using one run's
busy-percentage as the `H` input instead of the demand ledger [SCENARIO: SCENARIO-05]; the formula answers own-vs-rent for an already-chosen
configuration — it does not say which configuration to price.

Evidence: first-principles TCO algebra (`inference`); [EXT-HW-001] for the
market-snapshot discipline any `R`/`P`/`e` plugged in must carry.

---

## 11. Binomial margin of error by sample size

**Assumptions:** items are an effectively random draw (ordering-bias caveat
below); no clustering (else substitute `N_eff`, §2).

```
MOE_95 = 1.96 · √(0.5 × 0.5 / n) = 0.98 / √n
```
Worst-case (`p=0.5` maximizes variance) — right bound before any preliminary
estimate exists.

**Progressive-subset pattern (illustrative `n`):**

| n | 100 | 400 | 1,600 | 6,400 |
|---|---|---|---|---|
| Worst-case 95% MOE | 9.8% | 4.9% | 2.45% | 1.225% |

Quadrupling `n` halves MOE (the `1/√n` scaling made concrete). A live vendor
table shows the identical pattern at its own endpoints — roughly ±8.3 points
at `n≈140` down to roughly ±0.9 points at `n≈12,000`, matching this formula
exactly [ADAPT: NV-MODELOPTRESEARCH-001], as of 2026-08-21.

**First-N ordering-bias caveat.** Taking the *first* `n` items of a corpus
(e.g. a `--limit` flag) rather than a random/stratified subsample biases
`p̂` if the corpus isn't randomly ordered — common in generated or
appended-to corpora grouped by source/difficulty/date. This formula bounds
*sampling variance* around the true value only for an effectively random
draw; a biased first-N slice can miss by more than its own stated margin,
and **more `n` within the same biased ordering does not fix it** — bias
doesn't shrink with `n`, only variance does. [ADAPT: NV-MODELOPTRESEARCH-001]
states this explicitly for its own progressive-subset feature. Randomize
corpus order before subsetting, or use a stratified subsample; never report
a first-N result as final.

**When this breaks:** using the worst-case formula once `p̂` is known and far
from 0.5 (substitute `p̂(1−p̂)` for a tighter honest interval; worst-case is
for pre-data sizing only); small `n` or `p̂` near 0/1 (use an exact interval);
clustered items (substitute `N_eff`, which widens the true margin); first-N
ordering bias (a bias problem, not a variance problem — this formula
describes variance only).

---

## 12. Prediction-ledger scoring

**Assumptions:** a
[prediction ledger](../GLOSSARY.md#prediction-ledger) entry states a point
estimate, interval, and confidence level `c`, fixed before the run.

**Interval coverage.** `coverage_i = 1` if the realized outcome fell inside
the pre-registered interval, else 0:
```
coverage_rate = (Σ coverage_i) / N
```
A well-calibrated forecaster's stated-`c`% intervals should contain the
outcome roughly `c`% of the time. `coverage_rate` is itself a proportion over
`N` trials — its margin of error follows §11; don't read a gap from `c` as
miscalibration until it clears that margin.

**Calibration curve.** Bucket entries by stated confidence (60–70%,
70–80%, …); compute empirical hit rate per bucket. Plot stated confidence
(x) vs. hit rate (y): perfect calibration is the diagonal. Above the
diagonal = underconfidence; below = overconfidence — more common and more
dangerous, since decisions then trust narrower intervals than reality
supports.

**Worked example (illustrative).** `N=20` entries at stated 80% confidence;
14/20 outcomes fell inside their interval:
```
coverage_rate = 14/20 = 70%
n·(1 − p̂) = 20×0.30 = 6 < 10  →  §1 requires an exact interval, not Wald
Clopper–Pearson 95% CI for 14/20 = [45.7%, 88.1%]
```
The interval contains the nominal 80% — with only 20 entries, 70% observed
coverage isn't yet distinguishable from a genuinely well-calibrated 80%
forecaster.

*Why not §11's shortcut here.* §11's `0.98/√n` is the worst-case (`p=0.5`)
margin, valid **before** any `p̂` exists — pre-data sizing only. Once `p̂=0.70`
is in hand it is the wrong tool twice over: it ignores the known `p̂` (§11's
"when this breaks"), and at `n·(1−p̂)=6` the Wald form behind it is out of
range (§1). It would have printed a symmetric ±21.9 points → [48.1%, 91.9%],
too narrow below and too wide above the exact interval. The conclusion
survives either way; the discipline is the point — this file does not model
the shortcut it forbids.

**When this breaks:** judging calibration from too few entries without
checking §11's margin first; scoring only point accuracy while ignoring
interval coverage (misses systematic overconfidence with reasonable-looking
points); pooling entries across confidence levels without bucketing (masks
good calibration at one level, bad at another); treating one experiment's
prediction as proof the forecasting process "works" — calibration is a
property of the process measured over many entries.

Evidence: `inference` — this playbook's own instrument, reusing §11's
machinery; no independent external source specific to this ledger design.

---

## 13. Cohen's κ and its confidence interval

*status: doctrine — not yet exercised (see chapter 03 §5.7/§7 for what validation would look like)*

The algebra below is standard; what has no execution record in this playbook is
the judge-calibration protocol it sizes. Treat the sizing as a plan to be
checked against your own anchor data, not as a validated recipe.

**Assumptions:** two raters (a judge and a human anchor, or two humans) apply
the *same* label set to the *same* items, independently; labels are nominal;
the anchor set is representative of the items the judge will grade in
production; anchor items are the independent unit (if they are drawn from a
few documents or classes, they cluster — see the bootstrap note).

**Recap of the point estimate** (defined and worked in
[chapter 03](../03_EVALUATION_FOUNDATION.md) §8.3, not repeated here):
```
κ = (p_o − p_e) / (1 − p_e)
```
`p_o` = observed agreement (proportion); `p_e` = agreement expected by chance
from the two raters' marginals; `n` = anchor items (count). κ=0 is chance,
κ=1 is perfect, κ<0 is worse than chance. Chapter 03 mandates reporting κ
**with an interval**, every time; this section is that interval.

**Asymptotic SE (the standard form).**
```
SE(κ) ≈ √( p_o·(1 − p_o) / ( n·(1 − p_e)² ) )
95% CI ≈ κ ± 1.96 · SE(κ)
```
This is the large-sample form that treats the marginals — hence `p_e` — as
fixed. The full Fleiss–Cohen–Everitt variance additionally propagates
sampling error in the marginals and is what statistical packages report; the
two agree closely at balanced marginals and moderate `n`, and diverge as
marginals skew.

**Bootstrap alternative** — preferred whenever `n` is small, marginals are
skewed, κ is near 1 (the Wald interval overshoots), or anchor items cluster.
Resample **clustering units** (§2), not items, with replacement `B ≥ 2,000`
times; recompute κ on each resample; report the 2.5/97.5 percentiles. An
item-level bootstrap on clustered anchors understates the interval in exactly
the way §2 predicts.

**Anchor-ceiling note (read before blaming the judge).** κ(judge, anchor) is
bounded by the anchor's own reliability: noise in the anchor labels attenuates
the measured agreement toward 0 by the same mechanism §14 describes, so a
judge cannot demonstrate agreement beyond what the anchor set itself carries.
Three consequences: (1) measure human–human κ on a double-labeled subset
*before* reading κ(judge, anchor), and read the judge against that ceiling,
not against 1.0; (2) a κ that fails the judge-trust gate (chapter 03) with an
unmeasured anchor is an **undiagnosed** result — a bad judge and a noisy
anchor look identical and need different fixes; (3) raw agreement `p_o` is not
a substitute for κ — chance correction deflates it substantially, most where
marginals are skewed [EXT-JUDGE-003].

**Sizing: target CI half-width → required anchor `n`.** Invert the SE:
```
n ≈ z_α/2² · p_o·(1 − p_o) / ( h² · (1 − p_e)² )
```
`h` = target half-width of the κ interval, in κ units — chosen from the
decision the κ feeds (chapter 03's judge-trust gate names the bar; `h` must be
small enough to place κ on one side of it), not picked as a round number.

**Worked example (illustrative).** Expected `p_o = 0.85` with balanced binary
labels (`p_e = 0.50`), so κ ≈ 0.70. Target `h = 0.10`, α=.05
(`z_α/2² = 3.84`):
```
n ≈ 3.84 × (0.85×0.15) / (0.10² × 0.50²) = 3.84 × 0.1275 / 0.0025 ≈ 196 items
check: SE = √(0.1275 / (196×0.25)) = 0.051 → ±0.100 ✓
```
Scaling is §11's `1/√n`: halving `h` to 0.05 quadruples the requirement to
~784 anchor items, and a 50-item anchor set carries a half-width near ±0.20 —
it cannot separate a κ of 0.60 from a κ of 0.85, which is usually the exact
distinction the gate turns on.

**When this breaks:** Wald CI with κ near 1 or small `n` (bounds exceed 1 —
bootstrap instead); pooling κ across strata with different label prevalence
(κ is marginal-dependent — the same error pattern yields different κ at
different prevalence; report per stratum); reading κ as accuracy (it is
chance-corrected *agreement*, not correctness — §14 covers what imperfect
grading does to a downstream comparison); tuning the judge on the same anchor
items later used to certify it (§11's leakage failure in another costume);
an anchor set drawn from one document/class family (the interval is then
cluster-dependent, §2).

Evidence: `inference` — standard chance-corrected-agreement algebra applied to
this playbook's judge-calibration gate; [EXT-JUDGE-003] for the size of κ's
deflation against raw agreement. Governing chapter for the gate itself: 03.

---

## 14. Outcome-measurement error and attenuation

**Assumptions:** the per-item outcome is produced by an imperfect grader (an
LLM judge, a human annotator, a heuristic checker) with
`Se` = P(grader says pass | truly pass) and `Sp` = P(grader says fail | truly
fail), both **measured** on an anchor set (§13) representative of the items
being compared; error is **non-differential** (same `Se`/`Sp` in both arms)
and independent across items given truth. Every other section of this file
assumes `Se = Sp = 1`; this one prices that assumption.

**The attenuation relation (binary outcome).** Observed pass rate and observed
paired difference:
```
p*   = p·Se + (1 − p)·(1 − Sp)
δ*   = (p_A − p_B)·(Se + Sp − 1) = λ·δ        λ = Se + Sp − 1
```
`λ` (Youden's J) is the **attenuation factor**: grader error does not merely
add noise, it shrinks the true difference before any test sees it. Because the
MDE forms in §3 are stated on the *observed* scale, the smallest **true**
effect a design can resolve is `MDE/λ`, and the sample size needed to detect a
given true `δ` inflates by roughly:
```
N_required ≈ N_perfect-grader / λ²
```
(the `1/λ²` is the dominant term; the observed outcome's own variance also
shifts, second-order for `λ` near 1).

**Worked example (illustrative).** `Se = 0.95`, `Sp = 0.90` → `λ = 0.85`. A
true 10-point gap presents as 8.5 points; a design sized for 10 points under a
perfect grader needs `1/0.85² ≈ 1.38×` the `N_eff` — most efficiently bought as
~38% more independent clusters (§3b: replications saturate at `k/ICC`) — to hold
the same power. At `λ = 0.60` the multiplier is `1/0.36 ≈ 2.8×`.

**κ is not λ.** A κ figure alone does not determine the attenuation factor:
κ summarizes agreement, `λ` is a function of the two error *directions*, and
the same κ arises from very different `(Se, Sp)` pairs at different label
prevalence. Take `Se` and `Sp` straight off the judge-vs-anchor confusion
matrix — §13's anchor set already yields it — and use κ as the trust gate,
the confusion matrix as the power input.

**Differential error is bias, not attenuation.** If grader error differs by
arm — a judge rewarding longer outputs, an arm-identifying artifact in the
transcript, a rubric applied by someone who knows which arm is which — the
observed difference is biased in a direction **no amount of `N` fixes**, and
the sign can invert. Blind the grader to arm identity, randomize presentation
order, and grade both arms in one pass; a CONFIRMED verdict resting on
judge-graded outcomes MUST state that blinding in the contract.

**Record the input.** The grader reliability used in the power calculation
(κ, or `Se`/`Sp`, plus the anchor set it came from and its date) belongs in
the contract's statistical plan beside ICC, DEFF and MDE (04 §7/§8). A power
number computed at an unstated grader reliability is not reproducible, and its
MDE is optimistic by an unknown factor.

**When this breaks:** `λ ≤ 0` (a grader at or below chance carries no signal —
no `N` rescues it; fix the instrument, rung 0); the non-differential
assumption violated (see above — that is a bias problem, handled by blinding,
not by arithmetic); `Se`/`Sp` estimated on an easy or non-representative
anchor slice (§13); continuous or rubric-scored outcomes pushed through the
binary form (the analogue there is attenuation of a correlation by the square
root of the score's reliability — restate it before using it); treating
attenuation as a "safe" conservatism — it is conservative only for CONFIRMED,
while for INCONCLUSIVE it manufactures false negatives, which is the direction
that quietly kills real effects.

Evidence: `inference` — standard non-differential-misclassification algebra
applied to paired AI evaluations; the bridge between chapter 03's judge
calibration and chapter 04 §8's power machinery. No external source is claimed
for the specific `1/λ²` sizing rule beyond the algebra shown.

---

## Sources cited in this file

| ID | Role here |
|---|---|
| [EXT-STATS-001] | Bernoulli/clustered/paired SEs, power/MDE machinery (§1, §2, §3, §4, §5) |
| [NV-EVALSDK-001] | Live McNemar exact-test power table (§3a) |
| [EXT-STOPPING-001] | i.i.d.-calibrated sequential testing — admissibility conditions (§7) |
| [EXT-STOPPING-002] | Pre-specification doctrine — what it does and does not rescue (§7) |
| [EXT-AGENT-001] | pass@k estimator; pass^k reliability collapse (§8) |
| [EXT-SWITCHYARD-001] | Routing break-even formula — compute-only form (§9) |
| [EXT-JUDGE-003] | κ deflation against raw agreement; anchor-reliability reading (§13) |
| [NV-MODELOPTRESEARCH-001] | Binomial margin-of-error table + first-N ordering-bias caveat (§11) |
| [EXT-HW-001] | Market-snapshot discipline for rent-vs-buy inputs (§10) |
| [SCENARIO-01](../examples/SCENARIO-01_consequence-bearing-tolerances.md) | Curtailment guards; counterfactual replay of the paired-comparison firewall (§6) and the one measured sequential α-inflation instance (§7) |
| [SCENARIO-02](../examples/SCENARIO-02_clustered-eval-effective-n.md) | Clustering/effective-N collapse this file's §2 and §7 draw on |
| [SCENARIO-05](../examples/SCENARIO-05_hardware-purchase-discipline.md) | Honest-utilization warning for rent-vs-buy (§10) |

---

> [Index](../README.md) ·
> Governing chapter: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)
