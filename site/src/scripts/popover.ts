/**
 * Glossary popovers: explicit glossary links (class .gloss, data-term=slug)
 * show the canonical one-paragraph definition on hover/focus. Definitions come
 * from the per-space glossary JSON generated at build time from
 * playbook/GLOSSARY.md — same canonical source as the glossary page.
 */
const pop = document.getElementById('gloss-popover');
let defs: Record<string, { term: string; html: string }> | null = null;
let fetching: Promise<void> | null = null;
let anchorEl: HTMLElement | null = null;
let hideTimer: number | undefined;

function dataUrl(): string {
  const cfg = window.__aial ?? { base: '/', space: null };
  const base = cfg.base.replace(/\/$/, '');
  return cfg.space ? `${base}/versions/${cfg.space}/glossary.json` : `${base}/glossary.json`;
}

function loadDefs(): Promise<void> {
  if (defs) return Promise.resolve();
  if (!fetching) {
    fetching = fetch(dataUrl())
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((j) => {
        defs = j as typeof defs;
      })
      .catch(() => {
        defs = {};
      });
  }
  return fetching;
}

function position(target: HTMLElement): void {
  if (!pop) return;
  const r = target.getBoundingClientRect();
  const pw = pop.offsetWidth;
  const ph = pop.offsetHeight;
  let x = r.left + window.scrollX;
  let y = r.bottom + window.scrollY + 8;
  const maxX = window.scrollX + document.documentElement.clientWidth - pw - 12;
  if (x > maxX) x = Math.max(12, maxX);
  if (r.bottom + ph + 16 > window.innerHeight && r.top > ph + 16) {
    y = r.top + window.scrollY - ph - 8;
  }
  pop.style.left = `${x}px`;
  pop.style.top = `${y}px`;
}

function show(target: HTMLElement): void {
  const slug = target.dataset.term;
  if (!slug || !pop) return;
  window.clearTimeout(hideTimer);
  anchorEl = target;
  void loadDefs().then(() => {
    if (anchorEl !== target || !defs) return;
    const d = defs[slug];
    if (!d) return;
    pop.innerHTML = `<p class="gloss-term ui">${d.term}</p>${d.html}`;
    pop.hidden = false;
    position(target);
    target.setAttribute('aria-describedby', 'gloss-popover');
  });
}

function hide(): void {
  hideTimer = window.setTimeout(() => {
    if (pop) pop.hidden = true;
    anchorEl?.removeAttribute('aria-describedby');
    anchorEl = null;
  }, 120);
}

document.addEventListener('mouseover', (e) => {
  const t = (e.target as HTMLElement).closest?.('a.gloss') as HTMLElement | null;
  if (t) show(t);
});
document.addEventListener('mouseout', (e) => {
  const t = (e.target as HTMLElement).closest?.('a.gloss');
  if (t) hide();
});
document.addEventListener('focusin', (e) => {
  const t = (e.target as HTMLElement).closest?.('a.gloss') as HTMLElement | null;
  if (t) show(t);
});
document.addEventListener('focusout', (e) => {
  const t = (e.target as HTMLElement).closest?.('a.gloss');
  if (t) hide();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && pop && !pop.hidden) {
    pop.hidden = true;
    anchorEl?.removeAttribute('aria-describedby');
  }
});
// keep the popover open while hovering it (so links inside are clickable)
pop?.addEventListener('mouseenter', () => window.clearTimeout(hideTimer));
pop?.addEventListener('mouseleave', hide);

export {};
