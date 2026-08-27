# Harness Selection — The Harness Effect and Whether to Move Off Claude Code

> Decision note, 2026-08-27. Governed by playbook **ch. 05 (Model, Runtime, and
> Harness Selection)** — the harness is a first-class component of the
> execution system, not a UI preference — plus ch. 02 (identity) and ch. 04
> (one factor per arm).

## 1. The premise is correct, and the magnitude is larger than model choice

"The harness effect" is a documented 2026 phenomenon, measured repeatedly:

- The **same model** (Opus) scores **93% in Cursor vs 77% in Claude Code** on
  Terminal-Bench 2.0 — a **16-point swing from harness alone**, no model
  change, no fine-tuning, no task-level prompt engineering.
- Across scaffolds the spread is wider still: Opus ranged **42% on a minimal
  scaffold to 78% on the full Claude Code harness — a 36-point swing** driven
  entirely by harness engineering.
- Three independent benchmarks in early 2026 quantified this across Claude
  Code, Codex CLI, Cursor, Aider, OpenCode, and Pi on the same agentic tasks.
- **DeepCode** (research system) scored 0.8482 vs Claude Code's 0.5871 **using
  the same base model** — the advantage attributed to agentic architecture,
  planning, and execution strategy rather than weights.

**DeepSeek Harness** is real: an open-source, model-agnostic coding agent that
drew ~141,000 GitHub stars within four days of release.

**Implication for this project:** harness variance (16–36 points) is larger
than the model-quality gaps we have been pricing to the third decimal. Choosing
GLM over Qwen matters less than choosing the scaffold that wraps either.

## 2. Three methodological consequences (these are not optional)

**(a) The harness is part of the frozen execution-system identity (ch. 02).**
Every result produced under Claude Code is a measurement of
*model + harness + tool schemas + loaded context*. Switching harness
**invalidates comparability with everything measured before it**. Any
before/after claim spanning the switch crosses an unmeasured reproducibility
boundary — global tripwire 3.

**(b) "GLM in DeepSeek Harness" is a two-factor change.** Moving from
Claude/Claude Code to GLM/DeepSeek Harness changes **both** model and harness
simultaneously. Ch. 04 §5 requires exactly one manipulated factor per arm
unless a factorial design is pre-registered. A two-factor swap that improves
things tells you nothing about *which* factor did it — and if it degrades
things, you cannot tell which half to roll back.

**(c) The same lesson applies inside the product.** For the wholesaling AI
surfaces, the "harness" is the prompt + tool scaffold in `app/ai` and the
vision/extraction lanes. If a 36-point swing is attributable to scaffolding in
general-purpose coding, then the condition-vision prompt scaffold is a
first-class variable in `estimate_rehab` accuracy — not a detail. This
strengthens the case for versioning prompts (package **P1**) rather than
weakening it.

## 3. The counter-considerations

**Novelty is not evidence.** 141k stars in four days is an adoption signal, not
a quality signal — and specifically not evidence about *this* task, *this*
codebase, or *this* workload. Benchmark worship is a named playbook
anti-pattern; so is treating a leaderboard as a statement about your project.

**A four-day-old harness is the least-validated component you could introduce
into a workflow whose entire output is supposed to be trustworthy evidence.**
CASE-004 in the playbook is thirteen harness defects that were initially
indistinguishable from model weakness. Adopting a brand-new scaffold to
*generate lab evidence* inverts the risk: harness bugs would surface as false
findings about the wholesaling pipeline, which is the exact silent-failure
class this instantiation exists to eliminate.

**Migration cost is real but lower than expected here** — by accident of good
design. The handoff protocol's work orders are **single self-contained markdown
briefs with no link-chasing** (`HANDOFF_PROTOCOL.md` §0). That format is
harness-agnostic: it ports to DeepSeek Harness, OpenCode, or Cline unchanged.
What does *not* port: the `/goal` slash command, subagent delegation by model
tier, and the Claude-Code-specific session conventions in `SESSION_PROMPTS.md`.

## 4. Recommendation: test it as a controlled experiment, not a migration

The harness effect is large enough that **not** testing alternatives is the
expensive choice. But the test must be designed, or it produces exactly the
kind of unfalsifiable "feels better" verdict the playbook exists to prevent.

**Cheap diagnostic gate (ch. 07 §5.2 pattern):**

1. **Fix the task set first.** Use 5–8 *already-completed* work items from this
   project — e.g. the P1 spec, a failure-taxonomy classification pass, a
   pipeline-run analysis. Real tasks, known-good outcomes, no invention.
2. **One factor per arm.** Three arms, not two:
   - A: Claude Code + current model *(incumbent baseline)*
   - B: Claude Code + GLM-5.3 *(model factor isolated — the z.ai plan already
     supports Claude Code)*
   - C: DeepSeek Harness + GLM-5.3 *(harness factor isolated, given B)*
   B vs A prices the model; C vs B prices the harness. The two-factor jump
   A→C is what to avoid drawing conclusions from.
3. **Pre-register the scoring** before running: task completed without human
   correction (deterministic); spec deviations; wall-clock; credits/requests
   consumed; and — critically — **factual accuracy of any claim it makes about
   the codebase**, since the loop's product is evidence.
4. **Pre-register bands.** GO / RE-SCOPE / DROP, with the sufficiency floor
   acknowledged: 5–8 tasks is a *screening* sample. It must print **RANKED**,
   not an inferential claim. It cannot license "harness X is better"; it can
   license "worth a fuller trial."
5. **Ledger the run.** Whatever the outcome, record it — this is the lab's own
   methodology being exercised on itself.

**Sequencing:** run this *after* the GLM plan's usage is logged (the §5e
two-week window), not concurrently — otherwise harness change and model change
and plan quota all move at once and none of them is measurable.

## 5. What would make this an easy yes

If DeepSeek Harness supports the z.ai and Qwen Anthropic-compatible endpoints
(likely — it is advertised model-agnostic and both vendors publish
Anthropic-format base URLs), then arm C costs nothing beyond the plan already
purchased. Verify that first; a harness that cannot reach the purchased plan is
a non-starter regardless of its benchmarks.
