/**
 * Full-text search: Pagefind index built after `astro build`.
 * The Pagefind UI assets live under <base>/pagefind/ in the production build;
 * in `astro dev` they are absent and the dialog shows a hint instead.
 */
declare global {
  interface Window {
    __aial?: { base: string; space: string | null };
    PagefindUI?: new (opts: Record<string, unknown>) => unknown;
  }
}

const dialog = document.getElementById('search-dialog') as HTMLDialogElement | null;
const openBtn = document.getElementById('search-open');
let loaded = false;

function base(): string {
  return (window.__aial?.base ?? '/').replace(/\/$/, '');
}

async function ensurePagefind(): Promise<void> {
  if (loaded) return;
  loaded = true;
  const mount = document.getElementById('search-mount');
  if (!mount) return;
  const cssHref = `${base()}/pagefind/pagefind-ui.css`;
  const jsSrc = `${base()}/pagefind/pagefind-ui.js`;
  try {
    const probe = await fetch(jsSrc, { method: 'HEAD' });
    if (!probe.ok) throw new Error('no index');
  } catch {
    mount.innerHTML =
      '<p class="search-missing ui">The search index is built with the production build.<br>Run <code>make site-build</code> once (or use the deployed site); <code>astro dev</code> alone does not create it.</p>';
    return;
  }
  await new Promise<void>((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = cssHref;
    document.head.appendChild(link);
    const s = document.createElement('script');
    s.src = jsSrc;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error('pagefind load failed'));
    document.head.appendChild(s);
  });
  if (window.PagefindUI) {
    new window.PagefindUI({
      element: '#search-mount',
      baseUrl: `${base()}/`,
      showSubResults: true,
      showImages: false,
      autofocus: true,
    });
  }
}

function openSearch(): void {
  if (!dialog) return;
  dialog.showModal();
  void ensurePagefind().then(() => {
    dialog.querySelector<HTMLInputElement>('input')?.focus();
  });
}

openBtn?.addEventListener('click', openSearch);

document.addEventListener('keydown', (e) => {
  const target = e.target as HTMLElement | null;
  const typing =
    target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable);
  if (typing) return;
  if (e.key === '/' || ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k')) {
    e.preventDefault();
    openSearch();
  }
});

dialog?.addEventListener('click', (e) => {
  if (e.target === dialog) dialog.close();
});

export {};
