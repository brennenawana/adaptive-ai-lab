# Skill template — invoke the operator without remembering paths

> DRAFT — pending field trial; see README.md in this directory.

Install this as a **user-level** skill (it must fire in engagement homes,
which live outside this repository): create
`~/.claude/skills/operator/SKILL.md` with the content below,
`{{PLAYBOOK_REPO}}` replaced by the absolute path of your checkout of
this repository. Re-copy it here first if this template changes.

```markdown
---
name: operator
description: Use when the user wants to start, resume, or continue a playbook engagement (lab or client project work with the Adaptive AI Systems Playbook), or says things like "start an engagement", "where were we with <client>", or "walk me through the playbook here".
---

# Playbook operator

The playbook checkout is at:

    {{PLAYBOOK_REPO}}

1. Read `{{PLAYBOOK_REPO}}/playbook/operator/START.md` and follow it.
   The engagement home is the current directory unless the user names
   another one.
2. If that file does not exist, the checkout is on a branch without the
   operator kit: tell the user to update it (`git checkout main && git
   pull` there), and stop — do not improvise the process.
3. START.md and the files beside it are the single source of truth for
   the engagement process. Never explain or run the process from memory.
```
