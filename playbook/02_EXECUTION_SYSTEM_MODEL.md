# 02. Execution System Model

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) · [Index](README.md) · [Next →](03_EVALUATION_FOUNDATION.md)
> **Reading time:** ~15 min. **Prerequisites:** 00, 01.

## 1. Purpose and when to read this

Every later chapter compares numbers: model against model, prompt against prompt,
quantization against full precision, this week's run against last week's. All of
that rests on one question this chapter answers: **comparable to what, exactly?**
A "model comparison" that silently changed the runtime, the host, or the decoding
budget between arms is not a model comparison — [PRINCIPLE] P5 in chapter 00 states
this as a project-wide law. This chapter gives it a name, a component list, and a
measurement procedure.

Read this chapter before running any comparison that will drive a decision, and
again before any hardware, runtime, or provider migration. It is short and it is
foundational — chapter 03's instrument only means what it claims to mean if the
thing being measured is pinned.

## 2. Inputs required

- A [project profile](GLOSSARY.md#project-profile) (chapter 01) naming at least the
  candidate [execution surface](GLOSSARY.md#execution-surface)(s): local open-weights,
  self-hosted/rented, managed API, subscription harness, cloud agent environment.
- Whatever candidate models, runtimes, and hardware are already in scope (chapter 05
  formalizes selection; this chapter does not require selection to be finished).
- The [stakes tier](GLOSSARY.md#stakes-tier) from chapter 01, which sets how much
  pinning and probing is mandatory (§6).

## 3. Decisions this chapter supports

- What exactly must be frozen and recorded before a comparison is trustworthy.
- Which [reproducibility boundary](GLOSSARY.md#reproducibility-boundary) a project's
  causal claims are entitled to cross without a
  [contemporaneous paired control](GLOSSARY.md#contemporaneous-paired-control).
- Whether a change (runtime upgrade, quantization swap, host migration, provider
  redeploy) is "the same system, still comparable" or a new identity requiring
  re-measurement.
- Where a deployment target's hardware/format constraints must be decided *before*
  a training or optimization investment is sunk into an artifact that will not run
  there.

## 4. Normative principles

**[PRINCIPLE] The execution system is the unit of measurement.** (strong-evidence)
The full identity of the thing being measured — this playbook's
[execution system](GLOSSARY.md#execution-system) — is, verbatim:

```
ExecutionSystem =
    model
  + artifact / quantization / adapter
  + runtime / provider
  + hardware / host
  + harness
  + context policy
  + retrieval / knowledge
  + tools
  + workflow
  + generation / reasoning budget
  + verifier / grader
  + environment
```

A [comparability claim](GLOSSARY.md#comparability-claim) is a claim about the
*frozen* execution system, unless the experiment explicitly isolates one factor and
holds every other component fixed. **MUST NOT** collapse model, runtime, provider,
harness, and hardware into a single ambiguous label — "the model got better" is
twelve different possible claims wearing one sentence, and only one of them is about
the model. This is chapter 00's P5 instantiated: measurement validity before
comparison. Corroborated by field evidence that runtime/backend choice alone moves
scores by double-digit percentage points on identical model weights, independent of
any change to the model [EXT-PERF-003] (research-only; treat as a caution to verify
locally, not a load-bearing number).

**[PRINCIPLE] Reproducibility is measured, never assumed.** (strong-evidence)
Whether two runs of "the same" execution system agree is an empirical property of
the stack, not a default you are entitled to. Modern inference stacks are
non-deterministic even at temperature zero for reasons that have nothing to do with
sampling: floating-point reduction order in batched kernels varies with concurrent
GPU state, and this variance requires no concurrency to observe — a single session
restarted can reorder reductions differently the second time. KV-cache placement is
a secondary contributor. Batch-invariant execution modes exist to remove the
dominant source; where the engines named in this playbook's source ledger support
them (verified per engine, with dates, in [references/SOURCES.md](references/SOURCES.md)),
they ship **opt-in** at a material throughput cost (§10) — the default
configuration of a serving stack is not deterministic [EXT-DETERM-001]. Treat every
"the numbers should match" assumption as a hypothesis to probe (§5), not a starting
belief.

**[PRINCIPLE] A causal claim across a measured instability boundary requires a
contemporaneous paired control.** (strong-evidence)
When a [reproducibility boundary](GLOSSARY.md#reproducibility-boundary) probe (§5)
finds that outcomes are *not* stable across some axis — restart, host, concurrency,
provider redeploy — no comparison may cross that axis and still claim causal
attribution to one intervention. The only admissible design is a
[contemporaneous paired control](GLOSSARY.md#contemporaneous-paired-control): both
arms run in the same session/window, everything held fixed except the intervention,
order pre-registered and counterbalanced (e.g., AB/BA). Where a contemporaneous
control is unavailable, the causal claim **MUST** be declared unavailable and the
comparison relabeled descriptive. [SCENARIO: SCENARIO-12] is the field case this principle
generalizes from — restart instability large enough to flip a meaningful share of
per-item outcomes, addressed by scoping every causal comparison to the measured
boundary rather than assuming a wider one.

## 5. Default procedure

**Step 1 — Declare and pin an identity.** Before any run that will inform a
decision, record, for every execution-system component that has one: an artifact
digest (weights/adapter hash), a runtime/engine build identifier, host identity,
harness version, and a config snapshot (context policy, decoding parameters,
generation/reasoning budget, tool/verifier versions). This is the input to
[provenance](GLOSSARY.md#provenance) (chapter 13); do not defer it to "after the run
looks interesting" — by then the identity that produced the interesting number is
gone. A published-recipe convention worth following: ship the full execution recipe
alongside any result you intend others to trust, on the stated principle that the
goal is *methodological consistency with clear provenance*, not bit-wise identical
outputs across every reader's hardware [FOLLOW: NV-EVALRECIPE-001] (as-of the date
in [references/SOURCES.md](references/SOURCES.md)).

**Step 2 — Run the reproducibility-boundary probes relevant to your topology.**
Four probes, cheapest first. Run only the ones your deployment topology can cross;
skip a probe whose axis your system will never traverse (e.g., no cross-host probe
for a single pinned box that will never move).

| Probe | Tests | Design | A positive (unstable) result means |
|---|---|---|---|
| **Restart probe** | Same session vs. a fresh process on the same host | Run a fixed paired case set, restart the server, re-run the identical set, compare per-item outcomes | Comparisons **MUST** stay inside one session unless paired across the restart |
| **Concurrency probe** | Solo request vs. concurrent load | Run the same case set at concurrency 1 and again under representative concurrent load, compare | Any latency/throughput number and any correctness number both need a stated concurrency level |
| **Cross-host probe** | Same pinned artifact, different physical/virtual host | Run the identical case set on two hosts with the same declared identity | "Same identity" claims **MUST** be scoped to hosts actually probed, not assumed to generalize |
| **Provider-redeploy probe** | Managed-API identity stability across the provider's own maintenance | Re-run a fixed probe set against a managed endpoint after any provider-announced or observed redeploy | A provider-side model update mid-experiment is a **new** execution system, full stop |

Report each probe as an agreement rate (§8), not a pass/fail label — the rate is
what downstream chapters need to decide whether a paired control is required.
*status: doctrine — not yet exercised* for the concurrency and provider-redeploy
probes specifically (the restart and cross-host designs are exercised in
[SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md); see that case
for what a completed probe record looks like).

**Step 3 — Scope every comparability claim to the measured boundary.** If the
restart probe finds instability and the cross-host probe was never run, the license
you have is "comparable within a session on this host" — nothing wider. Write the
scope into the experiment contract (chapter 04), not into a footnote.

**Step 4 — Placing arms across nodes is permitted, under conditions.** A rented or
otherwise remote instance holding one full session per arm satisfies a
session-scoped reproducibility rule exactly as well as a single owned host does —
the rule is about the session boundary, not the machine's ownership. This licenses
running expensive arms on rented capacity (chapter 11) without weakening the
comparison, **provided**: (a) placement is pre-registered in the contract before
any case runs, not chosen opportunistically per arm; (b) the artifact digest is
independently verified on the remote host before the arm starts, not assumed from
the launch script; (c) the remote host's declared identity (driver/runtime versions,
hardware) is recorded exactly as it would be for an owned host; (d) the remote
surface is itself admissible under the project's written privacy/residency
requirement (11 Q0a/Q0b; 05 §5.2) — comparability licenses the *placement*, it
does not license the *surface*, and a held-out or regulated corpus lands only on
tiers the stakes-tier cloud policy (11 §8) admits.

**Step 5 — Quantize for the deployment target, not the development box.** Decide
where the frozen artifact will actually serve *before* investing in a quantization
or optimization pass, and verify the chosen format is supported there. Vendor
quantization formats are not universally portable across hardware generations —
some are locked to a single GPU architecture family and will not run, or will
silently take a slower fallback path, elsewhere [ADAPT: NV-NVFP4PLAYBOOK-001]. A
format chosen for the machine sitting in front of you, with no verification against
the deployment target, is a decision made by convenience rather than by the
requirement — see §9 and chapter 07's acceptance-gated escalation ladder for the
quantization decision itself.

## 6. Project adaptation parameters

**[PARAMETER] What counts as a "material" change that forces a new identity.**
Every execution-system component change is in principle a new identity; not every
one is worth re-probing at every stakes tier. Calibrate against consequence: at
Tier 1, a minor harness patch version bump MAY be treated as the same identity by
convention; at Tier 2+, any change to runtime, provider, quantization, or hardware
**MUST** trigger re-declaration (§5 Step 1) and, if a decision depends on
cross-change comparability, re-probing (§5 Step 2). State the project's own
threshold in writing rather than deciding case by case under pressure.

**[PARAMETER] Which probes are warranted, given topology.** A single-host,
single-provider, low-concurrency deployment may only ever need the restart probe.
A multi-host or autoscaled deployment needs the cross-host and concurrency probes
before any latency/throughput claim is trusted (chapter 06 depends on this). A
managed-API-only project needs the provider-redeploy probe and nothing else from
this list, since it has no host or restart axis to control.

**[PARAMETER] Authoritative clock per metric.** Environments with a virtualization
or container layer between the process and the hardware (containers, VMs, WSL2-class
compatibility layers) can let monotonic and realtime clocks disagree materially —
name which clock is authoritative for each reported metric in the experiment
contract. The dual-clock mechanics live in chapters 06 and 12
([dual-clock telemetry](GLOSSARY.md#dual-clock-telemetry),
[authoritative clock](GLOSSARY.md#authoritative-clock)); this chapter's obligation
is to recognize the hazard as part of "environment" in the execution-system
definition.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Identity-change gate.** On any change to a pinned execution-system
component: is the change material under §6's project threshold? If yes — re-declare
the identity (§5 Step 1); if the change crosses a probed reproducibility boundary,
re-run the relevant probe before trusting any comparison across the change.

**[STOP CONDITION] Unmeasured-boundary crossing.** Stop before running a comparison
that would cross a reproducibility axis (restart, host, concurrency, provider
redeploy) with no probe result for that axis. This is chapter 00's global tripwire
#3, operationalized: either run the probe first, run a contemporaneous paired
control instead, or relabel the intended claim as descriptive before proceeding.

**[STOP CONDITION] Format-portability mismatch.** Stop before committing optimization
or fine-tuning spend to an artifact format not yet verified against the deployment
target's hardware. Verify the format loads and serves correctly on target hardware
before, not after, the optimization pass that produced it.

## 8. Metrics and formulas

**Reproducibility agreement rate.** For a probe of *n* paired cases (same case,
same declared identity, compared across the probed axis — e.g., before/after a
restart), let *m* be the number of cases whose outcome (or, for a stricter check,
whose full output digest) is identical across the pair. The agreement rate is:

```
agreement_rate = m / n
```

Units: dimensionless, in [0, 1]. A rate below 1.0 confirms the axis is unstable and
triggers the contemporaneous-paired-control requirement (§4); it does not by itself
say how large a comparison must be to detect a difference under that instability —
that is chapter 04's clustering and MDE machinery, which treats the probed instability
as one more source of outcome correlation to model.

*Worked example (illustrative, invented round numbers).* A restart probe runs 20
paired cases before and after a server restart. 12 of the 20 cases produce an
identical outcome; 8 flip. `agreement_rate = 12/20 = 0.60`. A 60% agreement rate is
a strong instability signal — comparisons on this stack are scoped to "within one
session" until proven wider, and any restart-crossing comparison in this project's
history needs re-evaluation or a contemporaneous paired control before it can support
a decision.

**Artifact digest match rate.** For a set of hosts or redeploys expected to serve
an identical pinned artifact, the share whose computed digest matches the declared
digest. Any mismatch is a Step-4 (§5) placement failure, not a modeling result —
treat it as an integrity defect, not data.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Collapsing the execution system into one label.** "The model got better/worse"
  when the runtime, provider, quantization, harness, or generation budget changed
  is the anti-pattern P5 exists to forbid — the sentence names one component and
  silently changed several [SCENARIO: SCENARIO-06], [SCENARIO: SCENARIO-08].
- **Assuming determinism because a runtime supports a deterministic mode.**
  The two engines the source ledger verifies for this (see the EXT-VLLM-001 and
  EXT-SGLANG-001 rows) expose opt-in deterministic/batch-invariant modes at a
  throughput cost, and neither ships that mode as its default; support, defaults,
  and guarantees vary by engine and version, and other engines were not verified
  for such modes at all. Probe the actual frozen runtime (§5); never infer
  determinism from feature availability, and never assume a mode exists in an
  engine the ledger has not verified it for [EXT-DETERM-001].
- **Format-locked-to-hardware surprise.** Choosing or accepting a quantization
  format because it is convenient on the development machine, discovering only at
  deployment time that the target hardware does not support it or takes a silent
  slow-path fallback [ADAPT: NV-NVFP4PLAYBOOK-001].
- **Treating "same session" as "same identity forever."** A provider-side model
  update, a silent runtime auto-upgrade, or a host migration mid-experiment
  invalidates a previously-measured reproducibility boundary; the boundary is a
  property of a *specific* pinned identity, not a permanent fact about the project.

**Environment hazards across execution layers.** These generalize a recurring
pattern: a layered execution environment (container inside VM inside host,
interop shells, path-resolution across mounted filesystems) hides defects that
present as model or system weakness and are actually environment defects. None of
these are AI-specific, but AI-system experiments are unusually exposed to them
because comparisons depend on exact reproducibility. Check for, in order of how
often they recur:

1. **Name aliasing across a host/guest boundary.** The same command name can
   resolve to different programs depending on which layer invokes it. Verify the
   binary actually executed, not just its name, when a command's behavior seems to
   contradict its documentation.
2. **Interop mangling of inline arguments.** Commands issued across a
   virtualization/interop boundary can have inline variables or quoting silently
   altered in transit. Prefer writing the command to a script and executing the
   script over inline substitution when crossing such a boundary; better still,
   run the harness from inside the same layer the target process runs in.
3. **Existence is not executability.** A resolvable binary path is not proof the
   binary runs — platform application-store stubs and similar shims exist
   precisely to satisfy `which`/`command -v`-style checks while failing on
   invocation. Probe by executing a trivial command, not by checking existence.
4. **Environment configuration silently unread.** A serving script that only
   honors already-exported variables, or only reads a config file when invoked
   through one particular path, can serve a stale or wrong artifact after a
   restart with no error message pointing at the actual cause. Verify the
   declared identity (§5 Step 1) against what actually loaded, not against what
   the launch command intended to load.
5. **Baked absolute paths.** Binaries and virtual environments that embed absolute
   runtime-library or interpreter paths at build time break silently — not loudly
   — when the install location moves. Any relocation of an execution-system
   component's home directory is itself a Step-1 re-declaration event.
6. **Cross-layer package-manager namespace confusion.** A global package install
   run from one environment layer can land in a different layer's install prefix
   than the one the launch command actually uses.
7. **Filesystem-layer metadata loss.** Editing a file through a foreign filesystem
   interface (a network mount, a cross-OS interop mount) can silently drop
   executable permission bits; track modes in version control rather than trusting
   the filesystem to preserve them.
8. **Shared-host port/service collisions.** On a host running more than one
   project, a reused port silently routes traffic to the wrong service rather than
   failing to bind — treat "unexpected response from a known-good endpoint" as an
   environment-identity question before a model-behavior question.
9. **Clock validity under virtualization** (§6) — the environment component of the
   execution system, not a separate concern.

## 10. Vendor recipes

| Vendor / project | Verdict | What it gives you | As-of / caveat |
|---|---|---|---|
| Serving engine deterministic/batch-invariant modes [ADAPT: EXT-VLLM-001] | ADAPT | An opt-in flag trading throughput for reduction-order determinism | Verified active; opt-in, reduced throughput as of verification date — do not assume it is the default |
| Alternate serving engine deterministic mode [REFERENCE: EXT-SGLANG-001] | REFERENCE | An independent deterministic-mode implementation with a documented slowdown range | Verified active; consult before depending on cross-engine determinism comparisons |
| CPU/GPU single-slot engine [REFERENCE: EXT-LLAMACPP-001] | REFERENCE | A serving path whose single-slot model suits the determinism/provenance regime by construction (chapter 05 develops the regime choice) | Verified active; very frequent releases — pin the exact build in your identity record |
| Deployment-target quantization format guidance [ADAPT: NV-NVFP4PLAYBOOK-001] | ADAPT | A concrete instance of the format-portability trap (§5 Step 5, §9): a next-generation microscaling format documented as tied to one GPU architecture family | As-of verification date; re-check before relying on it — vendor format support windows move |
| Full-recipe-publication convention [FOLLOW: NV-EVALRECIPE-001] | FOLLOW | The stated goal — methodological consistency with clear provenance, not bit-wise identical outputs — matches this chapter's Step 1 exactly | As-of verification date; cite for the publication convention only, not for any specific pinning checklist |
| Git-versioned environment tooling [REFERENCE: NV-WORKBENCH-001] | REFERENCE | Environment/identity versioning across heterogeneous hardware targets | As-of verification date; does not provide run/eval tracking by design — the record of record (chapter 13) is still yours to build |

## 11. Worked examples

- [SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md) — a restart
  probe found a large share of case outcomes unstable across a mere server restart;
  the response was to scope causal comparisons to the measured boundary
  (same-session, contemporaneous paired controls) rather than to chase bit-identity.
- [SCENARIO-08](examples/SCENARIO-08_transport-serialization-defect.md) — a transport
  layer presented as transparent silently reordered structured output, breaking a
  downstream consumer that depended on byte-level fidelity; found only by explicit
  byte-equivalence verification, not by output inspection. A tool-contract instance
  of the layered-environment-hazard pattern in §9, developed fully in chapter 08.
- The agreement-rate worked calculation in §8 shows the arithmetic a restart probe
  produces before any case-level analysis begins.

## 12. Outputs and artifacts

- A declared execution-system identity (artifact digest, runtime/build identifier,
  host identity, harness version, config snapshot) for every run that will inform a
  decision — feeds [provenance](GLOSSARY.md#provenance) (chapter 13) and the
  execution-system identity field of every
  [experiment contract](templates/EXPERIMENT_CONTRACT.md) (chapter 04).
- A reproducibility-boundary probe record per axis actually probed (§5 Step 2),
  with its measured agreement rate (§8) — feeds the contract's comparability scope
  statement and, when instability is found, the contemporaneous-paired-control
  design for any causal claim crossing that axis.
- A recorded deployment-target verification for any quantization/optimization
  artifact before further spend is committed to it (§5 Step 5; chapter 07 owns the
  acceptance gate itself).

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-DETERM-001] | Nondeterminism mechanisms (reduction-order/GPU-state variance, KV-cache placement); batch-invariant modes as opt-in |
| [NV-EVALRECIPE-001] | Full-recipe-publication convention; methodological consistency over bit-wise identical outputs (cited only for this claim — see notes in references/sources.yaml) |
| [NV-WORKBENCH-001] | Git-versioned environment tooling across heterogeneous hardware; explicitly does not provide run/eval tracking |
| [EXT-PERF-003] | Backend/runtime choice alone moving evaluation scores materially (research-only caution) |
| [EXT-VLLM-001], [EXT-SGLANG-001], [EXT-LLAMACPP-001] | Serving-engine determinism-mode specifics for §10 |
| [NV-NVFP4PLAYBOOK-001] | Format-portability trap worked instance |

Gap dispositions in this chapter: none assigned to 02_EXECUTION_SYSTEM_MODEL by the
chapter briefs.

---

> [← Previous](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) · [Index](README.md) · [Next →](03_EVALUATION_FOUNDATION.md)
