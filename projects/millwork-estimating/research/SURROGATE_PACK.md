# Public Surrogate Document Pack

Purpose: approximate the **classes and structures** of documents likely to appear in
an architectural-millwork estimating workflow before prospect-specific files are
available.

These are not gold labels for the client. URLs were verified during research on
2026-08-22. Public accessibility does not imply redistribution rights, so third-party
binaries are referenced by URL and reproducibly fetchable from `../source/surrogate/`
rather than committed as canonical project evidence.

## Core surrogate chain

### S01 — Architectural drawing set

**Chatham, MA — Center for Active Living bidding plans (2026)**  
https://www.chatham-ma.gov/DocumentCenter/View/9876/CFAL-Bidding-Plans-February-2026-PDF

Why it matters:
- a real public architectural plan set;
- drawing index includes floor plans, RCPs, building/wall sections, millwork details,
  reception-desk details, room finish schedule, finish plans, and multiple interior
  elevation sheets;
- demonstrates why takeoff requires cross-sheet navigation rather than a single
  "millwork page."

Use for: document classification, sheet navigation, cross-reference extraction,
room/elevation/detail indexing, finish-schedule linkage, multimodal eval prototyping.

Limitation: unrelated project/company; not a prospect takeoff or pricing source.

### S02 — GC bid package / architectural-millwork scope

**Northbrook Public Library — RFID and 1st Floor Renovations Construction Manual
(2020)**  
https://www.northbrook.info/sites/default/files/bids/01%20NPL%20Construction%20Manual%2009.18.2020%20FINAL.pdf

Why it matters:
- real bid manual with instructions to bidders, drawing index, bid form, trade scope,
  schedule, labor-rate worksheet, sample agreement, insurance, and other requirements;
- explicitly includes Bid Package #3 Architectural Millwork;
- drawing index contains dedicated millwork sheets plus plans/elevations/details;
- trade-specific scope includes architectural cabinets/paneling and responsibilities
  such as millwork, solid-surface work, blocking/framing, cabinet hardware, filler
  panels, and grommets;
- illustrates prevailing-wage, site-condition, addenda/RFI, schedule, and commercial
  requirements that can affect Go/No-Go and price.

Use for: bid-intake ontology, scope/qualification extraction, trade-boundary analysis,
revision/addenda logic.

### S03 — Detailed construction estimate / Bid Recap analog

**Bloomfield Libraries — Design Development Estimate (2022)**  
https://bloomfieldct.gov/DocumentCenter/View/995/Design-Development-Phase-Estimate-PDF

Why it matters:
- real public cost estimate organized around description, quantity, unit, unit price,
  subtotal, and totals;
- contains finish-carpentry and architectural-millwork line items using SF/LF/EA;
- demonstrates the structured bridge between takeoff quantities and cost.

Use for: estimate-line schema, unit normalization, deterministic rollups, baseline
spreadsheet/estimate structure.

Limitation: a GC/design-development estimate, not the prospect's internal shop-cost
workbook.

### S04 — Real millwork proposal / qualifications

**Masterpiece Commercial Millwork — Sommet Blanc budget proposal (2023)**  
https://aspengroup.online/public/companyData/8/projects/1/images/1SkUb2W811tmEWK36uUCkPtBqjPXQKs5Q.pdf

Why it matters:
- proposal states drawing basis and addenda acknowledgement;
- line-item quantity/UOM/price structure;
- contains AWI/finish/schedule assumptions;
- has explicit clarifications, inclusions, and exclusions such as shop drawings,
  shipping/unloading, demolition, plumbing, blocking, hardware, permitting/bonding,
  overtime, AWI QCP certification, and final cleaning.

Use for: proposal schema, qualification/exclusion taxonomy, scope-boundary evals,
revision-basis fields.

Limitation: public example from an unrelated commercial entity; use only as a
structural surrogate.

### S05 — Job-cost / actuals feedback

**FOUNDATION — Sample Job Costing Report Book (2024)**  
https://www.foundationsoft.com/wp-content/uploads/2024/04/2024-04_FOUNDATION-SampleJobCostingReportBook_.pdf

Why it matters:
- demonstrates construction job-cost reporting and estimate-vs-actual concepts;
- useful proxy for eventual outcome feedback after award/production.

Use for: estimate→actual data model, variance taxonomy, production-learning loop.

Limitation: software-vendor sample, not millwork-specific and not prospect data.

## Takeoff / standards support

### S06 — Bluebeam takeoff workflow

**Bluebeam — Construction Takeoffs Guide**  
https://www.bluebeam.com/resources/construction-takeoffs-guide-2026/

**Bluebeam — Takeoffs and Estimation course curriculum (PDF)**  
https://downloads.bluebeam.com/pdfs/TakeoffsandEstimation-CourseCurriculum-mech.pdf

Why it matters:
- calibration/scale, length/area/count measurement, custom tools, Markups List,
  custom columns/formulas, and quantity export are close analogs to the supplied
  process;
- helps distinguish the drawing markup from the structured measurement record.

Use for: takeoff object schema, measurement provenance, tool-integration research.

### S07 — AWI architectural casework guidance

**AWI QCP — Practical Guide to the Architectural Woodwork Standards**  
https://awiqcp.org/wp-content/uploads/2020/06/a-practical-guide-to-the-architectural-woodwork-standards.pdf

**AWI — current standards resources**  
https://awiqcp.org/resources/

Why it matters:
- casework requirements can involve surface categories, finish requirements,
  materials, veneer/laminate choices, hardware, construction/installation quality,
  and certification;
- reinforces why spec extraction can materially change scope and price.

Use for: specification ontology and requirement extraction. Standards are reference
inputs, not a substitute for the project's actual contract documents.

## Workflow sanity checks from current industry examples

### S08 — Commercial millwork bid intake

**Taylor Made Custom Cabinetry — Commercial Bid Portal**  
https://tmcc-inc.com/commercial

Observed public intake fields include project/company information, scope categories,
bid due date, target install date, estimated value, bid type, drawings/spec upload,
and notes. The published process describes estimator review, missing-information
questions, then line-item budget/bid letter.

Use for: client-intake schema and expected handoffs.

### S09 — Millwork bid-package checklist

**Pio Custom Cabinetry — What to Include in a Millwork Bid Package (2026)**  
https://pioww.com/blog/millwork-bid-package-checklist.html

The checklist emphasizes full drawings, specifications/AWI grade, material/finish
selections, hardware, schedule/install window, and site/access information, and warns
against relying only on millwork sheets.

Use for: completeness gates and missing-information/RFI generation.

## What this surrogate pack supports

Reasonable hypotheses:

```text
INPUT → revision-aware document understanding
      → room/sheet/detail coverage
      → takeoff quantities + material/finish scope
      → deterministic estimate calculations + expert assumptions
      → proposal qualifications/exclusions
      → actual-cost feedback
```

It supports designing **schemas, eval tasks, and a first architecture**.

It does **not** support claims about:
- the prospect's actual workbook formulas or Bluebeam conventions;
- prospect estimate accuracy;
- the quality of any AI system on prospect projects;
- exact material/labor economics;
- the contract resale/assignment decision process.

One sanitized completed project from the prospect would reduce more uncertainty than
substantially expanding this public corpus.
