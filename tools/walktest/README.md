# Walk-Test Rig — isolated, fully-observed workspace resumability testing

Answers one question honestly: **can an agent with no prior context orient in a
workspace, determine state, and act — from files alone?**

The first attempt at this test (2026-08-27) was invalid because a subagent
inherits its parent session's ambient context. Disclosure showed it received the
product repo's `CLAUDE.md`, a ~50-entry cross-session memory index carrying
specific claims about the systems under evaluation, and an env block with branch
and commit state — all before reading a single target file. Telling a subagent
"you have no prior context" removes none of that. This rig removes it
structurally.

## Why a subagent can never substitute

| Injection vector | Keyed by | Removed how |
|---|---|---|
| Project `CLAUDE.md` | cwd + ancestor walk | stripped at copy; ancestors verified |
| User `CLAUDE.md` | `~/.claude/CLAUDE.md` | verified absent |
| Memory index | **exact cwd path slug** (`~/.claude/projects/<slug>/memory/`) | sandbox lives at a brand-new `/private/tmp` path → no slug → no memory |
| `.claude/` hooks, incl. SessionStart doc-injectors | project dir | excluded from the copy |
| Env block (repo, branch, recent commits) | cwd git repo | `.git` stripped by default |
| Other agent files (`AGENTS.md`, `.cursorrules`, …) | cwd | excluded |

Everything above is asserted at build time; the build **fails closed** rather
than producing a quietly contaminated sandbox.

## Usage

```bash
./build.sh <source-dir> [--keep-git]     # → /private/tmp/walktest/<stamp>/
./run.sh   /private/tmp/walktest/<stamp> [--model sonnet]
```

`build.sh` prints the isolation report and ends with `RESULT: ISOLATED` or
fails. `run.sh` refuses to run against a sandbox that is not isolated.

## Layout

```
/private/tmp/walktest/<stamp>/
  workspace/           the stripped copy — the ONLY thing the agent may read
  logs/events.jsonl    every SessionStart / UserPromptSubmit / Pre+PostToolUse / Stop
  logs/report.md       the agent's walk-test report
  .claude/settings.json  logging-only hooks — at the PARENT, so workspace stays pristine
  MANIFEST.txt         files copied, what was stripped, isolation proof
```

Two deliberate choices: **logs live outside `workspace/`** so the agent cannot
read its own telemetry, and **hooks live at the parent** so the workspace copy
contains no `.claude/` for the agent to discover.

## Observability

`hooks/log.py` appends one JSON object per harness event: timestamp, event,
session id, cwd, tool name, **full tool input**, prompt text, and a bounded
result summary (`result_bytes` + first 600 chars). It writes **nothing to
stdout**, so the logger cannot contaminate the run it observes — verified as an
isolation check.

The session transcript under `~/.claude/projects/<sandbox-slug>/` is the
independent ground truth; the JSONL is the convenient view. Cross-check them
when a result matters.

```bash
jq -r 'select(.event=="PreToolUse") | "\(.tool)\t\(.tool_input.file_path // .tool_input.command // "")"' logs/events.jsonl
jq -r 'select(.tool=="Read") | .tool_input.file_path' logs/events.jsonl   # exact read order
```

The read order matters as much as the report: it shows what the structure
actually led the agent to, versus what the report claims.

## Known residual

`~/.claude/settings.json` global hooks inject a timestamp `systemMessage` on
UserPromptSubmit/Stop. Trivial, but it is non-workspace context; remove those
hooks for a maximally clean run. The build records this in every MANIFEST rather
than quietly ignoring it.

## Interpreting results

- **Relational findings** (contradictions *between* workspace files) are robust
  even in a contaminated run — nothing ambient can supply them.
- **Orientation answers** ("what is this", "what are the constraints") are the
  contaminated ones, and the reason this rig exists.
- A flattering report is a failed test. The friction log is the deliverable.
