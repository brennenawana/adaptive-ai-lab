// @ts-check
import { defineConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';

// Static presentation layer over the canonical repository content.
// SITE_URL / SITE_BASE are provided by the deploy environment. Cloudflare Pages
// serves from a domain root, so SITE_BASE stays '/'; local dev also serves '/'.
export default defineConfig({
  site: process.env.SITE_URL ?? 'http://localhost:4321',
  base: process.env.SITE_BASE ?? '/',
  trailingSlash: 'always',
  build: { format: 'directory' },
  devToolbar: { enabled: false },
  vite: {
    define: {
      // absolute path of site/ on disk — bundled prerender code cannot derive
      // it from import.meta.url, and content is read from the repo at build time
      __SITE_DIR__: JSON.stringify(fileURLToPath(new URL('.', import.meta.url))),
    },
    plugins: [
      {
        // Canonical content lives OUTSIDE site/ (playbook/, research/). Watch
        // it in dev and full-reload on change so edits show immediately.
        name: 'watch-canonical-content',
        configureServer(server) {
          const dirs = ['playbook', 'research'].map((d) =>
            fileURLToPath(new URL(`../${d}`, import.meta.url)),
          );
          for (const d of dirs) server.watcher.add(d);
          server.watcher.on('change', (file) => {
            if (dirs.some((d) => file.startsWith(d))) {
              server.ws.send({ type: 'full-reload' });
            }
          });
        },
      },
    ],
  },
});
