# Playbook Website (`site/`)

A human-optimized reading and learning interface over the **Adaptive AI Systems
Playbook** and the evidence around it. This directory contains **presentation
tooling only** — it holds no canonical content and is not normative for
anything.

```
canonical repository Markdown / YAML / Git history
                    ↓
        site build pipeline (this directory)
                    ↓
       human-optimized static web interface
```

## Commands

From the repository root:

| Command | What it does |
|---|---|
| `make site` | local dev server with hot reload (http://localhost:4321); edits to `playbook/` reload live |
| `make site-build` | reproducible production build: `astro build` → Pagefind search index → internal-link/anchor validation (build fails on broken links) |
| `make site-preview` | serve the last production build |

Direct npm equivalents (`cd site && …`): `npm run dev`, `npm run build`,
`npm run preview`, `npm run validate`.

## Framework decision (recorded 2026-08-21)

**Astro 7 (plain, no docs theme) + Pagefind + a unified/remark custom pipeline.**

Compared against the repository's specific requirements:

- **Docusaurus** — its versioning model copies content into `versioned_docs/`,
  exactly the second-source-of-truth this architecture forbids; two-state color
  mode is baked in (we need light/dim/dark); React runtime is unnecessary
  weight for a reading site. Rejected.
- **MkDocs Material** — content must live in a `docs_dir` (or be copied there);
  multi-version support (`mike`) commits built trees to a branch; a third theme
  mode, glossary popovers, and a YAML-driven ledger page all fight the theme;
  low design ceiling for a distinctive long-form reading experience. Rejected.
- **Astro + Starlight** — closest contender, but our content has no frontmatter
  (Starlight requires it), lives outside the site tree, needs a third theme
  mode and version routing Starlight doesn't model; we would override so much
  that the theme's value inverts. Rejected in favor of plain Astro.
- **Astro (chosen)** — fully static output, zero client JS by default, content
  read from arbitrary repository paths at build time, complete control of
  typography/theming/popovers, and Pagefind provides self-contained client-side
  search with no backend.

## Architecture

Everything renders from canonical sources at build time; nothing is copied into
this tree. Key modules:

- `src/lib/routes.ts` — the single source of truth mapping repository paths to
  site routes (both for page generation and for rewriting inter-document
  links).
- `src/lib/corpus.ts` — enumerates canonical files and defines page kinds,
  groups and reading order. Adding a playbook chapter, template or scenario
  requires **zero site configuration** — pages, navigation, prev/next and
  search pick it up on the next build.
- `src/lib/markdown/render.ts` — the unified/remark pipeline. It binds styling
  ONLY to explicit source semantics: `**[PRINCIPLE]…**`-family badges,
  `[STOP CONDITION]`, `status: doctrine — not yet exercised`, citation tokens
  (`[EXT-…-NNN]`, `[SCENARIO: SCENARIO-NN]`) validated against
  `playbook/references/sources.yaml`, and explicit `GLOSSARY.md#term` links
  (which become popovers). It never alters canonical prose: no reflow, no math
  pass (all `$` in the corpus is currency), no syntax-highlight guessing (all
  fences are bare ASCII/unicode diagrams), no auto-linking of plain words.
- `src/lib/{glossary,sources,changelog}.ts` — structured parsers for the
  glossary, the source ledger (`sources.yaml`, the record of record), and the
  changelog grammar.
- `scripts/validate-links.mjs` — post-build validation of every internal href
  and `#anchor` across the built site; the build fails on any broken link.

### Historical versions — disabled

This build renders the current working tree only. `versions.json` keeps an empty
`versions` list: with no entries, `allPages()` produces no version-scoped routes.
The mechanism it replaced rebuilt `playbook/` from pinned commits via `git show`,
which on a public build would resurrect content that was deliberately removed.
Leave the list empty.

### Search

Pagefind indexes the current space only (historical snapshots are excluded to
keep results canonical). The index is produced by the production build; in
`astro dev` the search dialog explains how to create it.

### Theme modes

Three deliberate modes — light / dim / dark — set as `data-mode` on `<html>`,
persisted in `localStorage`, following `prefers-color-scheme` on first visit
(dark systems get **dim**, the low-contrast long-session mode, by design). All
body-text pairs meet WCAG AA in every mode. Tokens live in
`src/styles/tokens.css`.

### Known canonical quirks the site handles

- Chapter 04 cites statistics-formulary anchors (`#icc`, `#mde`, …) that have
  no matching heading in `STATISTICS_FORMULAS.md` — broken on GitHub too (the
  playbook validator only checks glossary anchors). The site derives alias
  anchors deterministically (see `formularyAliases` in `src/lib/rendering.ts`)
  so readers land on the right section; a proper fix belongs in a playbook
  PATCH release.
- Four wrapped-prose lines in the corpus start with `+` or `N)` and render as
  lists under CommonMark everywhere (GitHub included); the site renders them
  canonically rather than silently editing frozen/canonical text.
- `<date>` in `templates/PROJECT_PROFILE.md` is bare inline HTML; the pipeline
  renders all raw-HTML tokens as literal text (the corpus contains no real
  HTML).

## Deployment

The site is fully static (`site/dist/`). A GitHub Pages workflow is included at
`.github/workflows/site.yml`. **One-time owner step:** GitHub → Settings →
Pages → Source: *GitHub Actions*; then run the `site` workflow from the Actions
tab (and optionally uncomment its `push:` trigger for automatic deploys). Any
other static host works the same way: `SITE_URL=… SITE_BASE=… npm run build`
and publish `dist/`.

## Future: agent prompt recipes

A second consumption interface over the same methodology (concise stage
prompts: "Start a Project", "Freeze an Eval Suite", "Run a Performance
Autopsy") can be added without a second source of truth: the pipeline already
parses every chapter into titled sections with stable slugs
(`renderDoc().toc`), templates and glossary into structured objects, and the
route map knows every artifact. A recipe would be a declarative list of
(repoPath, section-slug) pairs assembled at build time into an agent-ready
page or endpoint — same canonical inputs, different projection. Deliberately
not built in the MVP; the Learn page carries the concept note.

## Boundaries this site never crosses

- It writes nothing into `playbook/` (the playbook's portability validator
  scans that tree).
- Claim→source links are rendered only where the repository itself encodes
  them: citation tokens resolved against `sources.yaml`. Nothing is inferred.
