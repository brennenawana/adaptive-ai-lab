# The winning evolved skill

`spreadsheet_values_and_oracle/` is published exactly as the loop wrote and
accepted it — no human edits. It was created by the frontier-guided arm (arm C,
seed 1): proposed from failure traces, accepted at validation 0.80, then patched
twice through the gate to 0.867 and 0.933. Its executor scored 80% on the
held-out test set, against a 36% no-skill baseline.

Two things worth noticing as you read it:

- **Its two core ideas** — compute in Python and write literal values instead of
  formulas; find the workbook's own worked example and use it as an answer key —
  were discovered from traces, not taught.
- **It contains machine-specific lines** (for example, a warning that `soffice`
  does not exist on the machine it evolved on). That is not a flaw; it is what
  skill evolution does — it captures facts about the exact environment it ran
  in. On your machine, the loop would learn your environment's facts instead.

`PURPOSE.md` is the loop's own record of why the skill exists: which failing
tasks it came from and which failure patterns it addresses.
