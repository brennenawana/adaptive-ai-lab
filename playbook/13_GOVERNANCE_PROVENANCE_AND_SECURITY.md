# 13. Governance, Provenance, and Security

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) · [Index](README.md) · [Next →](14_DECISION_TREES_AND_CHECKLISTS.md)
> **Reading time:** ~20 min. **Prerequisites:** 00, 01, 02, 04, 12.

## 1. Purpose and when to read this

Every other chapter tells you how to produce a trustworthy result. This chapter tells
you what must be true *around* that result so it stays trustworthy after the fact:
what is recorded, what is provably unaltered, what must never be reachable, and what
must never have entered the system in the first place.

Read this chapter before four moments, not after:

1. Before the first Tier-2+ [freeze](GLOSSARY.md#freeze) — the [record of
   record](GLOSSARY.md#record-of-record) must exist before anything gets frozen into
   it.
2. Before acquiring any base model weights or third-party dataset — the license and
   legality gate (§5, §7) runs at acquisition, not at ship time.
3. Before a model-facing tool gains a write or side-effecting capability — the
   threat-model gate (§5, §7) runs before the grant, not after an incident.
4. Before publishing anything derived from held-out evaluation content — the
   publication-hygiene gate (§9) runs before the artifact leaves the project.

This chapter operationalizes the [never-skippable floor](GLOSSARY.md#never-skippable-floor)
item 2 ([provenance](GLOSSARY.md#provenance)) at every [stakes tier](GLOSSARY.md#stakes-tier), and it is where
[P10 — fail closed, on a record of record](00_PRINCIPLES_AND_SCOPE.md#4-normative-principles)
gets its mechanics. It also carries the structural enforcement half of the
[gold-label boundary](GLOSSARY.md#gold-labels) that chapter 04 defines and the
[diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) that chapter 04 introduces —
both are cross-referenced here, not re-decided.

Three of this playbook's field gaps live primarily in this chapter and are marked
throughout: **G6** (PII/privacy in telemetry and trajectories), **G7** (model-license
review), and **G8** (tool-calling security threat model). Their dispositions are
summarized in §13.

**Read this before committing to a delivery timeline.** No dedicated template exists
yet for four of this chapter's core deliverables — the record of record, the license
register, the privacy-classification table, and the tool-calling threat model (§12);
§11's worked tables are the field sets to instantiate by hand until one ships. And the
G6 redaction-before-persist pipeline for real (non-synthetic) personal data and the
entire G8 tool-calling threat-model procedure carry `status: doctrine — not yet
exercised` (§9, §11). A Tier-3 team arriving here for the first time — including one
routed in for a regulatory or audit obligation — should plan to build tooling and
validate a procedure this playbook has designed but not yet run, not to receive a
pre-built one; budget for that before a compliance review is scheduled against it.

## 2. Inputs required

- The [project profile](GLOSSARY.md#project-profile): [stakes tier](GLOSSARY.md#stakes-tier),
  privacy/security/residency fields, tool/action-permission fields, regulatory
  fields (01).
- The [execution system](GLOSSARY.md#execution-system) definition this project has
  adopted — provenance binds to it (02).
- The [gold-label boundary](GLOSSARY.md#gold-labels) rule and the
  [diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) mechanism (04) — this
  chapter enforces both structurally.
- The [trajectory record](GLOSSARY.md#trajectory-record) field set this project
  persists (12) — the privacy classification in §5 is applied to it.
- An inventory of every model, dataset, and hosted provider in the loop, with a
  link to each one's current license or terms of service.

## 3. Decisions this chapter supports

- What must be tamper-evident versus merely logged, and at which stakes tier.
- Whether a model or dataset may be acquired and used at all (the legality/license
  gate).
- What a tool-using system may do autonomously, and what requires a human in the
  loop, by consequence class.
- What must never enter the corpus, prompt, or trained artifact (the
  [clean-room boundary](GLOSSARY.md#clean-room-boundary)).
- What must be redacted, minimized, or time-limited before telemetry persists.
- What "audit-ready" concretely means for this project, and how to rehearse it.

## 4. Normative principles

**[PRINCIPLE] Tamper evidence is a deliberate build, not a byproduct of logging.**
(inference — first-principles, corroborated by EXT-OPS-003) Mainstream
experiment-lineage tooling gives you versioning and
lineage-by-reference; none of it gives you tamper evidence
[EXT-OPS-003]. If a decision's provenance must survive an audit, a dispute, or a
"what actually produced this number" question asked six months later, the chain has
to be hash-linked and append-only by construction — dashboards may mirror it, they
never replace it (P10). [CASE: CASE-009] shows what versioned, non-negotiable record
discipline looks like in practice: comparisons across instrument versions were
refused by the tooling itself, which is what made a real criteria drift auditable
instead of silently absorbed.

**[PRINCIPLE] Sensitive data is isolated at two independent layers, and the
isolation is tested, not assumed.** (consensus — defense-in-depth is standard
security-engineering practice) A single enforcement layer — an
application-level filter, a naming convention, a code-review habit — is one bug away
from a leak. Pair an application-level control (an explicit denylist/allowlist of
readable fields) with an infrastructure-level control that holds even when the first
layer has a defect (a database role with no grant on the protected schema, a network
boundary, an import ban on the modules that can see it), and add a test that actually
attempts the leak through the model-facing path and asserts refusal. This applies
identically to answer keys (below) and to any other data class this chapter treats
as protected — the same pattern this playbook calls
[ground-truth isolation](GLOSSARY.md#ground-truth-isolation) when the protected
class is an answer key. [CASE: CASE-003] is the general cautionary instance: a
feature set looked clean until a leave-one-group-out audit showed it had
reconstructed a forbidden signal by another route — a
[class-identity ceiling](GLOSSARY.md#class-identity-ceiling) reached by a channel
nobody had enumerated. [Leakage](GLOSSARY.md#leakage) paths are found by auditing,
not by inspection.

**[PRINCIPLE] Fail-closed refusal belongs to the runner, not to policy.**
(case-study + inference — the same evidence basis as P10, which this operationalizes)
At Tier 2 and above, work lacking its prerequisites —
registration, a frozen contract, passed integrity gates — is refused
[fail-closed](GLOSSARY.md#fail-closed) by the execution machinery itself, never
merely discouraged by a written rule (P10). The
same applies one level down: a pre-registered [consequence-bearing
tolerance](GLOSSARY.md#consequence-bearing-tolerance) whose breach clause is not
mechanically enforced is not a control, it is a hope. [CASE: CASE-001] is the
generalizable failure: a named consequence existed on paper and did not fire,
because nothing in the execution path was wired to enforce it.

**[PRINCIPLE] Legality and license review happen at acquisition, not at ship time.**
(consensus) Every model, dataset, and hosted provider entering a project carries
terms that can prohibit the exact use the project needs — training a competing
model on outputs, redistributing weights, commercial use without a separate
agreement. Check the *current* terms before the artifact enters the system, record
what was checked and when, and re-check per project: vendor terms move on
independent, unsynchronized clocks, and a check performed for one project does not
transfer to the next [EXT-LEGAL-001], [EXT-LEGAL-002], [EXT-LEGAL-003] — three major
providers' current terms, checked on the same day, carried three different,
independently revised effective dates.

**[PRINCIPLE] Minimize and gate by default; do not log everything and sort it out
later.** (heuristic) Default telemetry and trajectory collection to metadata plus
explicit outcome signals, excluding raw sensitive content by default and adding
richer capture only when a stated need justifies it and a redaction step precedes
persistence. Default tool permissions to read-only, with write or side-effecting
capability granted per tool, per action class, scaled to consequence — never granted
wholesale because a broader grant was easier to configure. Both defaults exist for
the same reason: what was never collected cannot leak, and what a tool was never
permitted to do cannot be misused by it.

**[PRINCIPLE] Audit is a replay, not a narrative.** (inference — first-principles)
"We can explain what happened" is not auditability; a third party who was not in the
room, given only the record of record, must be able to *reconstruct* what produced a
specific decision-driving result without asking the team. Anything that requires an
insider's memory to interpret is not yet governed, however well it is documented in
prose. §9 gives the concrete rehearsal.

## 5. Default procedure

Eleven obligations. The first ten are in the order a project normally encounters
them; the eleventh (regulated personal data in an eval corpus) is numbered last for
cross-reference stability but is typically encountered *early*, alongside chapter
03's corpus-construction work — resolve it then, not at the end. Tier 1 projects may
satisfy several with a short written note (per the [rigor
dial](GLOSSARY.md#rigor-dial)); Tier 2+ projects satisfy them structurally.

1. **Stand up the record of record before the first Tier-2+ freeze.** Hash-chained,
   append-only, one entry per irreversible state transition (registration → contract
   freeze → qualification → confirmation-unlock → confirmation). A reset is refused;
   the log may only be extended.
2. **Bind every entry to an execution-system digest**, not a filename, port, alias,
   or version string (02). A composite digest — artifact content hash × runtime
   binary/library digest × material launch configuration × request-config hash —
   survives exactly the identity confusions a human-readable name does not.
3. **Enforce fail-closed refusal in the runner.** Unregistered or unfrozen work
   cannot execute at Tier 2+; a [diagnostic run
   kind](GLOSSARY.md#diagnostic-run-kind) stays inside the same ledger as a
   cryptographically non-promotable state, so a cheap diagnostic never becomes an
   unrecorded side channel (04).
4. **Isolate every protected data class at two layers and test the isolation**
   (§4). Apply this first to the [gold-label boundary](GLOSSARY.md#gold-labels)
   (04): the answer key is unreachable from any model-facing surface by permission
   *and* by a reachability test that actually tries.
5. **Write a clean-room boundary** for anything the project must never contain:
   proprietary third-party material, unlicensed data, secrets, and — for consultants
   and contractors — anything derived from an employer's or client's non-public
   systems (§6).
6. **Run the license/legality gate before acquisition** for every model and dataset,
   and the terms-of-service check for every hosted provider before training on its
   outputs (§6, §7).
7. **Classify every trajectory/telemetry field by privacy class** and apply the
   matching default (collect / collect-with-minimization / redact-before-persist /
   never-collect) before the pipeline goes live (§6; feeds chapter 12's telemetry
   floor).
8. **Threat-model the tool-calling surface before granting write or side-effecting
   capability**, and gate write actions by human approval scaled to stakes tier
   (§6).
9. **Apply publication hygiene** before anything derived from held-out evaluation
   content leaves the project: [canary strings](GLOSSARY.md#canary-string), no
   verbatim eval text, stated benchmark provenance (§9).
10. **Rehearse the audit.** Periodically, hand the record of record for one past
    decision to someone who was not involved and ask them to reconstruct what
    produced it. A step they cannot reconstruct is a gap in the record, found while
    it is still cheap to fix.
11. **Decide, per eval corpus, how regulated personal data is handled before any of
    it is annotated** (feeds chapter 03's corpus-construction work — see the pointer
    there). Explicitly choose one, in writing, for each corpus that contains it:
    **de-identify** before the corpus is built, **tokenize/pseudonymize** with a
    reversible key held outside the corpus, or **hold it raw under an
    access-control boundary**. State the trade-off in measurement-validity terms,
    not just privacy terms: de-identification can shift the input distribution the
    eval measures, which can move a stratum's [reachability
    ceiling](GLOSSARY.md#reachability-ceiling) and invalidate the claim that a score
    transfers to production on un-de-identified input; holding content raw avoids
    that shift but narrows who may ever see the corpus. Reconcile annotator access
    with the two-layer isolation of obligation 4 by isolating the *gold labels*,
    not the source content, from the model-facing path — an annotator who must read
    regulated content to label it correctly sits inside that content's own trust
    boundary, which is a different boundary than the one gold labels are isolated
    from. Set a retention window for the corpus at least as strict as §6's
    retention parameter for the matching privacy class, applied to the *frozen
    suite*, not only to live telemetry. *status: doctrine — not yet exercised —
    same G6 basis as obligation 7; this playbook's own source project ran on
    structurally synthetic data and never faced this decision for real regulated
    content (see §9, §13).*

## 6. Project adaptation parameters

| Parameter | Depends on | How to set it |
|---|---|---|
| **[PARAMETER]** Hash-chain granularity | Record volume, audit obligations | One entry per irreversible state transition is the floor; add per-artifact entries when individual artifacts (not just runs) need independent provenance. |
| **[PARAMETER]** Privacy-class taxonomy | Domain, regulatory tier, data sources | Start from §6's four-class table below; add domain-specific classes (e.g., a regulated-industry identifier class) rather than overloading an existing one. |
| **[PARAMETER]** Retention windows per privacy class | [Stakes tier](GLOSSARY.md#stakes-tier), residency constraints in the project profile | Tier 1: shortest window that supports debugging. Tier 2+: the longer of the regulatory minimum and the look-ledger's active window; never indefinite by default. |
| **[PARAMETER]** Tool-permission tiers | Reversibility and consequence of each action class | Read-only by default; write actions get their own tier per §6's table, gated by stakes tier, never by tool convenience. |
| **[PARAMETER]** License-review checklist depth | Commercial vs. research use, consultant/employer overlay, redistribution plans | The §7 checklist is the floor for any acquired model or dataset; add redistribution and attribution-chain review when the project's output will itself be redistributed. |
| **[PARAMETER]** Audit-rehearsal cadence | Stakes tier, regulatory obligation | Tier 1: opportunistic. Tier 2: at least once per suite-release cycle (03). Tier 3: scheduled, and folded into the periodic methodology audit (12). |
| **[PARAMETER]** Eval-corpus regulated-data disposition | Corpus source, regulatory tier, whether human annotation requires reading the raw content | Per corpus (§5 obligation 11): de-identify / tokenize / hold-raw-under-access-control; record which stratum's ceiling and production-transfer claim the choice could affect, and whether the transform's effect on the measured ceiling was actually checked or is still unverified. |

**Privacy classification (the four-class floor for trajectory/telemetry fields, feeding
chapter 12's telemetry floor):**

| Class | Example fields | Default | Feeds chapter 12 as |
|---|---|---|---|
| None | task/run ID, execution-system digest, timestamps | Collect | metadata |
| Indirect identifier | free-text task description, session ID | Collect with minimization (truncate, hash, or tokenize where feasible) | context/output field |
| Direct identifier / sensitive category | names, contact details, health or financial detail appearing in content | Redact before persist | redacted placeholder |
| Secret | credentials, API keys, tokens | Never collect | resolved inside the tool broker; never echoed to any store |

The table above classifies *telemetry and trajectory* fields produced by a running
system. Regulated personal data appearing in a **corpus assembled for evaluation**
(03) is a separate decision, not an instance of this table — see §5 obligation 11 —
because the corpus is model-facing content whose transformation can change what the
eval measures, not merely what a log retains.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Acquisition gate.** Before any model weights or dataset enters the
project: license identity recorded (content hash + license snapshot), permitted-use
check passed for the project's actual intended use. **Outcomes:** PROCEED (recorded)
/ BLOCK (use prohibited) / ESCALATE (ambiguous terms — legal review before use).

**[DECISION GATE] Tool-permission gate.** Before a tool or action moves from
read-only to write-capable: threat model reviewed (§6), human-approval policy
defined for the action's stakes tier. **Outcomes:** GRANT-WITH-APPROVAL-GATE /
GRANT-AUTONOMOUS (Tier 1 only, reversible, low blast radius) / DENY.

**[DECISION GATE] Publication gate.** Before anything derived from held-out
evaluation content is published: canary strings embedded, no verbatim eval-item
text present, benchmark provenance stated. **Outcomes:** PUBLISH / HOLD (remediate
first).

**[STOP CONDITION]** Work is about to run at Tier 2+ without a frozen contract or
registration in the record of record (P10) — refuse by machinery, not by asking.

**[STOP CONDITION]** A review finds a protected data class enforced at only one
layer (an application filter with no infrastructure-level backstop, or vice versa) —
treat as an open leak until the second layer exists and is tested.

**[STOP CONDITION]** A provider's terms of service have not been re-checked since
acquisition and training on its outputs is planned or underway — halt training-data
use from that provider until re-verified.

**[STOP CONDITION]** A tool grant would enable a write or side-effecting action
outside the reviewed threat model — deny the grant; do not expand the threat model
retroactively to justify a grant already made.

**[STOP CONDITION]** Held-out or protected content is about to be published without
a canary string or with the pre-publication check skipped "just this once" — hold
publication.

## 8. Metrics and formulas

N/A — this chapter is structural and procedural, not statistical. Its instruments
are counting-based rather than inferential: the count of ledgered, non-promotable
[diagnostic runs](GLOSSARY.md#diagnostic-run-kind) (04), the pass/fail result of the
ground-truth reachability test (§4), and the pass/fail result of the audit-replay
rehearsal (§5 step 10). The statistics canon for decision-quality claims lives in
chapter 04 and [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md).

## 9. Failure modes and anti-patterns

### Provenance and fail-closed enforcement

**[REJECTED]** (condition: always)

- **Dashboard-as-record-of-record**: treating a mainstream lineage/tracking tool
  (MLflow/W&B/DVC-class) as the authoritative store rather than a mirror of it
  [EXT-OPS-003]. None of these tools offers tamper evidence; using one as the
  record of record silently drops the guarantee the record exists to provide.
- **Identity by name**: trusting a model's filename, a server's port or alias, or a
  human-readable version string as its reproducibility identity. Two runtime builds
  can silently define the same internal format tag with incompatible physical
  layouts — the artifact looks compatible by name and size and decodes differently.
  Digest the actual binary and every library it maps; never the name attached to it.
- **Single-layer protection**: an application-level filter alone protecting a
  sensitive data class, with no independent infrastructure-level backstop.
- **The relaxed lane**: a parallel "quick" execution path outside the record of
  record for convenience. It recreates exactly the unrecorded path the machinery
  exists to forbid (P10); a cheap tier belongs *inside* the machinery as a
  non-promotable state, not beside it.

### Legality, licensing, and the clean-room boundary

**[REJECTED]** (condition: always)

- **Checked once, trusted forever**: verifying a provider's terms of service at
  project start and never again, while continuing to train on its outputs months
  later under terms that may have changed.
- **Employer-specifics leakage**: including any employer- or client-specific
  schema, logic, prompt, or "inspired by" reconstruction in a reusable or
  publishable artifact, even when the general domain category is public knowledge.
  The test in §6 exists precisely to catch this.
- **Auto-promoting ephemeral capability**: letting a system that can autonomously
  create a candidate tool, workflow, or configuration convert it into durable,
  trusted platform configuration without a separate, explicit review and promotion
  gate — the same discipline as [observe-only
  graduation](GLOSSARY.md#observe-only-graduation) (08), applied to capability
  itself rather than to a routing decision.

### Privacy and telemetry (G6)

*status: doctrine — not yet exercised (see §11 for what validation would look
like)* — applies to the redaction-before-persist pipeline and the subject-rights
design below; the minimize-by-default framing is ordinary data-protection practice
and does not require internal validation to state.

**[REJECTED]** (condition: always)

- **Collect first, classify later**: persisting full trajectory content by default
  on the theory that fields can be redacted retroactively. A field that was never
  written cannot leak from the store; a field that was written and later "redacted"
  may already be in a backup, a log line, or an index.
- **Immutable-record-implies-undeletable-payload**: assuming an append-only,
  hash-chained record forbids ever satisfying a legitimate erasure request. It does
  not — see the structural pattern in §6.
- **Treating corpus de-identification as free**: de-identifying or tokenizing an
  eval corpus and continuing to cite its old reachability-ceiling or
  passing-threshold numbers without re-checking whether the transform changed the
  measured ceiling (§5 obligation 11). The corpus is a different instrument than
  the one those numbers were measured on until that check is done.

### Tool-calling security (G8)

*status: doctrine — not yet exercised (see §11 for what validation would look
like)* — this entire subsection.

**[REJECTED]** (condition: always)

- **Granting write capability before threat-modeling it**: adding a write or
  side-effecting tool because it is useful, then writing the threat model
  afterward if at all.
- **Trusting retrieved or tool-returned content as instruction-free**: treating
  text that arrived via a tool result or retrieval as inert data, when it is
  attacker-reachable content the model will read as context and can be crafted to
  redirect it (prompt injection via tool outputs).
- **Secrets in the traversed path**: putting credentials, API keys, or tokens
  anywhere a prompt, a trajectory record, or a log line can capture them, rather
  than in a credential store the tool broker resolves at call time and never
  echoes back.

## 10. Vendor recipes

| Verdict | Source | What it gives you | What it does not |
|---|---|---|---|
| **[REFERENCE: EXT-OPS-003]** | MLflow / Weights & Biases / DVC | Versioning and lineage-by-reference; a good dashboard mirror | Tamper evidence — none of the three offers it |
| **[REFERENCE: NV-LINEAGEREGISTRY-001]** (as-of 2026-08-20) | NGC Private Registry + NeMo Entity/Data Store | Semver artifact versions, per-version metrics, HF-compatible one-hop base-model/adapter lineage fields | No end-to-end dataset→deployment lineage prescription; adapter artifacts are versionless in the same system — plan your own chain across the gap |
| **[REFERENCE: NV-WORKBENCH-001]** (as-of 2026-08-20) / **[REFERENCE: NV-NEMOCLAW-001]** (pre-alpha, as-of 2026-08-20) | Git-versioned agent-sandbox environments; a credential-custody wrapper pattern | Useful building blocks for the sandbox/credential-custody control in §6 | Neither is a governance system by itself; no run/eval tracking, no production maturity claim |
| **[REFERENCE: NV-GARAK-001]** (as-of 2026-08-20) | An LLM security-probing tool | A ready battery for injection/adversarial red-teaming of the tool-calling surface (§6) | Not a substitute for a project-specific threat model — a probe library finds known shapes, not your system's actual attack surface |
| **[FOLLOW: EXT-LEGAL-001]** (eff. 2025-06-17 / AUP eff. 2025-09-15) / **[FOLLOW: EXT-LEGAL-002]** (eff. 2026-01-01) / **[FOLLOW: EXT-LEGAL-003]** (eff. 2026-03-23, rev. 2026-04-28) | Anthropic Commercial Terms + Usage Policy; OpenAI Business Terms; Google Gemini API terms | Each currently prohibits using that provider's outputs to train a competing model, with provider-specific exceptions | Read the current page for your provider at training time — these three effective dates, checked the same day, do not agree with each other |
| **[ADAPT: NV-NEMOTRONCC-LICENSE-001]** (as-of 2026-08-20) | An NVIDIA open-model license document | A worked contrast case: this license explicitly *permits* training other models on that model's outputs | Do not generalize the permission — check the specific license text for whatever model you acquire; permissions are not symmetric across vendors |
| **[ADAPT: EXT-EVAL-007]** | BIG-bench canary-string convention | A standard, citable format for a cooperative-scraper exclusion marker | Cooperative only — it deters compliant crawlers and detects verbatim reproduction; it is not access control |

## 11. Worked examples

All identifiers, hashes, and names below are invented and illustrative.

**Composite execution-system digest.** An execution system is not one artifact; its
digest is computed over everything that can silently change behavior:

```
digest = H( artifact_content_hash
          ‖ runtime_binary_and_library_digest
          ‖ material_launch_configuration
          ‖ request_config_hash )
```

Two runs with the same displayed model name and the same runtime version *string*
can still land at different digests if a mapped library changed underneath the
version string — which is the point: the digest, not the label, is what a
comparison claim is allowed to trust (02).

**Two-layer isolation, worked as a table.** For the [gold-label
boundary](GLOSSARY.md#gold-labels) specifically:

| Layer | Mechanism | What it catches |
|---|---|---|
| Application | An explicit denylist of protected fields/schemas in the tool-broker code path | A tool definition that would otherwise expose the answer key |
| Infrastructure | A database role with no grant on the protected schema, independent of the application code | An application-layer bug that bypasses the denylist |
| Test | A test that calls the model-facing path and asserts the protected data is unreachable | Silent regression in either layer above |

The same three-row pattern applies unchanged to any other protected class this
chapter covers — secrets, PII, employer-specific material.

**Model-license review, walked through.** Acquiring an illustrative open-weight base
model:

1. Record content hash + a snapshot of the license text at the moment of
   acquisition (license pages change; the snapshot is what you actually agreed to).
2. Check, explicitly: commercial use permitted? Fine-tuning/derivative permitted?
   Redistribution permitted, and under what conditions? Who owns outputs?
3. Log attribution obligations (many open licenses require one) as a durable
   artifact, not a comment in a README.
4. Set a license-change watch: a periodic check (manual or automated) against the
   model card or license page, because acquisition-time terms are not guaranteed to
   persist.
5. Repeat independently for every dataset used in fine-tuning (09) — dataset and
   base-model licenses are reviewed separately; a permissive model license says
   nothing about the data license.

**Subject-rights erasure under an append-only chain.** Hash-chain the *record*
(event metadata, content digests, timestamps); store the *payload* (the actual
trajectory content) in a separate, deletable store, referenced from the chain by
digest. An erasure request deletes the payload; the chain retains only the pointer
and the fact that something was once there and was later removed under a stated
policy — the chain's integrity is unaffected because it never held the sensitive
content directly. *status: doctrine — not yet exercised.*

**Tool-calling threat model, worked as a table.** An illustrative support-agent
system with three tools (a lookup tool, a document-retrieval tool, a
ticket-update-write tool):

| Attack surface | Example | Mitigation |
|---|---|---|
| Prompt injection via retrieved content | A retrieved document contains text instructing the model to ignore prior instructions | Treat retrieved content as untrusted data in the prompt structure; never let it carry instruction-level authority; verify tool-reported content against the schema before use |
| Prompt injection via tool output | A tool result field contains adversarial text crafted by whatever produced that data | Same as above — the boundary is "did this content originate outside the trust boundary," not "which tool returned it" |
| Credential exfiltration via a tool argument | A crafted request tries to make the model echo a resolved credential back into its own output | Credentials resolve inside the tool broker and are never passed through the model's context in either direction |
| Unauthorized write action | The model attempts a ticket-closing action outside its granted scope | Least-privilege tool permissions (read-only default); write actions gated by human approval scaled to [stakes tier](GLOSSARY.md#stakes-tier); every invocation logged to the audit trail |

*status: doctrine — not yet exercised.*

## 12. Outputs and artifacts

- The **record of record**: hash-chained, append-only, one entry per irreversible
  state transition, referencing execution-system digests.
- A **clean-room boundary document**: what must never enter this project, the
  shape-vs-specifics test (§6), reviewed at project start and whenever a new data
  or content source is added.
- A **license register**: one row per acquired model/dataset — content hash,
  license snapshot, permitted-use determination, attribution obligations,
  license-change-watch status.
- A **trajectory privacy-classification table** (§6), feeding chapter 12's
  telemetry floor.
- A **tool-calling threat model** and permission-tier table (§6), reviewed before
  any write-capable grant.
- A **canary-string registry** for anything published from held-out content.
- An **eval-corpus regulated-data disposition record** (§5 obligation 11): for each
  eval corpus containing regulated personal data, which transformation it underwent
  (de-identify / tokenize / hold-raw-under-access-control) and what was verified
  about that transform's effect on the corpus's measured ceiling — the field this
  chapter recommends chapter 03's suite-release record carry alongside its other
  release metadata.
- Any principle override, as a
  [method decision record](GLOSSARY.md#method-decision-record)
  ([template](templates/METHOD_DECISION_RECORD.md)) (00).

No dedicated template exists yet for the last four of these; §11's tables are the
field sets to instantiate until one is written (open issue, §13).

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-OPS-003] | Mainstream lineage tooling lacks tamper evidence — the case for building the record of record |
| [EXT-LEGAL-001] | Anthropic Commercial Terms + Usage Policy — output-training restriction, verified live |
| [EXT-LEGAL-002] | OpenAI Business Terms — output-training restriction, verified via proxy |
| [EXT-LEGAL-003] | Google Gemini API terms — output-training restriction, verified live |
| [NV-NEMOTRONCC-LICENSE-001] | Contrast case: a vendor license that explicitly permits output-training |
| [NV-LINEAGEREGISTRY-001] | Vendor lineage-registry mechanics and their prescription gap |
| [NV-GARAK-001] | Security-probing tool referenced for tool-calling threat-model red-teaming |
| [NV-WORKBENCH-001], [NV-NEMOCLAW-001] | Agent-sandbox and credential-custody building blocks |
| [EXT-EVAL-007] | Canary-string convention for publication hygiene |
| [INT-CASE-001], [INT-CASE-003], [INT-CASE-009] | Empirical case evidence — fail-closed enforcement, leakage-audit discipline, versioned record discipline |

**Gap dispositions in this chapter:**

- **G6 (PII/privacy in trajectories and telemetry): COVERED, parts doctrine.** The
  classification-and-minimize-by-default framing (§4–§6) is ordinary data-protection
  practice. The redaction-before-persist pipeline for real (non-synthetic) PII and
  the subject-rights erasure design (§9, §11) carry
  *status: doctrine — not yet exercised* — this playbook's own source project ran on
  structurally synthetic data with a policy check (§6) refusing non-local data
  egress by construction, which is real, exercised practice for *avoiding* real PII
  entirely, but is not the same as having exercised redaction of real production PII.
  §5 obligation 11 extends G6 to regulated personal data appearing in an **eval
  corpus** specifically (as opposed to telemetry) — the decision to de-identify,
  tokenize, or hold raw under access control, and its measurement-validity
  trade-off — added this pass on the same doctrine-not-yet-exercised basis; no
  internal execution record covers it either.
- **G7 (model-license review): COVERED.** §6 and §11 give the acquisition-time
  checklist (content hash + license snapshot, permitted-use check, attribution
  obligations, license-change watch) as a compliance procedure informed by ordinary
  licensing practice, not requiring an internal execution record to state
  correctly. Cross-referenced from chapter 09 for the training-data instance of the
  same gate.
- **G8 (tool-calling security threat model): COVERED-AS-DOCTRINE-NOT-YET-EXERCISED.**
  §6, §9, and §11 give the full procedure (attack-surface enumeration,
  least-privilege permissions, write-action gating by stakes tier, credential
  custody, audit trail, injection red-teaming pointer); the source project's tools
  were read-only by construction and never exercised a write-capable grant, so this
  section is prescribed doctrine, marked accordingly throughout.
- **Cross-referenced, not owned here:** G16 (gold-label boundary) and G17
  (diagnostic run kind) are primary in chapter 04; this chapter states only their
  structural enforcement mechanism (§4, §5).

**Open issue for a future pass:** no dedicated template exists yet for the license
register, the privacy-classification table, or the tool-calling threat model (§12);
consider adding `templates/GOVERNANCE_LICENSE_AND_THREAT_MODEL.md` or equivalent in
a future minor version.

---

> [← Previous](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) · [Index](README.md) · [Next →](14_DECISION_TREES_AND_CHECKLISTS.md)
