# ICM-Architect — Assessment for This Workspace

> Evaluated 2026-08-27. Source: github.com/RinDig/icm-architect (MIT), backed by
> **arXiv:2603.16021**, "Interpretable Context Methodology: Folder Structure as
> Agentic Architecture" (Van Clief & McDermott, 2026-03-17) — **citation
> verified**; the paper exists and matches the tool's description.

## What it is

ICM replaces framework-level agent orchestration with **filesystem structure**:
numbered folders carry sequencing, hierarchy carries context scoping, plain
markdown carries state, and a single agent reads the right file at the right
moment. Six composable forms (pipeline, umbrella, record library, knowledge
bundle, context map, system map). Draws on Unix pipelines, modular
decomposition, multi-pass compilation, and literate programming. Ships as a
Claude skill that can also restructure an existing repo into the format.

## Scope disambiguation — the most important point

"Improve orchestration code" is ambiguous here and the two readings have
opposite answers:

| Target | ICM applies? |
|---|---|
| `app/orchestration/pipeline.py` (wholesaling) — SQLAlchemy workers, 6 stages, cron-driven **data/ETL** pipeline | **No.** Category error. This is not agent orchestration; the paper's scope is explicitly sequential workflows *where a human reviews output at each step*. |
| The **lab's** agent orchestration — session handoff, work orders, resumable state | **Yes**, directly — and we already converged on most of it independently. |

## Convergence with what exists

`projects/wholesaling/` is already an ICM-shaped workspace under a different
name: `GOAL.md` (role/context), `PROCESS_LOG.md` (append-only state),
`packages/P<N>/BRIEF.md` + `RESULT.md` (numbered stages carrying self-contained
context), `SESSION_PROMPTS.md` (routing/catalog). `HANDOFF_PROTOCOL.md` §0's
rule — *one self-contained file, no link-chasing* — **is** the ICM principle.

Adopting ICM wholesale would therefore mostly rename working structure. The
value is not the framework; it is the parts we have not got.

## What is genuinely worth taking

1. **The walk test.** *"An agent with no memory can orient, act, and report
   status using files alone."* This is a **testable property** and the thing
   `/goal` + `SESSION_PROMPTS.md` are supposed to guarantee but have never been
   validated against. Free to run, and it produces a defect list rather than an
   opinion. **Run this first, before adopting anything.**
2. **Vocabulary for the forms** — naming this workspace an *umbrella* over
   *pipelines* (packages) plus a *record library* (ledgers) clarifies where new
   artifacts belong, which is currently decided ad hoc.
3. **"Replace orchestration with structure"** as a design bias reinforces the
   §5b conclusion that the experiment loop should be a **script plus files**,
   not an agent turn per step. An ICM-shaped experiment workspace
   (numbered: pull → run → diff → analyze → decide) is a natural fit for the
   many-iteration loop, and is cheap to build.

## Cautions

- **Maturity: low.** 8 commits on main, no releases, no tests, and — stated
  plainly — **no performance metrics or experimental validation for the tool**.
  The paper is a methodology paper, not an evaluation. Under P12 this is
  **doctrine, not validated practice**; adopt it as *structure* (cheap,
  reversible) and never cite it as *evidence about outcomes*.
- **Never run the restructure over the existing provenance closure.** Our
  artifacts carry cross-citations: briefs cite lab paths, the feedback ledger
  cites document sections, commit messages cite files, and wholesaling PRs will
  cite package paths. An automated reshuffle would **silently break those
  citations**, and provenance integrity is the single thing this instantiation
  cares about most. If used at all: run it on a copy, or on a new sub-area
  (e.g. a fresh experiment workspace), never in place.
- **Harness coupling is mild and acceptable.** The generator is a Claude skill,
  but its *output* is folders and markdown — harness-agnostic. Given the open
  question about moving to a different harness (`HARNESS_SELECTION.md`), an
  artifact format that survives a harness swap is a point in its favor.

## Recommendation

1. **Run the walk test on `projects/wholesaling/` now** — free, and it validates
   or falsifies the workspace design we are already relying on. Fix whatever it
   exposes.
2. **Do not restructure the existing workspace.** It already satisfies the
   method; churn would cost provenance and buy naming.
3. **Consider an ICM-shaped workspace for the experiment loop specifically** —
   a new area, numbered stages, markdown state — where there is no existing
   provenance to disturb and the "structure instead of orchestration code"
   claim can be tested on real work.
4. **Ledger the outcome either way.** If the walk test finds real defects, ICM's
   contribution to this project is already proven and worth crediting; if it
   passes, that is evidence our independently-derived structure was sound.
