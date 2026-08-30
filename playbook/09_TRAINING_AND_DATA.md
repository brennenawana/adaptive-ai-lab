# 09. Training and Data

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) · [Index](README.md) · [Next →](10_DEPLOYMENT_AND_OPERATIONS.md)
> **Reading time:** ~20 min. **Prerequisites:** [00](00_PRINCIPLES_AND_SCOPE.md),
> [03](03_EVALUATION_FOUNDATION.md), [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
> [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).

## 1. Purpose and when to read this

Almost every fix you have been offered so far can be undone by editing a file. A prompt,
a retrieval rule, a routing threshold, a generation cap — get one wrong and the recovery
is an afternoon and a re-run.

Fine-tuning is where that stops. It produces weights: an artifact you now have to store,
hash, evaluate in full, and build again from scratch the next time the base model
underneath it is replaced. None of that is an argument for never doing it. It is the
reason this chapter spends most of its length on how to find out you do not have to, and
keeps the procedure itself short.

This is rung 7 of the [intervention ladder](GLOSSARY.md#intervention-ladder) — the point
at which the system stops being reconfigured and starts being retrained. Read it only
after chapter 07 has produced a diagnosed, evidence-backed case that a residual gap
belongs to root-cause class RC-10 (learnable capability gap) in the
[canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy), and that cheaper
rungs are exhausted, not merely unappealing.

If you hold that case, the rest of this chapter is a procedure and reads in order. If you
are not sure you hold it, §4 and §7 are where you find out, and they are the two sections
to read first.

**Honesty statement.** The playbook's source project has, as of this release, never
executed a training run. Every optimization gap it has faced to date was resolved at a
cheaper rung — prompt/workflow fixes, budget calibration, or routing — and rung 7 was
never reached.

This is recorded here as a *methodology success*, not an omission. The ladder's job is to
spend the expensive rung only when cheaper ones provably cannot close the gap, and so far
they always could.

It does change what you are reading, and you should know exactly how. Consequently this
chapter is assembled entirely from external literature, vendor mechanics, and playbook
inference reasoned from those sources plus the project's own (unexecuted) design work —
never from an internal execution record. Every claim below states which of these four
categories it comes from. Where a procedure has no internal or directly transferable
external execution record, it carries the doctrine marker in full:
*status: doctrine — not yet exercised (see the relevant subsection below for what
validation would look like)*.

## 2. Inputs required

Six things have to exist before the first training command runs. Most are produced by
other chapters. None of them is convincing if you assemble it afterwards.

- **A diagnosis, not a suspicion.** A
  [canonical-failure-taxonomy](GLOSSARY.md#canonical-failure-taxonomy) verdict placing the
  residual gap in RC-10, produced by chapter 03's instrumentation and chapter 07's
  diagnostic gates — not a hunch that "the model should just know this."
- **Chapter 07's evidence that rungs 0–6 are exhausted** or demonstrably inapplicable for
  this gap. The ladder's evidence bar is normative in chapter 07; this chapter restates it
  as a precondition, not as a second authority.
- **A frozen, versioned [evaluation suite](GLOSSARY.md#suite-release)** (chapter 03) that
  can score the tuned artifact on the full task distribution, not just on the target
  behavior. The full distribution is the part §4's forgetting gate needs.
- **A closed economics case** (chapter 11): training, iteration, and serving cost, against
  the value of closing the gap.
- **License identity for every base-weight candidate, and legal clearance for every data
  source** (§4, plus chapter 13's G7 procedure for base-weight license review).
- **An [execution system](GLOSSARY.md#execution-system) / provenance model that can
  represent a self-produced artifact** (§12) — extended *before* the first training run,
  not retrofitted after it.

## 3. Decisions this chapter supports

- Whether to train at all, versus continuing to invest in cheaper rungs.
- Retrieval and context versus training, as the direction of investment for a given gap.
- Method selection: parameter-efficient tuning (LoRA/QLoRA) versus full fine-tuning.
- Where training data comes from, and whether a given source is legally usable.
- How much data is enough, without inventing a universal number.
- What gates a tuned artifact before it is even considered for promotion (chapter 10).

## 4. Normative principles

Five rules govern this rung. The first decides whether you are here at all; the middle
three are the ones teams skip and pay for later; the last is a boundary you can violate
without ever noticing.

**[PRINCIPLE] Evidence threshold to train.** (consensus — restated from chapter 07,
normative there)
Three prompt variants did not close the gap, everyone is out of ideas at the cheap rungs,
and fine-tuning is the next thing anybody can name. That is a mood, and it is the most
common route to the most expensive rung on the ladder.
So training is justified only when *all four* of these hold:

1. The taxonomy diagnosis places the gap in RC-10.
2. Cheaper rungs are exhausted *with evidence*, not with impatience.
3. The training data demonstrably contains the target skill — someone can point at
   examples of it being done correctly.
4. The economics close (chapter 11).

Corroborated by three independent RAG-vs-fine-tuning studies that converge on
retrieval/prompt-first for factual and citation tasks [EXT-FT-001], and by vendor guidance
to "layer in training-based techniques where measurement shows they're needed"
[NV-AGENTICBLOGS-001]. Never train around a defect at rungs 0–4 (P3, chapter 00) — a
broken instrument, a transport bug, or a missing tool contract does not become more
fixable by fine-tuning around it. It becomes harder to detect.

**[PRINCIPLE] Rig before model.** (consensus, corroborated + first-principles)
The first time a training pipeline runs end to end, it is unexercised machinery, and
something in it is wrong. A merge step that quietly drops the adapter. A quantize step
that will not load what the merge produced. An eval harness pointed at the base weights
instead of the tuned ones. You want to find that out on a run whose result you did not
care about.
So de-risk the *pipeline* — train → merge → quantize → serve → evaluate, end to end, with
full provenance — on a cheap, throwaway configuration before spending the training budget
on the real experiment. Finding out the pipeline is broken during the real experiment
wastes the expensive resource to debug the cheap one. This is the same argument that
justifies a sanity-check pass on a toy example before scaling up any learning system
[EXT-TESTBED-001], applied to the pipeline rather than to the model.
*(status: doctrine — not yet exercised — the source project has designed but not run this
rig; see §5 step 3 for what execution would look like.)*

**[PRINCIPLE] Check every provider's current terms, at training time, and record the
check.** (consensus)
This is the check that reads like boilerplate and is not. A licence problem found *after*
the run does not cost you a paragraph in a compliance document — it costs the run. The
weights are unusable, the dataset has to be rebuilt without the offending records, and the
compute is already spent. It is also among the cheapest checks in this chapter, and it
takes an hour before anything is written to disk.

Any training data that touches a managed model provider's inputs or outputs is bound by
that provider's *current* terms of service — not the terms as understood at project start.
Anthropic's Commercial Terms of Service prohibit using the Services "to build a competing
product or service, including to train competing AI models," and its separate Usage Policy
independently bars "utilization of inputs and outputs to train an AI model ... without
prior authorization" [EXT-LEGAL-001]. OpenAI's consumer Terms of Use bar using "Output to
develop models that compete with OpenAI," and its Business Terms bar using output "to
develop artificial intelligence models that compete," with narrow carve-outs for
non-distributed classifiers/embeddings and for provider-hosted fine-tuning
[EXT-LEGAL-002]. Google's Gemini API terms bar using the Services "to develop models that
compete with the Services" [EXT-LEGAL-003].

**The rule, not the specific clauses, is what travels**: these three sources were verified
on different pages with different effective dates within the same verification pass —
vendor terms move on independent clocks. A clearance obtained once is not evidence of
clearance six months later. So verify the live terms of every provider in the data path
immediately before training, and keep the verification (date, URL, quoted clause) in the
record of record (chapter 13). *(EXT-LEGAL-002 was reachable only through a
text-extraction proxy at verification time, not a direct fetch — its content is
corroborated by independent sources but carries a lower confidence than a direct fetch;
re-verify directly per project before relying on it for a Tier-3 decision.)*

**[PRINCIPLE] The forgetting gate runs on the full suite, never the target slice
alone.** (strong-evidence)
Your tuned model comes back clearly better on the behavior you tuned it for. You check
that slice, it passes, and it goes forward. What nobody re-ran is everything else the
model used to do — so the first evidence that three of those things got worse arrives
weeks later, as a report from a part of the system nobody connected to the training run.

Catastrophic forgetting after fine-tuning is real, its scaling behavior is not obviously
predictable in advance, and model merging does not reliably repair it [EXT-FT-006]. A
tuned artifact that improves the targeted behavior and silently degrades everything else
has not closed a gap; it has traded one for an unmeasured set of others.

So the regression check is the [evaluation suite](GLOSSARY.md#suite-release) in full, run
exactly as it runs for any other candidate — see chapter 03's
regression-vs-capability-suite distinction. This gate is easy to skip, and the reason is
structural rather than careless: by the time you reach it, the target metric already looks
like a win, and running the whole suite costs more than running the one slice you care
about. Skipping it does not make the regression not happen. It only moves the moment you
learn about it to after promotion.

**[PRINCIPLE] Training data never touches a held-out split.** (consensus,
first-principles — same boundary as [gold labels](GLOSSARY.md#gold-labels))
The split you will judge the tuned model on is the one thing in the project that no choice
of yours has been fitted to. That is the entire source of its value, and training on any
of it — even indirectly — spends that value without producing any visible symptom.

Data used to train or curate a tuning run must therefore be disjoint from the
qualify/confirm splits (chapter 04) used to evaluate it, enforced the same way
[leakage](GLOSSARY.md#leakage) is enforced anywhere else in this playbook: structural
separation plus a reachability test, not a promise.

One detail decides whether the separation is real. Hold out entire generation seeds or
source groups, not individually sampled rows. Row-level holdout leaks structure —
paraphrase, template, adjacent context — that a group-level split does not.

## 5. Default procedure

1. **Confirm the evidence threshold** (§4, chapter 07). If any of the four conditions is
   unmet, stop here — return to the ladder, not to the training budget.
2. **Clear data and license legality** (§4; chapter 13 G7 for base-weight license
   identity). Record the check before any data is written to disk.
3. **Build the rig.** Take the smallest viable base model and a small, cheap, illustrative
   example set (e.g., on the order of a few hundred synthetic examples, targeting well
   under an hour end to end — invented, illustrative figures; calibrate to your own
   compute). Exercise the full pipeline on it: train → merge → quantize → serve → evaluate
   against a small held-out slice, with every stage's artifact digested into provenance
   (§12). Delete the rig once the pipeline is boring — that is, once it completes
   deterministically with no manual intervention.
4. **Harvest and curate data — provenance-qualified.** The default source is the system's
   own execution trajectories, successful and failed, scored against the system's own
   [ground truth](GLOSSARY.md#gold-labels). Supplying exactly that is what
   [failure harvesting](GLOSSARY.md#failure-harvesting) (chapter 12) is designed for.

   **Owning the trajectory record does not imply owning training rights to every output
   embedded in it.** A [trajectory record](GLOSSARY.md#trajectory-record) can contain
   managed-provider outputs (an escalation tier's responses — this playbook's own default
   cascade architecture, chapter 08, produces exactly that), judge outputs,
   provider-generated synthetic labels, tool outputs, human annotations, and
   self-hosted-model outputs. Each carries different permitted uses.

   Training admissibility is therefore determined at the **component level**: before a
   record enters a training set, identify the provenance of every model-generated component
   it contains, and confirm that component's terms permit use as a training input or target
   (§4). The operable default is *self-produced* traces in the narrow sense — components
   generated by models whose weights and terms you control, scored against your own ground
   truth — with every managed-provider-generated component either excluded, covered by an
   authorization on file, or the whole record dropped. Then deduplicate and filter for
   quality over raw volume [heuristic; EXT-FT-007 is promising but research-only — treat as
   a direction, not a recipe].
5. **Split for training**, holding out entire seeds or source groups from every split the
   evaluation will later use (§4).
6. **Choose the method** (§6, §10). Parameter-efficient tuning (LoRA/QLoRA) is the default
   starting point; escalate to full fine-tuning only with evidence that the PEFT regime is
   insufficient for the task (§10's contradiction note).
7. **Run the sample-size question as an ablation**, not as a lookup. Small/medium/large
   data rungs (invented illustrative sizes, e.g. ~100 / ~300 / ~900 examples — see §6),
   against the iterate split, under one-look discipline, pre-registered before any rung
   runs. There is no primary source for a universal minimum-n on a narrow behavioral fix
   (§6); the ablation is the answer, every time, for this project.
8. **Train**, with seed(s) and full hyperparameter/config provenance recorded per run.
9. **Run the forgetting gate**: the full suite, not the target slice (§4).
10. **Compare paired against the frozen base system**, under a pre-registered
    [experiment contract](templates/EXPERIMENT_CONTRACT.md) (chapter 04): paired
    statistics, MDE stated, INCONCLUSIVE a legitimate outcome.
11. **Hand a passing artifact to the promotion gate** (chapter 10). A failing or
    INCONCLUSIVE artifact is still a complete, recordable experiment — not a failure to
    hide.

## 6. Project adaptation parameters

| Parameter | Starting point | Evidence / source | Calibrate against |
|---|---|---|---|
| LoRA target modules | all major linear layers | [EXT-UNSLOTH-001] | task complexity; narrower targeting trades quality for speed |
| LoRA rank | moderate (commonly cited range ~16–32) | [EXT-UNSLOTH-001] | task complexity, VRAM budget |
| LoRA alpha | α ≈ 2 × rank | [EXT-UNSLOTH-001] | empirical stability on your rig |
| Learning rate (LoRA vs full FT) | ~10× the full-fine-tune LR as a starting point | [EXT-UNSLOTH-001] | loss-curve stability on the rig |
| QLoRA / 16-bit LoRA VRAM floors, by base-model size | QLoRA / 16-bit LoRA, paired: 9B ~6.5 / ~24 GB; 27B ~22 / ~64 GB; 70B ~41 / ~164 GB — the ratio runs 2.9×–4.0× across sizes, not a flat multiplier | [EXT-UNSLOTH-001] (method reference: [EXT-FT-003]) | your actual base model and quantization; these are floors, not comfortable operating points — never round a floor down to a flat ratio when sizing hardware |
| Dataset size, PEFT vs full FT | ~100–1,000 prompt-pairs PEFT; 1,000+ full FT (vendor-stated, as-of 2025-12-15) | [NV-RTXAIGARAGE-001] | task family; treat as a prior, not a target (§5 step 7) |
| Tool-calling data volume | 85/15 train/eval split with an independent golden set; hundreds of synthetic samples reported sufficient for high accuracy on that task family | [NV-TOOLCALLTUTORIAL-001] | your own tool surface; the ratio, not the absolute count, is the transferable part |
| Forgetting-gate tolerance | a [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) on full-suite regression (illustrative: no more than a small, pre-declared point-drop before RECALIBRATE) | inference | stakes tier; Tier-3 tolerances should be tighter and reviewed |
| Rig scale | illustrative: few hundred synthetic examples, target well under an hour end to end | inference (rig-first principle, §4) | your own hardware; the property that matters is "cheap enough to throw away" |
| Sample-size ablation rungs | illustrative: small/medium/large (e.g. ~100/~300/~900) | inference (§4, §5 step 7) | your task; report the rung, not a folklore number |

**Reading the VRAM row, if you are sizing one machine.** Each model size in that row
carries two numbers, and they are not interchangeable. The higher one is 16-bit LoRA,
which keeps the frozen base weights at half precision and trains a small adapter on top of
them. The lower one is QLoRA, which trains the same kind of adapter but keeps those frozen
base weights in a quantized, much smaller form — which is the whole reason one column is a
fraction of the other.

Two cautions, both in the table and both worth restating because they are the ones people
lose. The gap between the two columns runs **2.9×–4.0× across sizes, not a flat
multiplier**, so you cannot derive one number from the other with arithmetic; read the
column you are actually going to use. And these are **floors, not comfortable operating
points** — the smallest configuration in which the run fits at all, with nothing left over
for longer sequences, larger batches, or the merge step at the end. Never round a floor
down to a flat ratio when sizing hardware. The source carries no documented publication
dates, so re-verify it live before it decides a Tier-3 hardware purchase (§10).

**If this is your first adapter.** Rank sets how much capacity the trained adapter has:
higher rank, more capacity, more VRAM. Alpha scales how strongly that adapter's
contribution enters the model, and the table's α ≈ 2 × rank is a starting relationship
rather than a law — what you calibrate it against is stability on your own rig, not
someone else's benchmark. The learning rate is the number most often carried over from a
full-fine-tune recipe, and it should not be: the starting point for LoRA is roughly 10×
the full-fine-tune LR, from the same source. Start with the adapter on all major linear
layers; narrowing the target set is a speed optimization you can make later, once you know
what quality you are trading away.

**Minimum-n field gap** (stated explicitly, per the honesty rule): no primary source
establishes a minimum training-set size for a narrow behavioral fix. LIMA's widely cited
n≈1,000 is a style-alignment result on a large base model — a different scope from a
targeted correction, and its authors do not claim it generalizes to narrow fixes
[EXT-FT-002]. Treat this as a genuine gap in the field, not a playbook omission, and close
it locally with the ablation in §5 step 7 rather than importing a number from an unrelated
paper.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Train-at-all.** Inputs: RC-10 diagnosis, ladder-exhaustion evidence,
data-contains-the-skill evidence, closed economics (all four, §4). Rule: all four present →
proceed to the rig; any absent → return to chapter 07, do not proceed. Outcome: GO to §5
step 3, or an explicit NO-GO with the missing input named.

**[DECISION GATE] Rig graduation.** Inputs: the rig pipeline (§5 step 3), run to
completion with full provenance and no manual intervention. Rule: deterministic,
provenance-complete, boring → proceed to real data; any manual patch mid-run → fix the
pipeline defect and re-run the rig, and do not carry the patch into the real experiment.
Outcome: cleared to §5 step 4, or another rig cycle.

**[DECISION GATE] Legal/license clearance.** Inputs: the current terms of every provider
in the data path (§4), and the license identity of every candidate base weight (chapter 13
G7). Rule: this MUST clear before any data is written to disk or any base weight is
downloaded for tuning. Outcome: cleared with the check recorded, or blocked with the
specific clause cited.

**[STOP CONDITION] Forgetting-gate breach.** Trigger: full-suite regression exceeds the
pre-registered
[consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) (§6). Response:
execute the named consequence (ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING) —
never argue with it in the moment (P7, chapter 00).

**[STOP CONDITION] Sample-size ablation shows no signal at the largest affordable rung.**
Trigger: the largest rung in §5 step 7 fails to move the target metric beyond the design's
[MDE](GLOSSARY.md#mde). Response: report INCONCLUSIVE, not "training doesn't work." The
honest reading is that the data or the method, at the budget tested, did not demonstrate
the skill. Return to chapter 07 to re-examine whether the gap is actually RC-10 or was
misdiagnosed — possibly RC-11, a fundamental gap, which is rung 8.

**[DECISION GATE] Post-tune promotion.** Inputs: a passed forgetting gate, a paired
comparison result (CONFIRMED / INCONCLUSIVE) against the frozen base system, and a full
provenance record (§12). Rule: only a CONFIRMED, forgetting-gate-clean artifact enters the
promotion pipeline (chapter 10); an INCONCLUSIVE result is recorded and does not promote by
default.

## 8. Metrics and formulas

The statistical machinery for the post-tune comparison is chapter 04's, unchanged: paired
standard errors on same-item comparisons, [MDE](GLOSSARY.md#mde) stated before the
comparison runs, [INCONCLUSIVE](GLOSSARY.md#inconclusive) as a legitimate verdict. Nothing
about fine-tuning licenses a different statistical standard for "did this help."

One addition is specific to this chapter. The sample-size ablation is read the same way a
screening rung is read everywhere else in this playbook (chapter 04's
[screening-vs-inference](GLOSSARY.md#screening-vs-inference) distinction): it ranks rungs,
it does not itself certify a final answer. A neutral illustrative worked table:

| Rung (illustrative) | Examples | Target-metric estimate (illustrative) | 95% interval width (illustrative) |
|---|---|---|---|
| Small | ~100 | +4 pp over base | ±9 pp |
| Medium | ~300 | +9 pp over base | ±6 pp |
| Large | ~900 | +11 pp over base | ±4 pp |

Reading: the small rung's interval is too wide to be worth anything but direction. The
first rung whose interval is narrower than the pre-registered MDE is the one worth
carrying into the frozen comparison — smaller rungs inform the curve, not the choice.
Note what that sentence does *not* say. No rung here is reportable, however clean its
interval looks. This is a screening ablation, and chapter 04's boundary is strict:
screening ranks, only the frozen comparison infers. The number you publish comes from
that comparison, run at the size this table helped you pick.

For the promotion economics — cost per successful task after tuning versus before, and
whether the training spend is justified by the gap it closes — use chapter 11's
cost-per-solve formula unchanged. Fine-tuning is one more line in that ledger, not a
separate accounting system.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Training around a defect at rungs 0–4.** If the gap is an instrument defect, a runtime
  bug, a missing tool contract, or an unenforced output format, fine-tuning hides the
  symptom and leaves the defect live for the next task it touches (P3, chapter 00).
- **Distilling a managed provider's outputs into a competing model without
  authorization.** (condition: no authorization is on file for that provider's current
  terms) §4's rule exists precisely to prevent this — and "we only train on our own
  trajectories" is not a defense by itself: a trajectory from a cascade system embeds the
  escalation tier's provider outputs. Admissibility is component-level provenance (§5 step
  4), not record ownership.
- **Treating a universal minimum-n as folklore-derived truth.** (condition: no
  project-specific ablation has been run) There is no such number in the literature for
  narrow fixes (§6); citing one anyway launders an unjustified sample size as if it were
  evidence-based.
- **Grading the forgetting gate on the target slice only.** A tuned artifact that passes on
  its target behavior and was never checked against the rest of the suite has not been
  evaluated — it has been confirmed on the one axis it was optimized for.
- **Treating merge as a forgetting fix.** Model merging does not reliably restore regressed
  capability [EXT-FT-006]; the forgetting gate, not a merge step, is the control.
- **Skipping the rig and debugging the pipeline and the model at the same time.** When a
  real training run fails, an unexercised pipeline makes it impossible to tell whether the
  model, the data, or the mechanics broke.
- **A placeholder legal clearance that is never re-checked.** A check performed once at
  project start is not evidence of clearance at training time; vendor terms move on
  independent clocks (§4).

## 10. Vendor recipes

Eight sources, and what each is good for. The first column is this playbook's stance —
FOLLOW, ADAPT, or REFERENCE ([vendor verdicts](GLOSSARY.md#vendor-verdicts)). The last
column is the one to read carefully: it says what the source does *not* license, which is
where most of the misuse starts.

| Verdict | Source | Scope | What it gives you | What it does not |
|---|---|---|---|---|
| [REFERENCE] | [EXT-FT-003] | QLoRA mechanics (method reference) | The quantization/adapter method itself — arXiv:2305.14314 (2023), whose worked model sizes predate the families this chapter's own floors are quoted for | Verified by-size VRAM floors for current model families — see [EXT-UNSLOTH-001] for those; do not treat this paper's era-specific sizes as the current numbers |
| [FOLLOW] | [EXT-UNSLOTH-001] | LoRA/QLoRA targeting, hyperparameters, and by-size VRAM floors | Verified-live VRAM floors by base-model size (§6), plus rank/alpha/LR starting points | No documented publication dates — staleness is not independently datable from the source itself; re-verify live before relying on it for a Tier-3 hardware decision |
| [ADAPT] | [NV-FINETUNESTACK-001] | LoRA-vs-full-SFT selection | Selection guidance (LoRA favored for 1–2 GPUs, fast iteration, multiple specialized adapter versions) | **Correction**: this source's docs do *not* carry the early-stopping defaults sometimes attributed to it — those live in the underlying training-framework code, not in the published guidance. Cite this source only for the selection criteria, not for early-stopping numbers. |
| [ADAPT] | [NV-RTXAIGARAGE-001] | Dataset-size thresholds | A vendor-stated PEFT-vs-full-FT size boundary, dated | Any narrow-task minimum-n validation (§6 field gap) |
| [ADAPT] | [NV-TOOLCALLTUTORIAL-001] | Tool-calling fine-tune data design | Split ratio + independent golden-set pattern | General-purpose data sizing outside tool-calling |
| [REFERENCE] | [NV-CURATORDESIGNER-001] | Large-scale data curation/synthetic-data tooling | Pretraining-scale cleaning and dedup tooling, beta schema-driven synthetic generation | No small-dataset fine-tuning-specific curation methodology — do not expect this tooling to answer §5 step 4 at a lab's scale |
| [FOLLOW] | [EXT-FT-006] | Catastrophic forgetting | The mandate for a full-suite gate (§4) | A fix for forgetting once it's found — there isn't a reliable one besides re-tuning |
| [REFERENCE] | [EXT-FT-007] | Error-driven data curation research cluster | A promising pattern that matches this playbook's own-trace design | Unreviewed 2025/26 preprints — pilot-grade only, not a recipe to follow by the book |

**The LoRA-vs-full-fine-tune quality contradiction (kept visible, per this playbook's
practice of never picking a silent winner).** One well-known study on a single 7B model
found LoRA "learns less and forgets less" than full fine-tuning — a real but narrow-scope
result. A later study at post-training scale found all-linear-layer LoRA approaches full
fine-tuning quality at roughly two-thirds the compute, and explicitly reconciles the two
findings as a matter of *regime* rather than contradiction [EXT-FT-005].

**Decision rule**: at small-model / single-model narrow-task scale, budget for LoRA to
underperform full fine-tuning on raw capability, and treat that as an acceptable trade for
speed and reversibility. At larger-model / broader post-training scale, prefer all-layer
LoRA as the default, and reserve full fine-tuning for evidence that PEFT specifically is
the bottleneck — not merely that the target metric is short of goal. Do not resolve this by
picking a side once for a whole project. Resolve it per training run, against the regime
that run is actually in.

## 11. Worked examples

A neutral illustrative walk-through of §5 (all numbers invented and round):

> A team diagnoses a residual RC-10 gap: a document-classification step names the wrong
> category on an ambiguous subclass, and prompt/context fixes (rungs 2–4) have been
> exhausted without closing it.
>
> The rig runs a small base model against ~150 synthetic examples through the full
> train→merge→quantize→serve→evaluate pipeline in under 40 minutes. It surfaces one
> provenance-schema bug, which is fixed, and the rig is re-run clean.
>
> Real data comes from the system's own held trajectories for that classification step,
> scored against the system's own ground truth. Component-provenance review (§5 step 4)
> confirms that no managed-provider output is embedded in any record, and that the local
> model's license permits its generations as training targets — so §4's legal gate clears
> without a special exception.
>
> The sample-size ablation runs three rungs (~100/~300/~900 examples); the interval first
> excludes zero at the middle rung, so that is the rung reported.
>
> The forgetting gate runs the full suite. A 1-point regression on an unrelated stratum is
> within the pre-registered tolerance and proceeds; a 6-point regression would have
> triggered RECALIBRATE. The paired comparison against the frozen base system reports
> CONFIRMED at the pre-declared MDE, and the artifact moves to chapter 10's promotion
> pipeline.

- [SCENARIO-11](examples/SCENARIO-11_diagnostic-gate.md) — the general pattern of a cheap,
  pre-registered diagnostic deciding an expensive experiment's fate before it runs; the
  same discipline applies to the train-at-all gate (§7).
- [SCENARIO-06](examples/SCENARIO-06_token-budget-confounding.md) — a budget confound
  inflated a headline comparison before the underlying factor was isolated; the same
  caution applies to a tuned-vs-base comparison run under an uncontrolled generation
  budget.
- [SYNTH-06](examples/SYNTH-06_training-rejected.md) — a synthetic worked example of the
  train-at-all gate correctly returning NO-GO.
- [SYNTH-07](examples/SYNTH-07_training-justified.md) — a synthetic worked example of the
  gate correctly returning GO, and the pipeline through promotion.

## 12. Outputs and artifacts

Before the first training run, extend the
[execution system](GLOSSARY.md#execution-system) /
[provenance](GLOSSARY.md#provenance) model to represent a self-produced artifact — one
your own pipeline made, rather than one you downloaded. Minimum field set:

| Field | Purpose |
|---|---|
| Dataset digest | Content-hash of the exact training set used |
| Base-artifact reference | Which frozen base model/weights this run started from |
| Hyperparameters | Full config: method, rank/alpha (if PEFT), LR, epochs/steps, schedule |
| Seed(s) | For reproducibility of the training run itself |
| Adapter/weight-delta hash | Content-hash of the produced artifact |
| Pipeline digests | Hash of every stage's tool/script version (train, merge, quantize, serve) |
| License check record | Provider terms verified (§4), base-weight license identity (chapter 13 G7), with date |

Other outputs of this chapter's procedure:

- An [experiment contract](templates/EXPERIMENT_CONTRACT.md) for the tuned-vs-base
  comparison, frozen before the comparison runs (chapter 04).
- A [prediction ledger](templates/PREDICTION_LEDGER.md) entry: the pre-run estimate of the
  effect, scored against the actual result.
- A forgetting-gate report: the full-suite comparison, pass or breach, against the declared
  tolerance.
- A promotion recommendation (GO / NO-GO / INCONCLUSIVE) handed to chapter 10.

**RL evidence bar.** *status: doctrine — not yet exercised (see this note for what
validation would look like)* — reinforcement learning and preference-optimization methods
carry a materially higher evidence bar than supervised tuning. Verifier quality must itself
be validated before it is trusted as a reward signal, and a reward-hacking audit — does the
policy exploit the verifier rather than solve the task? — is required before any RL-tuned
artifact is trusted. This playbook takes no position beyond stating that the bar exists: it
has neither an internal execution record nor a first-principles procedure worked out in
place for RL specifically, unlike the SFT/PEFT path above.

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-FT-001] | RAG/prompt-first direction for factual/citation tasks (§4) |
| [EXT-FT-002] | LIMA — style-alignment scope caveat on the minimum-n field gap (§6) |
| [EXT-FT-003] | QLoRA method reference — not the source for by-size floors (§6, §10) |
| [EXT-FT-005] | LoRA quality-regime package; resolves the LoRA-vs-full-FT contradiction by regime (§10) |
| [EXT-FT-006] | Catastrophic forgetting; mandates the full-suite gate (§4, §9) |
| [EXT-FT-007] | Error-driven data curation research cluster — research-only (§10) |
| [EXT-LEGAL-001] | Anthropic Commercial Terms + Usage Policy — provider-output training restriction (§4) |
| [EXT-LEGAL-002] | OpenAI Terms/Business Terms — provider-output training restriction; verified via reader-proxy, not direct fetch (§4) |
| [EXT-LEGAL-003] | Google Gemini API terms — provider-output training restriction (§4) |
| [EXT-UNSLOTH-001] | LoRA/QLoRA hyperparameter starting points and verified-live by-size VRAM floors — primary source (§6, §10) |
| [NV-FINETUNESTACK-001] | LoRA-vs-full-SFT selection guidance (§10) |
| [NV-RTXAIGARAGE-001] | Dataset-size thresholds, PEFT vs full FT (§6, §10) |
| [NV-CURATORDESIGNER-001] | Large-scale curation/synthetic-data tooling — reference, not small-dataset methodology (§10) |
| [NV-TOOLCALLTUTORIAL-001] | Tool-calling fine-tune data-design pattern (§6, §10) |
| [EXT-TESTBED-001] | Toy-case-before-scaling corroboration for the rig-first principle (§4) |
| [NV-AGENTICBLOGS-001] | Evaluate/measure-first ordering, corroborating the evidence threshold (§4) |

**Gap dispositions in this chapter:**
- **G7 (model-license review for base weights, shared with chapter 13): COVERED** — the
  acquisition-time license-identity procedure (content hash + license snapshot,
  permitted-use check, attribution, license-change watch) is normative in chapter 13; this
  chapter states it as a required input (§2) and as a hard gate (§7) before any base weight
  or training data is touched.
- **Minimum-n**: no numbered gap, but stated explicitly per the thin-chapter honesty rule —
  no primary source establishes a minimum training-set size for a narrow behavioral fix;
  treated here as a field gap closed locally by ablation (§5, §6), not as a playbook
  omission.

---

> [← Previous](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) · [Index](README.md) · [Next →](10_DEPLOYMENT_AND_OPERATIONS.md)
