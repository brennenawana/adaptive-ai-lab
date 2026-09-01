# Playbook Feedback Ledger — skill-evolution-mvp

Candidate playbook learnings from this project, in the wholesaling ledger pattern.
Status values: CAPTURED (recorded here, changes nothing) → adjudicated via
`docs/playbook-development/EVIDENCE_MAP.md` → playbook rule. The six experimental
findings F-SE1-1…6 live in the frozen report
`research/2026-08-31_SE1_Skill_Evolution_Experiment_Report.md` §6; this ledger holds
operational learnings that arose around the experiment rather than inside it.

## F-SEP-1 — Model-tier delegation by reversibility and novelty — CAPTURED

**Candidate rule.** Assign model tiers by the reversibility and novelty of the
decision, not the technical difficulty of the task: frontier-level models (example:
Fable) create the rules — designs, contracts, compiled artifacts (skills, runbooks,
briefs), novel-incident diagnosis, verdict interpretation, adversarial review;
strong models (example: Opus) orchestrate frozen rules and handle listed incidents;
cheap models (example: Haiku) execute high-volume work whose output a gate, checker,
or schema verifies. Cheaper tiers fail closed: anything not covered by written
instructions stops and escalates. Full statement: `RUNBOOK.md` §8.

**Why.** Frontier spend compounds only when it produces artifacts that cheaper tiers
reuse; per-run frontier labor is the expensive habit the SE-1 economics argue
against.

**Evidence.** Project: SE-1 secondary result — frontier discovery gave reliable
per-seed outcomes (TEST 70–80) where cheap discovery scattered (48–81), while the
cheap executor did all volume work; inference cost per solved task fell ~3× once
frontier-compiled skills existed. This project's own operation followed the pattern
(frontier designed contract/rig/runbook; the run itself is Opus-operable). External:
WikiSkill cross-model transfer (arXiv:2608.27454 Tab. 2); the wholesaling
HANDOFF_PROTOCOL §4 model-selection table and compiled-brief practice. Single-project
evidence → class B ceiling. Likely playbook homes: ch. 05 (selection), ch. 08 §5.4
(routing/tiering), ch. 12 (operator practice).

## F-SEP-2 — Runbook compilation as the delegation mechanism — CAPTURED

**Candidate rule.** Before handing an experiment or operational loop from a frontier
model to a cheaper operator, compile the operating knowledge into one runbook with:
the commands, the standard sequences, an incident table (symptom → action), and
explicit never-decide-alone escalation rules. A recurring escalation is the signal to
add a runbook entry — moving that work down-tier permanently.

**Why.** Knowledge scattered across plans, contracts, and stories is frontier-only
knowledge; a single executable document is what makes the cheap tier safe. This is
the LLM-Wiki "schema" idea applied to operations.

**Evidence.** Project: `RUNBOOK.md` here, compiled from four documents after SE-1;
the incident table is exactly the set of incidents that consumed frontier judgment
during the run. External: WikiSkill's skills layer (compiled procedure beats scattered
experience: +15.0 ablation); Karpathy LLM-Wiki schema layer. Class B ceiling.

## F-SEP-3 — Session router + durable engagement state — CAPTURED

**Candidate rule.** Long-running engagements get a durable state file, a session
router, and a resume-with-identity-check protocol: any session begins by reading
recorded state, summarizing the position in plain words, and verifying the current
execution-system identity (ch. 02 sense) against what the active contract recorded
before continuing measured work. Conversational memory is never the record of where
an engagement stands. Draft mechanism: `playbook/operator/START.md`.

**Why.** Playbook engagements run weeks to months across many sessions; without a
router and durable state, every session pays a re-derivation tax and risks silently
continuing measured work in a changed environment.

**Evidence.** Project: wikiskills-lab's field-shaped pattern (state.json, streaming
writes, resume protocol, engagement folders, inbox), which is this lab's compaction
lesson productized — the SE-1 sessions themselves survived context compaction only
via files written as work happened. External: none yet; the disposition is a field
trial on the next real engagement before adjudication. Class B ceiling. Likely
playbook homes: ch. 12 (operator practice), ch. 14 (checklists), ch. 01 (intake).

## F-SEP-4 — Append-only engagement implementation ledger — CAPTURED

**Candidate rule.** Implementing the playbook produces an append-only,
decision-level action ledger written at act time (procedures entered, gates
passed/failed/inapplicable, artifacts produced, deviations, spend, handoffs, owner
decisions). State files and narratives — status updates, engagement reports,
evidence submitted for adjudication — are views derived from the ledger, cite its
rows, and the ledger wins on conflict. Draft format:
`playbook/operator/ledger-format.md`.

**Why.** The playbook prescribes ledgers everywhere (look, spend, prediction,
hash-chained record of record, ch. 13) yet keeps none about its own implementation;
engagement history is otherwise reconstructed after the fact — lossy, expensive, and
unauditable. The ledger is also the raw material every future EVIDENCE_MAP row
needs.

**Evidence.** Project: SE-1's ledger-first practice — spend reconciled from
append-only ledgers at close; the harness-written skill-impact audit trail; by
contrast, IMPLEMENTATION.md was hand-written narrative and was the expensive,
lossy part. External: ch. 13's record-of-record doctrine applied reflexively; no
published instance of a methodology keeping an implementation ledger about itself.
Class B ceiling. Likely playbook homes: ch. 12, ch. 13, ch. 01.
