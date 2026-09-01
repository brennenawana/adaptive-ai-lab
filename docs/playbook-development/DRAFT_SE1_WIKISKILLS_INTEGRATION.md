# DRAFT — SE-1 / wikiskills-lab integration into the playbook

**Status: DRAFT for owner adjudication (2026-09-01). Nothing here is
normative.** Chapter text lands only after the §1 rows are adjudicated;
the §4 operator layer is a proposal to be field-tested, not doctrine.
Maintainer document, same standing as EVIDENCE_MAP.md — not shipped.

Framing worth keeping in view: the relationship between the playbook and
wikiskills-lab is circular by design. The playbook supplied the machinery
(experiment contracts, look ledgers, consequence-bearing tolerances,
execution-system identity, promotion discipline); SE-1 exercised it;
wikiskills-lab productized it for outsiders; and the product's operator
experience (§4) is now the strongest candidate to flow back. Every arrow
in that circle should pass through the evidence map like anything else.

---

## 1. Candidate EVIDENCE_MAP rows

Proposed for `EVIDENCE_MAP.md` §2. Two format notes for landing time:

- Column 2 is headed "FIS evidence"; these are the first rows whose
  internal evidence is not FIS. Proposal: retitle the column **"Internal
  evidence"** and prefix entries `FIS:` / `SE-1:`. IDs and existing rows
  unchanged.
- SE-1 citations are to the frozen report
  `research/2026-08-31_SE1_Skill_Evolution_Experiment_Report.md`
  (cite-by-line; the report is frozen, so line numbers are stable).

| Generic rule (playbook home) | Internal evidence | External corroboration | Class |
|---|---|---|---|
| Evolved skills as a rung-4 exhaustion procedure: on procedural, tool-mediated families with mechanical scorers, gated skill evolution can substitute for model scale at inference time (07 §5.4) | SE-1: cheap executor 36.0%→75.7% on held-out TEST, +39.7pp [30.0, 49.3], p<0.001 (report L91–107, L154–157) | WikiSkill Table 1 (9B+skills beats bare 27B), arXiv:2608.27454 | B |
| Frontier optimizer with the cheap executor in-loop buys discovery *reliability*, not just peak (07 §5.4, 05) | SE-1: arm-C seed spread 70–80 vs arm-B 48–81; C−B +13.0pp [6, 20] (L158–161) | Adjacent only — the paper never ran this configuration; SE-1 is the primary evidence | B — needs a second task family before promotion past B |
| Gate on the small validation split; claim only on held-out TEST (03, 04) | SE-1: VAL peaks overstated TEST by 8–14pp in 6/6 runs; two identical no-skill baselines differed 6.7pp on VAL n=15 (L162–164) | WikiSkill small-split caveat; coheres with the existing look-ledger row (GSM1k exposure) | B |
| Spend projections must be measured, not estimated; re-project from first measured runs (04 §7 — annotate the existing consequence-bearing-tolerances row rather than adding a rule) | SE-1: the one real budget stop traced to an estimated unit cost reality beat by 1.9×; caps re-sized by amendment, fail-closed held (L165–168) | Clinical pre-specification doctrine (already cited on the parent row) | B (annotation) |
| Skills reduce inference cost per solved task; the economics case is independent of the accuracy case (07, 11) | SE-1: $0.225→$0.071–0.075 per solved task (~3×); skilled arms' full evaluations cost LESS than the unskilled arm's while solving twice as much (L141–147, L169–171) | WikiSkill App. D covers optimizer cost only; the per-task inference saving is internal-first | B |
| Meter provider usage by summing every model entry and billing the max of independent accountings (12, 13) | SE-1: single-entry reading undercounted ~30×; caught by smoke only because the ledger kept the CLI's own figure alongside ours (L172–174) | None published (implementation lesson) | B |
| Model-tier delegation by reversibility and novelty: frontier creates rules/artifacts, strong tier orchestrates frozen rules, cheap tier executes gate-verified volume; escalate on novelty, fail closed (00, 05, 14) | SE-1 program structure itself + RUNBOOK §8; F-SEP-1 (projects/skill-evolution-mvp/PLAYBOOK_FEEDBACK.md) | Consistent with the routing-mismatch class (RC-9) framing; no direct external instance | B |
| Runbook compilation as the delegation mechanism: recurring escalations become runbook entries that move work down-tier (12, 14) | SE-1: RUNBOOK.md written to let Opus-tier sessions run frozen contracts; F-SEP-2 | Standard-operating-procedure first principles; no published agent-tier instance | B |

## 2. Draft chapter-07 text (lands only after §1 adjudication)

### 2a. Addition to §5.4 (Prompt/workflow optimization discipline, rung 4)

