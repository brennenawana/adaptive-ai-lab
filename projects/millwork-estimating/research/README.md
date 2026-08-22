# Research — Millwork Estimating

Research snapshot initiated 2026-08-22 during prospective-client discovery.

This directory is **project evidence, not generic playbook doctrine**. Public sources
are used to infer plausible artifact shapes and industry workflow patterns while we
wait for prospect-specific examples. They do not establish the prospect's actual
spreadsheets, markup conventions, pricing logic, or performance.

## Evidence classes

1. **Prospect primary source** — `../source/client/Estimating Process.txt`.
2. **Public surrogate documents** — real bid manuals/drawings/estimates/proposals/job
   cost examples and official product/industry guidance.
3. **Project inference** — our proposed data model, workflow decomposition, eval plan,
   and system architecture. Inferences are labeled as such.

## Research conclusions with reasonable confidence

### The input is a document graph, not a single PDF

Public bid packages and drawing sets reinforce the prospect's own description: useful
scope can be distributed across floor plans, interior elevations, sections/details,
finish schedules, specifications, addenda, RFIs, and project schedules. A reliable
system needs revision and cross-reference awareness.

### Takeoff is both geometry and coverage

Bluebeam-style takeoff is not simply "measure a cabinet." It creates a visible
markup/measurement plus structured quantity metadata. The prospect's room-by-room
procedure also treats systematic coverage as a control against missed scope.

### The Bid Recap likely mixes deterministic rules and judgment

The prospect source names explicit formula-like labor/install rules and sanity ranges,
but also says to use common sense/teamwork and adjust. Public construction estimates
show the quantity/unit/unit-price/subtotal structure; the prospect's actual Excel
workbook is still a major unknown.

### Qualifications/exclusions are part of estimate correctness

Real millwork proposals make clarifications, inclusions, exclusions, revision basis,
lead-time/schedule assumptions, and AWI requirements first-class commercial content.
A numerically correct bid with a materially wrong scope qualification can still be a
bad estimate.

### Actuals create the learning asset

Job-cost reporting commonly compares original estimate, actual cost to date,
cost-to-complete, projected final cost, and variance. If the client can link these
back to takeoff/estimate lines, the resulting estimate→actual dataset is more valuable
than merely reproducing today's spreadsheet behavior.

## High-value unknowns

- Actual Bluebeam Tool Chest subjects/colors/custom fields and measurement export.
- Actual Bid Recap workbook layout, lookup tables, hidden formulas, overrides, and
  sheet-to-sheet dependencies.
- Vendor/material pricing sources and refresh cadence.
- How addenda/revisions alter in-progress estimates.
- Estimator disagreement and override behavior.
- Historical estimate-vs-actual accuracy by material/labor/install category.
- Win/loss/competitor information and how it changes aggressiveness.
- Exact contract assignment/resale underwriting process.
- Privacy/retention rules for bid documents and managed AI providers.

## Files

- [`SURROGATE_PACK.md`](SURROGATE_PACK.md) — curated human-readable corpus.
- [`source-manifest.yaml`](source-manifest.yaml) — machine-readable provenance and
  retrieval locations.
- [`../source/surrogate/`](../source/surrogate/) — downloader and source-management
  notes.
