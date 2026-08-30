# 02. Execution System Model

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) · [Index](README.md) · [Next →](03_EVALUATION_FOUNDATION.md)
> **Reading time:** ~15 min. **Prerequisites:** 00, 01.

## 1. Purpose and what it protects

*"The new model is seven points better."*

One sentence, one subject — and twelve candidates for who actually earned those seven
points. The weights are one candidate. The others are the quantized artifact, the serving
engine, the machine, the harness that fed in the prompts, the rules deciding what went into
the context window, whatever was retrieved, the tools on offer, the workflow around the
call, the token budget, the grader that scored the output, and the environment all of it
ran inside. If any of those moved between the two runs, some of the seven points are
theirs.

Nobody has to be careless for this to happen. Serving engines auto-upgrade. Managed
endpoints are redeployed on the provider's schedule, not yours. A run lands on a different
box in the pool because that was the one free at the time. No alarm goes off, because
nothing failed. The comparison simply stopped being about the model, and the number it
produced still looks exactly as trustworthy as it did before.

So this chapter does two things. It names the full list, so that a result can say what
produced it. And it gives you a way to find out how far your particular stack can move
before two runs of the same thing stop agreeing — which is something you measure, not
something you assume. [PRINCIPLE] P5 in chapter 00 already makes this a project-wide law:
measurement validity before comparison. What follows is that law with a component list, a
probe procedure, and an answer to the question that every pair of side-by-side numbers
quietly claims to have settled already — **comparable to what, exactly?**

Read this before any comparison that will drive a decision, and again before you move
hosts, swap runtimes, change quantization, or change providers. It is short, and the rest
of the book leans on it. Chapter 03 builds an instrument for measuring quality; that
instrument only means what it claims to mean if the thing underneath it is holding still.

## 2. Inputs required

Three things, all of them from chapter 01:

