/** Three-mode appearance switch: light / dim / dark, persisted locally. */
type Mode = 'light' | 'dim' | 'dark';

function setMode(m: Mode): void {
  document.documentElement.dataset.mode = m;
  try {
    localStorage.setItem('aial-mode', m);
  } catch {
    /* private mode etc. */
  }
  reflect();
}

function reflect(): void {
  const current = document.documentElement.dataset.mode;
  document.querySelectorAll<HTMLButtonElement>('[data-mode-set]').forEach((b) => {
    const active = b.dataset.modeSet === current;
    b.setAttribute('aria-pressed', String(active));
  });
}

document.querySelectorAll<HTMLButtonElement>('[data-mode-set]').forEach((b) => {
  b.addEventListener('click', () => setMode(b.dataset.modeSet as Mode));
});
reflect();

// follow OS changes only while the reader hasn't chosen explicitly
try {
  if (!localStorage.getItem('aial-mode')) {
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('aial-mode')) {
        document.documentElement.dataset.mode = e.matches ? 'dim' : 'light';
        reflect();
      }
    });
  }
} catch {
  /* ignore */
}

// sidebar toggle (mobile)
const sbBtn = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
if (sbBtn && sidebar) {
  sbBtn.addEventListener('click', () => {
    const open = document.body.classList.toggle('sidebar-open');
    sbBtn.setAttribute('aria-expanded', String(open));
  });
} else if (sbBtn) {
  sbBtn.style.display = 'none';
}
