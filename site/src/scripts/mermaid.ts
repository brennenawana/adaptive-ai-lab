/**
 * Declarative diagrams: any canonical ```mermaid fence renders client-side.
 * The corpus currently contains none — this keeps the pathway open without
 * costing anything on pages that have no diagrams (the library chunk is only
 * fetched when a .mermaid block exists).
 */
const blocks = document.querySelectorAll<HTMLElement>('pre.mermaid');
if (blocks.length > 0) {
  void import('mermaid').then(({ default: mermaid }) => {
    const dark = document.documentElement.dataset.mode !== 'light';
    mermaid.initialize({ startOnLoad: false, theme: dark ? 'dark' : 'neutral', securityLevel: 'strict' });
    void mermaid.run({ nodes: [...blocks] });
  });
}

export {};
