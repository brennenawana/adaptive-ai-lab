# Adaptive AI Lab — Charter

> STATUS: CURRENT / NORMATIVE at the lab level. Extracted 2026-08-21 from
> `AI_SYSTEMS_LAB_MASTER_PLAN.md` §1/§11 (now `projects/fis/PROJECT_PLAN.md`)
> during the repository restructuring, and re-stated under the lab's identity.
> Owner-edited only, like the project plans it governs alongside.

## What this lab is

Not "benchmark local models." The product of this lab is a **reusable AI-systems
methodology**: the demonstrated ability to discover, for each task a company brings,
which combination of *model, runtime, harness, context, tools, workflow, verifier,
routing policy, and (only when justified) training intervention* solves it most
reliably and economically — and to prove it with evidence a client can audit.

That methodology now ships as the **Adaptive AI Systems Playbook** (`../playbook/`,
versioned, project-independent, extraction-ready). The lab develops and validates it
through a loop this repository's structure mirrors:

```
external research / evidence          research/
        ↓
Adaptive AI Systems Playbook          playbook/            (the product)
        ↓
project implementations               projects/<name>/     (FIS is the first)
        ↓
primary experimental evidence         projects/<name>/ + registries + artifacts
        ↓
curated case studies                  playbook/examples/CASE-*
        ↓
playbook evolution                    playbook/CHANGELOG.md (via docs/ governance)
```

**Project implementations are the means; the transferable methodology is the end.**
FIS — the Fintech Integration Sandbox (`../projects/fis/`) — is the first
implementation and the empirical source of every real case study shipped so far. Its
domain is disposable by design (clean-room, synthetic); the method it exercises is
the asset.

The playbook's own 1.0 gate (its CHANGELOG header) requires **two materially
different project instantiations through frozen executed contracts** — the standing
reason implementations stay adjacent to the methodology in this repository.

## Definition of done ("ready to transfer to a client")

The lab is done enough to sell when every row below has been exercised at least once
in a real project implementation **and** exists as a written, reusable procedure
(playbook chapter or template). Status column: FIS, as of 2026-08-20.

| Capability | Status |
|---|---|
| Task-specific trustworthy eval creation (ceilings, versioning, leakage guards) | **Done** (Suite v1→v3) |
| Local specialist selection under provenance + frozen contracts | **Done** (R6 method) |
| Reasoning-budget calibration as a procedure | M0/R7 |
| Frontier escalation with a deterministic gate | **Done** (R4; reliability qualification pending R9) |
| Measured routing economics (break-even, pass^k) | R9 |
| Self-hosted/rented tier operation (cross-node arms, pinned artifacts) | M0 onward |
| Training intervention when justified (rig, own-trace SFT, forgetting gate) | FT-rig/R8 |
| Serving characterization (AIPerf method, dual clocks, operating points) | Partial (autopsy); M0 telemetry + adoption |
| Shadow/canary promotion process | Doctrine written; exercised at first client system |
| Production failure harvesting into evals/training | Designed-in; exercised at first client system |
| Reproducible lineage end-to-end (incl. trained artifacts) | Done for downloads; `TrainedArtifact` pending |
| Publishable credibility artifacts | 3 identified (deterministic-gate cascade; class-identity ceiling; transport-serialization defect) — write-ups pending |

When the table is green (client-dependent rows may be green-by-doctrine), the next
engagement starts from procedure, not from research.
