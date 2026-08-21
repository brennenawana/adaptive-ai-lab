/** Highlight the table-of-contents entry for the section in view. */
const toc = document.getElementById('toc');
if (toc) {
  const links = [...toc.querySelectorAll<HTMLAnchorElement>('a[href^="#"]')];
  const byId = new Map(links.map((l) => [decodeURIComponent(l.hash.slice(1)), l]));
  const headings = [...byId.keys()]
    .map((id) => document.getElementById(id))
    .filter((h): h is HTMLElement => !!h);

  let active: HTMLAnchorElement | null = null;
  const setActive = (id: string | null) => {
    const link = id ? (byId.get(id) ?? null) : null;
    if (link === active) return;
    active?.removeAttribute('aria-current');
    link?.setAttribute('aria-current', 'true');
    active = link;
  };

  const visible = new Set<string>();
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) visible.add(e.target.id);
        else visible.delete(e.target.id);
      }
      // topmost visible heading wins; else keep the last one scrolled past
      const first = headings.find((h) => visible.has(h.id));
      if (first) {
        setActive(first.id);
      } else {
        const past = [...headings].reverse().find((h) => h.getBoundingClientRect().top < 120);
        setActive(past?.id ?? null);
      }
    },
    { rootMargin: '-64px 0px -70% 0px' },
  );
  headings.forEach((h) => io.observe(h));
}

export {};
