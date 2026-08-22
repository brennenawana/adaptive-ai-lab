# Workflow Hypothesis

This is a **working model**, not a claim about the prospect's implementation. The
"observed" sections are grounded in the supplied estimating-process description. The
"target" sections are project hypotheses to test against real artifacts.

## 1. Observed human workflow

```text
Bid invite
  ↓
Go / No-Go review
  ↓
Project folder + bid-document setup
  ↓
Bluebeam page review / labels / scale
  ↓
Room-by-room takeoff across plans/elevations/sections/details
  ↓
Material/finish interpretation + exclusions/questions
  ↓
Transfer quantities into Excel Bid Recap
  ↓
Material + shop labor + install + travel + drafting/CNC pricing
  ↓
Sanity checks + estimator/team overrides
  ↓
Word proposal + exclusions/qualifications
  ↓
PDF + email submission
```

The critical observation is that the workflow does not merely extract numbers. It
continuously combines **document interpretation, spatial coverage, material scope,
commercial assumptions, deterministic arithmetic, and expert judgment**.

## 2. Likely document graph

A useful mental model is a project graph rather than a pile of PDFs:

```text
PROJECT
├── revisions
│   ├── drawings
│   ├── specifications
│   ├── schedules
│   ├── RFIs
│   └── addenda
├── locations
│   └── room / area / elevation
├── scope observations
│   ├── source sheet/detail
│   ├── scope type
│   ├── material/finish
│   ├── quantity + unit
│   └── uncertainty / question
├── estimate lines
│   ├── material
│   ├── shop labor
│   ├── install
│   ├── travel
│   ├── drafting/CNC
│   └── overhead/markup
├── qualifications
│   ├── inclusion
│   ├── exclusion
│   ├── assumption
│   └── RFI
└── proposal / outcome
```

A single cabinet may require evidence from a floor plan, elevation, section/detail,
finish schedule, and specification. Revision lineage therefore belongs in the core
data model.

## 3. First target-system decomposition

### A. Intake and revision registry

- ingest bid invite, drawings, specs, schedule, RFIs, addenda;
- identify document type, revision/date, sheet/page labels;
- refuse or flag ambiguous supersession;
- preserve source identity for every downstream observation.

### B. Document navigation / scope map

- index rooms, sheet references, elevations, details, finish schedules, spec sections;
- identify likely millwork-bearing pages;
- maintain a coverage map so "not examined" is distinguishable from "examined, no scope".

### C. Takeoff assistant

- work room-by-room rather than only searching for isolated symbols;
- propose scope items and quantities with unit and source provenance;
- separate measured quantities from inferred/allowance quantities;
- surface low-confidence scale, geometry, material, or scope interpretations.

### D. Specification / finish interpreter

- connect finish codes and material callouts to scope items;
- extract AWI/QCP, wage, vendor, hardware, specialty-casework, and other bid-affecting requirements;
- generate explicit questions when required evidence is missing or contradictory.

### E. Deterministic estimate engine

Use code/tools for arithmetic and declared business rules:
- unit conversions;
- waste factors;
- labor formulas;
- material rollups;
- crew-hour / duration math;
- install/travel calculations;
- general-condition/material/labor/install sanity metrics;
- subtotal/markup/total calculations.

The model may choose/justify inputs; it should not be the calculator when the formula
is known.

### F. Verification / exception layer

Examples:
- room coverage complete?;
- referenced elevations/details actually checked?;
- quantities have valid units and sources?;
- finish/material mapping resolved?;
- stale drawing revision used?;
- arithmetic exact?;
- proposal total matches approved estimate?;
- exclusions implied by unresolved scope surfaced to reviewer?;
- outlier metrics require review rather than silent acceptance?

### G. Human estimator workspace

The initial UX should optimize **review**, not autonomous generation:
- source evidence beside each proposed item;
- accept / edit / reject;
- mark missed scope;
- mark material/quantity/qualification error type;
- record review minutes and correction severity;
- approve final estimate/proposal explicitly.

### H. Outcome learning

When available, link estimate lines to:
- actual material/labor/install costs;
- change orders;
- estimator corrections;
- win/loss outcome;
- margin / variance;
- project-specific anomalies.

This becomes the highest-value long-term evaluation data.

## 4. Human vs model vs deterministic code

| Responsibility | Default owner |
|---|---|
| Cross-document semantic interpretation | frontier multimodal model + human review |
| Find relevant sheets/details/spec clauses | retrieval/indexing + model |
| Quantity measurement proposal | model/vision + geometry tools + human review |
| Unit conversion and arithmetic | deterministic code |
| Known labor/waste formulas | deterministic code with versioned parameters |
| Ambiguous scope/material judgment | model proposal + human decision |
| Go/No-Go commercial judgment | human, with decision support only |
| Final bid value / qualifications | human approval |
| Proposal drafting | model/template + deterministic fields |
| Submission to GC/customer | human until separately authorized and validated |

## 5. Initial experimental objects

Even with the model frozen, candidates can be **system designs**:

- full-set ingestion vs millwork-page-only ingestion;
- room-by-room traversal vs retrieval-only lookup;
- explicit cross-sheet reference following vs flat context;
- free-form notes vs structured takeoff schema;
- model arithmetic vs deterministic calculator;
- one-pass extraction vs extraction + verifier;
- generic prompt vs reusable estimator skill;
- broad context vs staged context policy;
- source-citation requirement vs no citation requirement;
- different human-review interfaces.

Those comparisons are at least as important as model comparisons.
