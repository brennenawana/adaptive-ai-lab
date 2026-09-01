# Adaptive AI Lab

This lab develops and validates the **[Adaptive AI Systems
Playbook](playbook/README.md)** — an evidence-driven, project-independent
methodology for designing, evaluating, optimizing, deploying, and continuously
improving AI systems. The lab runs real project implementations, harvests their
frozen experimental evidence into curated case studies, and promotes what survives
into the playbook:

```
research evidence → playbook → project implementations → primary records
        ↑                                                      ↓
        └──────── playbook evolution ← curated case studies ←──┘
```

| I want to… | Go to |
|---|---|
| Start a new AI project with the methodology | [`playbook/QUICKSTART.md`](playbook/QUICKSTART.md) |
| Run an engagement interactively — an agent walks me through implementing the playbook on a lab or client project, with resumable state | [`playbook/operator/`](playbook/operator/README.md) (DRAFT; install the `/operator` skill from [`skill-template.md`](playbook/operator/skill-template.md) and just say "start an engagement") |
| Read the methodology | [`playbook/`](playbook/README.md) |
| Read and study it as a website (search, glossary popovers, versions) | `make site` — see [`site/README.md`](site/README.md) |
| See the evidence behind it | [`research/`](research/README.md) · [`playbook/references/SOURCES.md`](playbook/references/SOURCES.md) |
| See real project implementations | [`projects/fis/`](projects/fis/README.md) · [`projects/millwork-estimating/`](projects/millwork-estimating/README.md) |
| Read the curated case studies | [`playbook/examples/`](playbook/examples/README.md) |
| Understand how the lab itself is governed | [`docs/`](docs/README.md) |

## Project implementations

**FIS — the Fintech Integration Sandbox** ([`projects/fis/`](projects/fis/README.md))
is the lab's first project implementation: a realistic synthetic fintech laboratory
with deterministic ground truth, frozen eval suites, and fail-closed cryptographic
provenance. It is the empirical source of every real case study shipped so far. It
is a project *in* this lab, not the lab itself.

**Millwork Estimating** ([`projects/millwork-estimating/`](projects/millwork-estimating/README.md))
is the lab's second project implementation, currently in prospective-client discovery.
It applies the playbook to a consequential multimodal human-workflow problem:
architectural millwork/cabinetry estimating, takeoff, pricing, proposal generation,
and eventual estimate-to-actual learning. Its initial technical hypothesis is
frontier-model-first with deterministic calculation and mandatory human approval;
local proxy models, routing, and fine-tuning are evidence-gated interventions, not
starting assumptions.

**Authority in one breath:** `playbook/` is normative for reusable methodology;
`projects/<name>/` for that project's plan and execution; `docs/` for lab
governance; frozen records for the facts of their own events — and none of them
overrides another in its own domain (details: [`docs/README.md`](docs/README.md)).

Health check: `make test` (FIS suite + provenance verifiers) and
`make playbook-check` (the playbook's 7-check release validator). FIS operations
run from `projects/fis/` — start at its [README](projects/fis/README.md).