> **Skill evolution: the systematic form of rung 4 for procedural task
> families.** When the task family is procedural and tool-mediated, the
> scorer is mechanical, and error analysis shows failure causes
> concentrated in a few recurring patterns, do not hand-iterate prompt
> and instruction text — run a gated skill-evolution loop (WikiSkill,
> arXiv:2608.27454): an optimizer model studies failure traces, keeps
> persistent notes, and proposes one skill create/patch per iteration;
> a candidate is accepted only if validation strictly improves; claims
> come from held-out TEST only.
>
> | Property | Value |
> |---|---|
> | Fixes (RC class) | RC-6 task-specification gap; RC-7 in-system verification gap (skills that install self-check procedures) |
> | Cost class | C2 (loop iterations on the iterate split + one held-out confirmation) |
> | Entry evidence | Mechanical scorer exists; headroom band satisfied (baseline far from 0% and 100%); failure-cause concentration visible in error analysis |
> | Exit evidence | Loop ran to plateau (or val-100) under a frozen contract with a spent-before-run look ledger; accepted skills' TEST gain read against the pre-registered floor |
> | Cheap diagnostic first | The baseline + headroom check itself; a dry run proving every scorer before spend |
>
> Optimizer-tier choice is an economics decision, not a capability one:
> self-evolution by the executor-tier model works; a frontier optimizer
> buys per-seed *reliability* (evidence row 2). Budget more seeds when
> staying fully local.

### 2b. Amendment to rung 7's entry evidence (fine-tuning)

Insert into the rung-7 entry-evidence cell, after "every rung above
satisfies its own Exit evidence cell":

> — which for rung 4 includes a skill-evolution pass run to plateau under
> a frozen contract, or a recorded inapplicability finding (no mechanical
> scorer, or failure causes not concentrated). A capability that gated
> skills can install from context is not RC-10; it is RC-6 wearing
> RC-10's costume.

### 2c. §10 vendor-recipe entry

> **wikiskills-lab** (private repo, github.com/brennenawana/wikiskills-lab
> — shared by direct access). The packaged, outsider-ready form of this
> chapter's skill-evolution procedure plus the surrounding discipline:
> interview → probe-verified observation → diagnosis → generated
> contract → gated loop. Field-tested end to end on SpreadsheetBench
> (its `benchmarks/spreadsheet/` is the full SE-1 record with receipts).
> Playbook machinery it productizes: EXPERIMENT_CONTRACT.md → generated
> measurement contracts; TEST_LOOK_LEDGER.md → `looks.jsonl` with the
> continuation rule; ch. 02 execution-system identity → its resume-time
> environment check; ch. 12 telemetry-floor doctrine → its Observability
> Checklist O1–O10 with probes; PROJECT_PROFILE.md → its interview
> profile. Use it when the client engagement fits its five-step shape;
> use this chapter directly when it does not.

### 2d. §11/§13 hooks

- Worked-example pointer: SE-1 (frozen report, cite by line) as the
  rung-4 skill-evolution exemplar, including the honest limits (one task
  family; concentrated failure cause; contamination mitigated not
  removed).
- Sources: §3 below. Citation rule honored: site corpus links `.md` only
  (the frozen report, not the HTML deep-dive). All edits must pass
  `playbook/tools/check_playbook.py` before landing.

## 3. Candidate sources.yaml entries

```yaml
  - id: WIKISKILL-PAPER-001
    org: "Google Research"
    title: "WikiSkill (Tang et al.) — wiki-mediated skill evolution for LLM agents"
    url: "https://arxiv.org/abs/2608.27454"
    type: "paper"
    pub_date: "2026-08-27"
    last_verified: "2026-08-30"
    maturity: "new"
    classification: "ADAPT"
    evidence_strength: "strong-evidence"
    claims: "3-layer loop (traces/wiki/gated skills); accept on strict val improvement; 9B+skills > bare 27B; cross-domain +11..+41; prompts CC BY 4.0"
    chapters: [3, 7]
    freshness: "stable"
    notes: "Primary reference for the rung-4 skill-evolution procedure; App. E prompts reproduced verbatim (attributed) in wikiskills-lab."

  - id: SE1-INTERNAL-001
    org: "adaptive-ai-lab"
    title: "SE-1: skill evolution with a frontier optimizer and a cheap executor (frozen report)"
    url: "research/2026-08-31_SE1_Skill_Evolution_Experiment_Report.md"
    type: "internal-case"
    pub_date: "2026-08-31"
    last_verified: "2026-08-31"
    maturity: "current"
    classification: "CASE"
    evidence_strength: "case-study"
    claims: "+39.7pp held-out on cheap executor; frontier optimizer buys seed reliability; ~3x cost/solved-task reduction; val overstates test 8-14pp; metering max-of-accountings"
    chapters: [4, 7, 11, 12]
    freshness: "snapshot"
    notes: "Cite by line; report frozen at commit 1f7427f. Untested config in the source paper — SE-1 is primary for the reliability claim."
```

(`wikiskills-lab` itself is referenced from the ch. 07 vendor recipe, not
the source ledger — it is tooling, not evidence; its evidence IS SE-1.)

## 4. The operator layer — the product teaching the playbook back

