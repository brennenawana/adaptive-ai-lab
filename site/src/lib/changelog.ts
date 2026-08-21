/**
 * Parse playbook/CHANGELOG.md. Verified grammar:
 *   header: H1, blockquote preamble, semver-interpretation prose + bullets
 *   per version: `## <semver> — <YYYY-MM-DD> — <release name>[ (<BUMP>)]`
 *   body: optional prose then one `| What | Why | Evidence |` table.
 */
import { readCanonical, type Space } from './corpus.ts';

export interface ChangelogVersion {
  version: string;
  date: string | null;
  name: string | null;
  bump: string | null;
  bodyMarkdown: string;
}

export interface Changelog {
  /** raw markdown between the H1 and the first version H2 (semver rules, 1.0 gate) */
  introMarkdown: string;
  versions: ChangelogVersion[];
}

export function loadChangelog(space: Space): Changelog {
  const src = readCanonical(space, 'playbook/CHANGELOG.md');
  const versions: ChangelogVersion[] = [];
  const headRe = /^##\s+(\d+\.\d+\.\d+)(?:\s*—\s*([0-9]{4}-[0-9]{2}-[0-9]{2}))?(?:\s*—\s*([^(\n]+?))?(?:\s*\(([A-Z]+)\))?\s*$/gm;

  const matches = [...src.matchAll(headRe)];
  const firstIdx = matches.length ? matches[0]!.index! : src.length;
  // intro: after the H1 line, before the first version heading
  const afterH1 = src.indexOf('\n', src.indexOf('# ')) + 1;
  const introMarkdown = src.slice(afterH1, firstIdx).trim();

  matches.forEach((m, i) => {
    const start = m.index! + m[0]!.length;
    const end = i + 1 < matches.length ? matches[i + 1]!.index! : src.length;
    versions.push({
      version: m[1]!,
      date: m[2] ?? null,
      name: m[3]?.trim() ?? null,
      bump: m[4] ?? null,
      bodyMarkdown: src.slice(start, end).trim(),
    });
  });

  return { introMarkdown, versions };
}
