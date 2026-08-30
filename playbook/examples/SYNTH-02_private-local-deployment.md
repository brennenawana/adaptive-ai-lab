# SYNTH-02: Private Local Deployment for Confidential Document Q&A

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

A single clause in a client contract does most of the routing here: no client document
content may leave the client's private network, in any form, including to a managed API.
That is a written rule, not a preference, and no vendor configuration satisfies it — so
every managed model is out of scope before the candidate list is drafted, and the whole
system has to run on the one GPU host a structural-engineering consultancy already owns.
What runs on it is a question-answering assistant over about 2,000 confidential drawings,
specs, and compliance memos, so senior engineers stop hand-searching past projects for
code-compliance answers.

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

Three routing facts. Rentable compute is not permitted, and that is a hard residency
constraint rather than a preference. The deployment environment is air-gapped. And the
only execution surface left is one owned GPU host. That combination fires the
**local/private deployment mandate** [archetype](../GLOSSARY.md#archetype), QUICKSTART's
B, which pulls chapter 02's execution-system identity work and reproducibility probes to
the very front of the project — ahead of any candidate comparison.

Stakes tier is **Tier 2 (Consequential)**: a real business decision with
customer-adjacent consequences, kept reversible because a human reviews every citation
before it reaches a client-facing document.

## The decisive moves

1. **Execution-system identity pinned first.** Before anything is measured, the team
   writes down one frozen [execution system](../GLOSSARY.md#execution-system) (chapter
   02): model artifact hash, quantization, runtime build, host identity, and harness
   version, all recorded together. On a single owned host, that bundle — not "the
   model" — is what every later number is actually about.
2. **[STOP CONDITION] The reproducibility probe fires before the first comparison.**
   Chapter 02's restart probe is cheap and it runs first. Send the same 40 prompts.
   Restart the server process. Send the same 40 prompts again. Several cases came back
   different, with nothing in the pinned identity changed — so "same pinned config" and
   "same session" are two different claims on this host. The team had been about to
   compare two prompt variants across two separate restarts. That plan trips
   [00 §7](../00_PRINCIPLES_AND_SCOPE.md)'s tripwire — *a comparison is about to cross an
   unmeasured reproducibility boundary* — and it trips before the comparison runs, which
   is the only point at which a tripwire is worth anything.
3. **Contemporaneous paired control adopted.** The planned cross-restart comparison is
   replaced. Both prompt variants now run back-to-back in the same server session, with
   the order pre-registered — a
   [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control)
   (chapters 02 and 04). The
   [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) measured here
   extends to "same session" and no further, and no claim is made past it.
4. **Runtime regime chosen for determinism, not throughput.** Chapter 05 asks you to pick
   a regime before you pick an engine, and the profile answers it. One interactive user
   at a time. A low query volume. A hard traceability requirement, since every answer
   must cite a retrieved span. Those point to the determinism/provenance regime —
   single-slot serving, a pinned build, grammar-enforced structured citation output. The
   team had defaulted to assuming the throughput regime, on the instinct that more
   concurrency is always better. It is not, on a system that serves one person at a time.
5. **Capacity fit probe eliminates a candidate before any eval spend.** Chapter 06's
   capacity-fit check runs before a single candidate is scored. The largest candidate
   needs a context window big enough to hold a full document plus retrieval overhead, and
   at that size it does not fit the host's VRAM once a safety margin is reserved. It
   comes off the shortlist before one eval item is run against it. Eval budget is never
   spent characterizing a candidate that cannot be deployed.
6. **Grader stays deterministic; judge calibration is N/A.** Every answer must cite a
   retrieved span, and the grader checks that the citation exists and matches the source
   document. That is chapter 03's decision rule applied directly: objectively verifiable
   output means deterministic grading. Nothing in this task is open-ended enough to
   need a judge, so the judge-calibration protocol that
   [SYNTH-01](SYNTH-01_api-only-assistant.md) turns on does not apply here at all —
   stated out loud rather than left silent.

## What was skipped and why

- **Chapter 11 purchase machinery** (demand ledger, purchase trigger): no purchase is
  being considered. The host is already owned, and rental is excluded by the residency
  clause rather than deferred by choice. The machinery is not needed until a capacity
  question actually arises.
- **Chapter 09 (training/data):** no
  [RC-10](../GLOSSARY.md#canonical-failure-taxonomy) evidence exists yet, and the ladder
  has not been descended past its retrieval and prompt rungs.
- **Tier-3 governance machinery** (pass^k reliability claims, tamper-evident record of
  record): the Tier-2 signature plus the human-review gate cover the actual risk.
  Escalating the whole project would be disproportionate.
- **Managed-API candidates:** not screened out on cost or quality. They were excluded
  outright by the residency clause before the candidate set was even drafted — a hard
  constraint, not an unexamined option.

## Outcome

With the largest candidate removed by the capacity fit probe, a mid-size open-weights
candidate is selected, at a reduced context window sized to the host's measured headroom.
The reproducibility boundary is documented as same-session-only, and every later
comparison in the project runs under a contemporaneous paired control. The system is
piloted with three engineers, read-only, with every compliance citation human-reviewed
before use. By the end of the eight-week runway, no compliance answer has been used
unreviewed in a client submission.

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
