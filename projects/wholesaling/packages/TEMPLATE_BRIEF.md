# Work Order <ID> — <short name>

Status: DRAFT | AUTHORIZED v<N> (<date>)
Session model: <Opus|Sonnet> · effort high · one session, fresh context
Repo: ~/code/wholesaling · branch `feat/<name>` off `origin/dev` · PR to `dev`
Stop point: <PR-open (default) | merge-to-dev after green CI>

## Standing rules (complete — do not seek other process docs)

- This brief is your complete task context. Do NOT read documents outside the
  wholesaling repo; do not follow links except code `path:line` references.
  If something you need is missing here, that is a defect in this brief:
  STOP and report it in your final message rather than exploring or guessing.
- Echo check before any code change: restate objective, non-goals, acceptance
  criteria, and your stop point in 3–6 lines.
- Wholesaling repo rules that apply to this task: never push `main` or `dev`
  directly; feature branch → PR to `dev`; secret-scan before push; hermetic
  pytest must stay green; <any task-specific rules, inlined>.
- Scope changes are not yours to make. If the spec conflicts with what you
  find in code, STOP, write the conflict into RESULT.md, and end the session.
- At session end, append your report to `<this dir>/RESULT.md` using §7's
  format, then stop. Do not self-assess the acceptance gate; do not begin any
  other work.

## 1. Objective

<One paragraph. What exists when this is done.>

## 2. Why (compiled context — everything you need to know)

<2–6 sentences. The diagnosis/license behind this package, restated
self-contained. Inline any excerpt the agent must know verbatim.>

## 3. Non-goals

<Explicit list. Especially neighboring fixes the agent will be tempted to make.>

## 4. Spec

<Numbered, concrete. Files, behaviors, migration numbers, flag defaults.
`path:line` pointers into the wholesaling repo.>

## 5. Acceptance criteria (agent-checkable)

<Numbered. Tests/commands + expected results. The agent runs these and pastes
raw output into RESULT.md. The lab-side gate is separate and not the agent's.>

## 6. Verification commands

```bash
<exact commands>
```

## 7. RESULT.md format

```markdown
## <ID> result — <date>
- Branch / PR: <branch> / #<PR>
- Spec deviations: <none | list, with reasons>
- Acceptance output: <pasted raw>
- Discovered en route (not acted on): <list>
- Stopped at: <stop point honored>
```

---
Provenance (do not read — for audit only): <lab doc paths + contract IDs>
