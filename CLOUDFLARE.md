# Deploying to Cloudflare Pages

The site is a static Astro build with no adapter, so Pages serves `site/dist/`
directly.

## Project settings

| Setting | Value |
|---|---|
| Production branch | `playbook-public` |
| Root directory | `site` |
| Build command | `npm ci && npm run build` |
| Output directory | `dist` |
| Node version | 22 (pinned by `.node-version` at the repo root) |

## Environment variables

| Variable | Value | Why |
|---|---|---|
| `SITE_BASE` | `/` | The site is served from a domain root. A sub-path value breaks every internal link. |
| `SITE_URL` | the deployed origin, e.g. `https://<project>.pages.dev` | Used for canonical URLs and the sitemap. |

`SITE_BASE` defaults to `/` and `SITE_URL` to `http://localhost:4321`, so a build
with neither set still succeeds — it just emits localhost canonical URLs.

## What the build checks

`npm run build` runs three stages, and the whole thing fails if any of them does:

1. `astro build` — renders every page from `playbook/`.
2. `pagefind --site dist` — builds the search index.
3. `node scripts/validate-links.mjs` — walks every built page and fails on any
   internal link or `#anchor` with no backing file in `dist/`.

Run `python3 playbook/tools/check_playbook.py` before pushing as well. It is not
part of the site build, and it is what enforces that no project-specific content
reaches the published site.