**Owner observation (2026-09-01):** a playbook engagement runs weeks to
months across many sessions, but the corpus is chapters plus templates —
there is no convention for a session to know where the engagement stands
and resume. wikiskills-lab solved exactly this for its own five-step
process, and the pattern is field-shaped: a router (`START.md`) that
reads durable state, streaming writes so files outlive conversations, a
resume protocol that re-checks execution-system identity before
continuing (which is chapter 02 doctrine, mechanized), engagement folders
frozen on completion, and an inbox where mid-work observations queue as
future candidates.

**Status update 2026-09-01: the kit is DRAFTED at `playbook/operator/`
(README, START router, interview, routing doctrine, ledger format — every
file headed DRAFT-pending-field-trial), and F-SEP-3/F-SEP-4 are CAPTURED
in the project feedback ledger. The design below is what was built; the
field trial and adjudication remain owner-gated.**

**The operator layer. Owner additions 2026-09-01: the append-only
engagement ledger is the core of it; the layer is a delivery mechanism
over the corpus, never a fork; and it exists so an agent can walk the
owner through implementing the playbook on lab and client projects the
way wikiskills walks an outsider — clone-alongside, conversational,
resumable.**

1. **Engagement implementation ledger (the record of record).**
   `engagement/ledger.jsonl`, append-only, written by the operator agent
   *as it acts* — one row per significant action at **decision level**
   (procedure entered, gate passed/failed, artifact produced, deviation
   recorded, spend, owner decision), never keystroke level and never
   batch-reconstructed. Rationale: the playbook prescribes ledgers
   everywhere (look, spend, prediction, hash-chained records, ch. 13)
   but keeps none about its own implementation; the ledger is also the
   raw material every future EVIDENCE_MAP row needs — SE-1's
   IMPLEMENTATION.md was hand-reconstructed narrative, and the
   generalized lesson is *ledger first, narrative distilled from it*.
2. **Router over derived state.** `ENGAGEMENT_STATE.json` is a
   **derived snapshot of the ledger** (position, next action,
   environment fingerprint); on conflict the ledger wins — the same
   rule as the budget meter recomputing totals from its ledger. On
   session start: no state → intake interview; state → summarize
   position in plain words and continue.
3. **Intake as interview.** Instantiate the existing
   `templates/PROJECT_PROFILE.md` conversationally — one question at a
   time, recommend-with-override, answers written as given — instead of
   handing the operator a blank template.
4. **Procedure-level routing — no reading assignments.** The corpus is
   large only if someone is told to read it. Every chapter shares the
   same 13-section skeleton, so "ch. 07 §5 rung 2, entry evidence
   pending" is a routable position: the operator surfaces the
   applicable procedure (§5), gate (§7), or ch. 14 checklist — never a
   whole chapter. The corpus stays normative and untouched; the layer
   is thin (door, not brochure — chapters are never rewritten into
   conversational form, because that copy would drift).
5. **Resume protocol.** Before continuing any experiment mid-flight:
   compare current environment identity against what the active
   contract recorded (ch. 02); mismatch → amend/re-baseline or record
   the deviation, never continue silently.
6. **Inbox.** `engagement/inbox/` for observations captured mid-work;
   surfaced at every session start; feeds the next decision point.

Audience boundary, permanent: wikiskills-lab serves outsiders; the
operator layer serves this lab's own engagements. They share patterns,
never files.

**Candidate rules** (for PLAYBOOK_FEEDBACK.md, then the map):

- **F-SEP-3:** *Long-running engagements get a durable state file, a
  session router, and a resume-with-identity-check protocol;
  conversational memory is never the record of where an engagement
  stands.* Internal evidence: wikiskills-lab field pattern + this lab's
  compaction lessons.
- **F-SEP-4:** *Implementing the playbook produces an append-only,
  decision-level action ledger written at act time; state files and
  narratives are views derived from it, and the ledger wins on
  conflict.* Internal evidence: SE-1's ledger-first practice (spend
  reconciled from ledgers; hand-written narrative was the expensive
  part); ch. 13's record-of-record doctrine applied reflexively.

External evidence: none yet for either — which is exactly why the right
adjudication is:

**Recommended disposition:** write OPERATOR.md (with the ledger format)
as a draft, run it on the next real engagement (millwork discovery is
the standing candidate), and adjudicate F-SEP-3/F-SEP-4 with that
engagement as internal evidence — the playbook's own rule that
procedures earn their place through use, applied to itself.

## 5. Adjudication checklist (owner)

- [ ] §1 rows: accept / amend / reject each (accepted rows land in
      EVIDENCE_MAP §2 with the column retitle noted above)
- [ ] §2a/§2b: land in chapter 07 (after §1), then run check_playbook.py
- [ ] §2c/§2d: land vendor recipe + example pointer + sources
- [ ] §3: append to sources.yaml, regenerate SOURCES.md via the renderer
- [x] §4 (done 2026-09-01): operator kit drafted at `playbook/operator/`;
      F-SEP-3/F-SEP-4 captured in PLAYBOOK_FEEDBACK.md
- [ ] §4 field trial: run the next real engagement (millwork discovery is
      the standing candidate) on the operator kit, then adjudicate
      F-SEP-3/F-SEP-4 with its ledger as internal evidence
