/** True under `astro dev` — caches bypass so canonical edits show on reload. */
export const IS_DEV: boolean =
  typeof import.meta !== 'undefined' &&
  !!(import.meta as { env?: { DEV?: boolean } }).env?.DEV;
