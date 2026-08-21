# SYNTH-02: Private Local Deployment for Confidential Document Q&A

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

The [project profile](../GLOSSARY.md#project-profile) fields that route this
project (template: [PROJECT_PROFILE](../templates/PROJECT_PROFILE.md)):

| Field | Value |
|---|---|
| Business outcome | Cut senior-engineer time spent searching past project drawings and specs for code-compliance answers, for a structural-engineering consultancy |
| Task population & volume | ~150 queries/week over ~2,000 confidential documents (drawings, specs, compliance memos) |
| Criticality / failure cost | Moderate-high but caught before it matters — a wrong compliance citation could drive a costly design rework, but every answer is human-reviewed before it reaches a client submission |
| Quality / reliability target | No answer without a traceable source excerpt; citation-grounded only |
| Latency / throughput / SLA | Interactive, single user at a time; a few seconds to tens of seconds is acceptable |
| Privacy / security / residency | Contractual clause: no client document content may leave the client's private network, in any form, including to a managed API |
| Data & knowledge availability | ~2,000 documents as scanned PDFs and text exports; no prior retrieval corpus built |
| Tool / action permissions | Read-only retrieval; no write or external actions |
| Model candidates | Open-weights models sized to fit one on-prem GPU host, by parameter class only |
| Owned compute | One existing on-prem workstation-class GPU host (already owned, not purchased for this project) |
| Rentable compute | Not permitted — excluded by the residency clause, not by cost |
| Capex / recurring budget | Near-zero recurring cost (power only); no new capex planned at start |
| Staffing / time | One engineer, part-time, an eight-week runway |
| Deployment environment | Air-gapped internal network, no external egress |
| Observability constraints | Local logging only; no cloud telemetry |
| Regulatory / compliance | Client-contract data-residency clause |
| Existing evidence | None — cold start, no prior eval |
| Stakes / consequence tolerance | Tier 2 — business-consequential, reversible via the human-review gate |

## Archetype & rigor tier

The routing facts: rentable compute is not permitted (a hard residency
constraint, not a preference), the deployment environment is air-gapped, and the
only available execution surface is one owned GPU host. That combination fires
the **local/private deployment mandate**
[archetype](../GLOSSARY.md#archetype) — the QUICKSTART route that pulls chapter
02's execution-system identity work and reproducibility probes forward to the
start of the project, ahead of any candidate comparison.

Stakes tier is **Tier 2 (Consequential)**: a real business decision with
customer-adjacent consequences, kept reversible by the mandatory human-review
gate before any citation reaches a client-facing document.

## The decisive moves

1. **Execution-system identity pinned first.** Before any measurement, the team
   declares one frozen [execution system](../GLOSSARY.md#execution-system)
   (chapter 02): model artifact hash, quantization, runtime build, host identity,
   and harness version, all recorded together. On a single owned host, this
   identity — not "the model" — is the thing every later number is actually
   about.
2. **[STOP CONDITION] Reproducibility probe fires before the first comparison.**
   Chapter 02's restart probe is run before any prompt-variant comparison is
   trusted: the same 40 prompts are sent, the server process is restarted, and
   the same 40 prompts are sent again. Outputs disagree on several cases despite
   an unchanged pinned identity — evidence that "same pinned config" is not the
   same claim as "same session." The team was about to compare two prompt
   variants across two separate restarts; the probe result trips
   [00 §7](../00_PRINCIPLES_AND_SCOPE.md)'s tripwire ("a comparison is about to
   cross an unmeasured reproducibility boundary") before that comparison runs.
3. **Contemporaneous paired control adopted.** In response, both prompt variants
   are run back-to-back in the same server session with order pre-registered — a
   [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control)
   (chapters 02 and 04) — instead of the cross-restart comparison originally
   planned. The [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary)
   measured here is scoped to "same session"; no claim is made beyond it.
4. **Runtime regime chosen for determinism, not throughput.** Chapter 05's
   regime criterion is applied directly: a single interactive user, a low query
   volume, and a hard traceability requirement (every answer must cite a
   retrieved span) point to the determinism/provenance regime — single-slot
   serving, a pinned build, grammar-enforced structured citation output — over
   the throughput regime the team had defaulted to assuming ("more concurrency
   is always better" does not apply to a one-user-at-a-time system).
5. **Capacity fit probe eliminates a candidate before eval spend.** Chapter 06's
   capacity-fit check is run before any candidate is scored: the largest
   candidate, at the context window needed to hold a full document plus
   retrieval overhead, does not fit the host's VRAM headroom once a safety
   margin is reserved. It is dropped from the shortlist before a single eval
   item is run against it — eval budget is never spent characterizing a
   candidate that cannot be deployed.
6. **Grader stays deterministic; the judge-calibration protocol is N/A.**
   Every answer must cite a retrieved span; the grader checks that the citation
   exists and matches the source document (chapter 03's decision rule:
   objectively verifiable output ⇒ deterministic grading). No open-ended judged
   dimension exists in this task, so the judge-calibration protocol used in
   [SYNTH-01](SYNTH-01_api-only-assistant.md) simply does not apply here — stated
   explicitly rather than left silent.

## What was skipped and why

- **Chapter 11 purchase machinery** (demand ledger, purchase trigger): no
  purchase is being considered — the host is already owned, and rental is
  excluded by the residency clause rather than deferred by choice. The
  machinery is not needed until a capacity question actually arises.
- **Chapter 09 (training/data):** no
  [RC-10](../GLOSSARY.md#canonical-failure-taxonomy) evidence exists yet; the
  ladder has not been descended past retrieval/prompt rungs.
- **Tier-3 governance machinery** (pass^k reliability claims, tamper-evident
  record of record): the Tier-2 signature and the human-review gate cover the
  actual risk; escalating the whole project would be disproportionate.
- **Managed-API candidates:** not screened out for cost or quality reasons —
  excluded outright by the residency clause before the candidate set was even
  drafted. This is a hard constraint, not an unexamined option.

## Outcome

After the capacity fit probe removes the largest candidate, a mid-size
open-weights candidate is selected at a reduced context window sized to the
host's measured headroom. The reproducibility boundary is documented as
same-session-only, and every later comparison in the project is run under a
contemporaneous paired control. The system is piloted with three engineers,
read-only, with every compliance citation human-reviewed before use; no
compliance answer has been used unreviewed in a client submission by the end of
the eight-week runway.

## Chapter trail

[00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) ·
[01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) ·
[02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) ·
[03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[05. Model Runtime and Harness Selection](../05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) ·
[06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) ·
[10. Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md) ·
[GLOSSARY](../GLOSSARY.md)

---

> [Index](../README.md) · [Examples](README.md)