- A [project profile](GLOSSARY.md#project-profile) naming at least the candidate
  [execution surface](GLOSSARY.md#execution-surface)(s) — where the model will actually
  run: local open-weights inference, self-hosted or rented, a managed API, a subscription
  coding harness, a cloud agent environment.
- Whatever models, runtimes, and hardware are already in scope. You do not need to have
  chosen yet — chapter 05 owns selection, and this chapter does not require it to be
  finished. You do need to know what you are choosing among, because that is what tells you
  which parts of your setup are capable of moving.
- The [stakes tier](GLOSSARY.md#stakes-tier), which sets how much of the pinning and
  probing below is mandatory rather than merely advisable (§6).

## 3. Decisions this chapter supports

- **What has to be written down before a comparison is trustworthy?** Which components get
  frozen, and what "frozen" means for each of them.
- **How far may a causal claim travel?** Which
  [reproducibility boundary](GLOSSARY.md#reproducibility-boundary) a project's claims are
  entitled to cross unaided, and where they instead need a
  [contemporaneous paired control](GLOSSARY.md#contemporaneous-paired-control).
- **Is this still the same system?** A runtime upgrade, a quantization swap, a host
  migration, a provider redeploy — each one is either "the same system, still comparable"
  or a new identity requiring re-measurement. Somebody has to decide which, on stated
  grounds, before the next comparison runs.
- **Will the artifact you are about to spend money on actually run where it has to run?**
  A deployment target's hardware and format constraints have to be settled *before* a
  training or optimization investment is sunk into something that will not load there.

## 4. Normative principles

**[PRINCIPLE] The execution system is the unit of measurement.** (strong-evidence)
You never measure a model on its own. You measure a model wired into everything it needs
in order to produce an answer, and that whole assembly is what this playbook calls the
[execution system](GLOSSARY.md#execution-system). Its full identity, verbatim:

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

Setting two numbers beside each other is itself an assertion: that they came from
conditions similar enough for the gap between them to mean something. This playbook calls
that assertion a [comparability claim](GLOSSARY.md#comparability-claim), and it is a claim
about the *frozen* execution system — unless the experiment explicitly isolates one factor
and holds every other component fixed. You **MUST NOT** collapse model, runtime, provider,
harness, and hardware into a single ambiguous label. "The model got better" is twelve
different possible claims wearing one sentence, and only one of them is about the model.

This is chapter 00's P5 instantiated: measurement validity before comparison. Published
work points the same way — runtime and backend choice alone moves evaluation scores by
double-digit percentage points on identical model weights, with nothing about the model
changed [EXT-PERF-003] (research-only; treat it as a reason to verify locally, not as a
load-bearing number).

**[PRINCIPLE] Reproducibility is measured, never assumed.** (strong-evidence)
Whether two runs of "the same" execution system agree is an empirical property of that
stack. It is not a default you are entitled to, and no configuration flag hands it to you.

The mechanism is worth holding in your head, because it explains why the usual precautions
do not help. Modern inference stacks are non-deterministic even at temperature zero, for
reasons that have nothing to do with sampling. Adding the same floating-point numbers in a
different order gives a slightly different sum, and the order in which a batched GPU kernel
performs its reductions varies with the concurrent state of the GPU. At a token where two
candidates are nearly tied, that difference in the last decimal places picks the other one,
and greedy decoding never returns to the path it left. This variance requires no
concurrency to observe: a single session restarted can reorder its reductions differently
the second time. KV-cache placement is a secondary contributor.

Engines can remove the dominant source. Batch-invariant execution modes exist for exactly
that, and where the engines named in this playbook's source ledger support them — verified
per engine, with dates, in [references/SOURCES.md](references/SOURCES.md) — they ship
**opt-in**, at a material throughput cost (§10). Read that as the practical instruction it
is: the default configuration of a serving stack is not deterministic [EXT-DETERM-001]. So
every "the numbers should match" assumption is a hypothesis about your stack, and §5 is how
you test it rather than believe it.

**[PRINCIPLE] A causal claim across a measured instability boundary requires a
contemporaneous paired control.** (strong-evidence)
Suppose one of the probes in §5 finds that your outcomes are *not* stable across some
axis — a restart, a different host, concurrent load, a provider redeploy. From that point
on, no comparison may cross that axis and still attribute the difference to one
intervention. You have just measured noise large enough to have produced the difference by
itself.

One design survives that situation. Both arms run inside the same session or window.
Everything is held fixed except the intervention. The order is pre-registered and
counterbalanced — AB/BA, for instance — so that "which arm ran first" cannot masquerade as
the effect. That is a
[contemporaneous paired control](GLOSSARY.md#contemporaneous-paired-control). Where one is
unavailable, the causal claim **MUST** be declared unavailable and the comparison relabeled
descriptive: you may still report both numbers, you may not say that one caused the other.
[SCENARIO: SCENARIO-12] works this through end to end — restart instability large enough to
flip a meaningful share of per-item outcomes, answered by scoping every causal comparison
to the boundary that was actually measured rather than to a wider one nobody checked.

## 5. Default procedure

**Step 1 — Declare and pin an identity.** Before any run that will inform a decision,
write down what produced it. For every execution-system component that has one: an artifact
digest (a hash of the weights or adapter), a runtime or engine build identifier, the host
identity, the harness version, and a snapshot of the configuration — context policy,
decoding parameters, generation and reasoning budget, tool and verifier versions.

Do this before the run, not once the run looks interesting. That ordering is the whole
point. By the time a number is worth chasing, the identity that produced it is frequently
gone: the engine updated itself, the container was rebuilt, the instance was recycled. This
record is the input to [provenance](GLOSSARY.md#provenance) (chapter 13), and it is not
reconstructable afterwards from the number alone.

There is a published convention worth following here: ship the full execution recipe
alongside any result you intend other people to trust. The stated goal is *methodological
consistency with clear provenance*, not bit-wise identical outputs on every reader's
hardware [FOLLOW: NV-EVALRECIPE-001] (as-of the date in
[references/SOURCES.md](references/SOURCES.md)). That is the right bar to hold yourself to.
You are not promising the world reproduces your bytes. You are promising it can tell
exactly what you ran.

**Step 2 — Run the reproducibility-boundary probes your topology can actually cross.**
A [reproducibility boundary](GLOSSARY.md#reproducibility-boundary) is the envelope inside
which repeated runs still agree with each other. Within one session? Across a restart?
Across machines, across provider redeploys, under load? Each is a candidate boundary, and
where yours sit is a fact about your stack that costs an afternoon to establish.

Four probes, cheapest first. Run only the ones whose axis your deployment will ever
traverse — there is no cross-host probe to run for a single pinned box that will never
move.

| Probe | What it compares | How to run it | A positive (unstable) result means |
|---|---|---|---|
| **Restart probe** | The same session against a fresh process on the same host | Run a fixed set of paired cases, restart the server, run the identical set again, compare outcomes case by case | Comparisons **MUST** stay inside one session, unless the two arms are paired across the restart |
| **Concurrency probe** | One request at a time against realistic concurrent load | Run the same case set at concurrency 1, then again under representative concurrent load, and compare | Every latency and throughput number, and every correctness number, now has to state the concurrency level it was taken at |
| **Cross-host probe** | The same pinned artifact on a different physical or virtual machine | Run the identical case set on two hosts carrying the same declared identity | "Same identity" claims **MUST** be scoped to the hosts actually probed, not assumed to generalize past them |
| **Provider-redeploy probe** | A managed endpoint's identity stability across the provider's own maintenance | Re-run a fixed probe set against the endpoint after any provider-announced or observed redeploy | A provider-side model update mid-experiment is a **new** execution system, full stop |

Report each probe as an agreement rate (§8) rather than as a pass/fail label. The rate
itself is what downstream chapters need in order to decide whether a paired control is
required; a pass/fail label throws away the one thing that answers that question.
*status: doctrine — not yet exercised* for the concurrency and provider-redeploy probes
specifically. The restart and cross-host designs are worked through in
[SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md); read that
scenario for what a completed probe record looks like.

**Step 3 — Scope every comparability claim to the boundary you measured.** If the restart
probe found instability and the cross-host probe was never run, then the licence you hold
is "comparable within a session on this host" — and nothing wider. Not "probably fine
across hosts". Write that scope into the experiment contract (chapter 04), where the next
person to run a comparison will see it, rather than into a footnote nobody reads.

**Step 4 — Placing arms on different nodes is permitted, under conditions.** A rented or
otherwise remote instance that holds one full session per arm satisfies a session-scoped
reproducibility rule exactly as well as a single owned host does. The rule is about the
session boundary, not about who owns the machine. That means expensive arms can run on
rented capacity (chapter 11) without weakening the comparison — **provided** all four of
these hold:

- **(a)** Placement is pre-registered in the contract before any case runs. It is not
  chosen per arm, opportunistically, once you can see which arm needs the bigger box.
- **(b)** The artifact digest is verified independently on the remote host before the arm
  starts. What the launch script intended to load is not evidence of what loaded.
- **(c)** The remote host's declared identity — driver and runtime versions, hardware — is
  recorded exactly as it would be for a host you own.
- **(d)** The remote surface is itself admissible under the project's written
  privacy/residency requirement (11 Q0a/Q0b; 05 §5.2). Comparability licenses the
  *placement*; it does not license the *surface*. A held-out or regulated corpus lands only
  on the tiers that the stakes-tier cloud policy (11 §8) admits.

**Step 5 — Quantize for the deployment target, not for the development box.** Decide where
the frozen artifact will actually serve *before* you invest in a quantization or
optimization pass, and verify that the chosen format is supported there. Vendor
quantization formats are not universally portable across hardware generations. Some are
locked to a single GPU architecture family, and will either refuse to run elsewhere or
silently drop onto a slower fallback path [ADAPT: NV-NVFP4PLAYBOOK-001] — the second being
the worse outcome, because it looks like it worked. A format chosen for the machine sitting
in front of you, with no verification against the deployment target, is a decision made by
convenience rather than by the requirement. See §9, and chapter 07's acceptance-gated
escalation ladder for the quantization decision itself.

## 6. Project adaptation parameters

**[PARAMETER] What counts as a "material" change that forces a new identity.** In
principle, every change to an execution-system component creates a new identity. In
practice, not every one is worth re-probing at every stakes tier, so calibrate against
consequence. At Tier 1, a minor harness patch version bump MAY be treated as the same
identity by convention. At Tier 2+, any change to runtime, provider, quantization, or
hardware **MUST** trigger re-declaration (§5 Step 1) — and, if a decision depends on
comparing across that change, re-probing (§5 Step 2). Write your project's threshold down
in advance. Deciding it case by case, under pressure, reliably produces the answer that
lets the current run count.

**[PARAMETER] Which probes are warranted, given your topology.** A single-host,
single-provider, low-concurrency deployment may only ever need the restart probe. A
multi-host or autoscaled deployment needs the cross-host and concurrency probes before any
latency or throughput claim can be trusted — chapter 06 depends on this. A managed-API-only
project needs the provider-redeploy probe and nothing else from the list, because it has no
host axis and no restart axis of its own to control.

**[PARAMETER] Authoritative clock per metric.** A machine has more than one clock, and
when there is a virtualization or container layer between your process and the hardware —
containers, VMs, WSL2-class compatibility layers — the monotonic and realtime clocks can
disagree materially. The same span then yields two different durations depending on which
one you asked. So name which clock is authoritative for each reported metric, in the
experiment contract. The mechanics live in chapters 06 and 12
([dual-clock telemetry](GLOSSARY.md#dual-clock-telemetry),
[authoritative clock](GLOSSARY.md#authoritative-clock)); this chapter's obligation is
narrower — to recognize the clock as part of "environment" in the execution-system
definition, and therefore part of the identity you froze.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Identity-change gate.** Something changed in a pinned execution-system
component. Is the change material under your project's §6 threshold? If yes, re-declare the
identity (§5 Step 1). And if the change crosses a reproducibility boundary you have already
probed, re-run that probe before trusting any comparison that spans the change.

**[STOP CONDITION] Unmeasured-boundary crossing.** Stop before running a comparison that
would cross a reproducibility axis — restart, host, concurrency, provider redeploy — for
which you hold no probe result. This is chapter 00's global tripwire #3, operationalized.
Three ways forward, and only three: run the probe first, run a contemporaneous paired
control instead, or relabel the intended claim as descriptive before you proceed.

**[STOP CONDITION] Format-portability mismatch.** Stop before committing optimization or
fine-tuning spend to an artifact format that has not been verified against the deployment
target's hardware. Verify that the format loads and serves correctly on the target
hardware *before* the optimization pass that produces it, not after.

## 8. Metrics and formulas

**Reproducibility agreement rate.** Take a probe of *n* paired cases — the same case, the
same declared identity, compared across the probed axis, such as before and after a
restart. Let *m* be the number of cases whose outcome is identical across the pair. (For a
stricter check, use the full output digest instead of the outcome.) The agreement rate is:

```
agreement_rate = m / n
```

Units: dimensionless, in [0, 1]. A rate below 1.0 confirms the axis is unstable, which
triggers the contemporaneous-paired-control requirement in §4. It does not, by itself, tell
you how large a comparison has to be to detect a real difference despite that instability.
That is chapter 04's clustering and MDE machinery, which treats the probed instability as
one more source of correlation between outcomes to model.

*Worked example (illustrative, invented round numbers).* A restart probe runs 20 paired
cases, before and after a server restart. 12 of the 20 produce an identical outcome; 8
flip. So `agreement_rate = 12/20 = 0.60`.

A 60% agreement rate is a strong instability signal, and it has two immediate consequences.
Forward: comparisons on this stack are scoped to "within one session" until something wider
is demonstrated. Backward: every restart-crossing comparison already in this project's
history needs re-evaluation, or a contemporaneous paired control, before it can support a
decision. The second consequence is the uncomfortable one, and it is the reason to run this
probe early rather than late.

**Artifact digest match rate.** Across a set of hosts or redeploys that are all supposed to
be serving one identical pinned artifact, the share whose computed digest matches the
declared digest. Any mismatch at all is a Step-4 (§5) placement failure rather than a
modeling result. Treat it as an integrity defect and fix it; do not analyze it as data.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Collapsing the execution system into one label.** Saying "the model got better" or "the
  model got worse" when the runtime, provider, quantization, harness, or generation budget
  also changed. This is the anti-pattern P5 exists to forbid: the sentence names one
  component and silently moved several [SCENARIO: SCENARIO-06], [SCENARIO: SCENARIO-08].
- **Assuming determinism because a runtime supports a deterministic mode.** The two engines
  the source ledger verifies for this (see the EXT-VLLM-001 and EXT-SGLANG-001 rows) expose
  opt-in deterministic or batch-invariant modes at a throughput cost, and neither ships that
  mode as its default. Support, defaults, and guarantees vary by engine and by version, and
  other engines were not verified for such modes at all. So probe the runtime you actually
  froze (§5). Never infer determinism from feature availability, and never assume a mode
  exists in an engine the ledger has not verified it for [EXT-DETERM-001].
- **Format-locked-to-hardware surprise.** Choosing or accepting a quantization format
  because it is convenient on the development machine, then discovering at deployment time
  that the target hardware does not support it — or takes a silent slow-path fallback
  [ADAPT: NV-NVFP4PLAYBOOK-001].
- **Treating "same session" as "same identity forever."** A provider-side model update, a
  silent runtime auto-upgrade, or a host migration mid-experiment invalidates a
  reproducibility boundary you previously measured. The boundary is a property of one
  *specific* pinned identity. It is not a permanent fact about the project.

**Environment hazards across execution layers.** These generalize a recurring pattern: a
layered execution environment — a container inside a VM inside a host, interop shells, path
resolution across mounted filesystems — hides defects that present as model or system
weakness and are actually environment defects. None of them are AI-specific. AI-system
experiments are unusually exposed to them anyway, because comparisons depend on exact
reproducibility, so a defect that a normal application would tolerate shows up here as a
result. Check for these, in order of how often they recur:

1. **Name aliasing across a host/guest boundary.** The same command name can resolve to
   different programs depending on which layer invokes it. When a command's behavior seems
   to contradict its documentation, verify which binary actually executed — not just what
   it was called.
2. **Interop mangling of inline arguments.** Commands issued across a virtualization or
   interop boundary can have inline variables or quoting silently altered in transit.
   Prefer writing the command to a script and executing the script over inline
   substitution when crossing such a boundary. Better still: run the harness from inside
   the same layer the target process runs in.
3. **Existence is not executability.** A resolvable binary path is not proof the binary
   runs. Platform application-store stubs and similar shims exist precisely to satisfy
   `which`/`command -v`-style checks while failing on invocation. Probe by executing a
   trivial command, not by checking existence.
4. **Environment configuration silently unread.** A serving script that only honors
   already-exported variables, or only reads a config file when invoked through one
   particular path, can serve a stale or wrong artifact after a restart — with no error
   message anywhere near the actual cause. Verify the declared identity (§5 Step 1)
   against what actually loaded, not against what the launch command intended to load.
5. **Baked absolute paths.** Binaries and virtual environments that embed absolute
   runtime-library or interpreter paths at build time break silently, not loudly, when the
   install location moves. Relocating any execution-system component's home directory is
   itself a Step-1 re-declaration event.
6. **Cross-layer package-manager namespace confusion.** A global package install run from
   one environment layer can land in a different layer's install prefix than the one the
   launch command actually uses.
7. **Filesystem-layer metadata loss.** Editing a file through a foreign filesystem
   interface — a network mount, a cross-OS interop mount — can silently drop executable
   permission bits. Track modes in version control rather than trusting the filesystem to
   preserve them.
8. **Shared-host port/service collisions.** On a host running more than one project, a
   reused port routes traffic to the wrong service rather than failing to bind. Treat "an
   unexpected response from a known-good endpoint" as a question about environment identity
   before you treat it as a question about model behavior.
9. **Clock validity under virtualization** (§6). This is the environment component of the
   execution system, not a separate concern.

## 10. Vendor recipes

| Vendor / project | Verdict | What it gives you | As-of / caveat |
|---|---|---|---|
| Serving engine deterministic/batch-invariant modes [ADAPT: EXT-VLLM-001] | ADAPT | An opt-in flag that trades throughput for reduction-order determinism | Verified active; opt-in, reduced throughput as of verification date — do not assume it is the default |
| Alternate serving engine deterministic mode [REFERENCE: EXT-SGLANG-001] | REFERENCE | A second, independent deterministic-mode implementation, with a documented slowdown range | Verified active; consult it before depending on any cross-engine determinism comparison |
| CPU/GPU single-slot engine [REFERENCE: EXT-LLAMACPP-001] | REFERENCE | A serving path whose single-slot model suits the determinism/provenance regime by construction (chapter 05 develops the regime choice) | Verified active; very frequent releases — pin the exact build in your identity record |
| Deployment-target quantization format guidance [ADAPT: NV-NVFP4PLAYBOOK-001] | ADAPT | A concrete instance of the format-portability trap (§5 Step 5, §9): a next-generation microscaling format documented as tied to one GPU architecture family | As-of verification date; re-check before relying on it — vendor format support windows move |
| Full-recipe-publication convention [FOLLOW: NV-EVALRECIPE-001] | FOLLOW | The stated goal — methodological consistency with clear provenance, not bit-wise identical outputs — matches this chapter's Step 1 exactly | As-of verification date; cite for the publication convention only, not for any specific pinning checklist |
| Git-versioned environment tooling [REFERENCE: NV-WORKBENCH-001] | REFERENCE | Environment and identity versioning across heterogeneous hardware targets | As-of verification date; does not provide run/eval tracking by design — the record of record (chapter 13) is still yours to build |

## 11. Worked examples

- [SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md) — an invented
  case in which a restart probe finds a large share of case outcomes unstable across nothing
  more than a server restart. The response is to scope causal comparisons to the measured
  boundary — same session, contemporaneous paired controls — rather than to chase
  bit-identity that the stack was never going to deliver.
- [SCENARIO-08](examples/SCENARIO-08_transport-serialization-defect.md) — an invented case
  in which a transport layer advertised as transparent silently reorders structured output
  and breaks a downstream consumer that depended on byte-level fidelity. It is found only
  by explicit byte-equivalence verification, never by looking at the outputs. This is a
  tool-contract instance of the layered-environment-hazard pattern in §9, developed fully
  in chapter 08.
- The agreement-rate calculation worked through in §8 shows the arithmetic a restart probe
  produces, before any case-level analysis begins.

## 12. Outputs and artifacts

- A declared execution-system identity — artifact digest, runtime/build identifier, host
  identity, harness version, config snapshot — for every run that will inform a decision.
  It feeds [provenance](GLOSSARY.md#provenance) (chapter 13) and the execution-system
  identity field of every [experiment contract](templates/EXPERIMENT_CONTRACT.md)
  (chapter 04).
- One reproducibility-boundary probe record per axis actually probed (§5 Step 2), each with
  its measured agreement rate (§8). These feed the contract's comparability scope statement
  and — where instability was found — the contemporaneous-paired-control design for any
  causal claim that crosses that axis.
- A recorded deployment-target verification for any quantization or optimization artifact,
  made before further spend is committed to it (§5 Step 5; chapter 07 owns the acceptance
  gate itself).

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
