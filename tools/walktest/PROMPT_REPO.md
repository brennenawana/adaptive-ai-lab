You are a new engineer (or a new agent session, in a harness with no memory of
this project) opening this codebase for the first time. Your target is the
`workspace/` directory in your current working directory. Read ONLY files inside
`workspace/`.

Do not ask questions. Work only from files. You have no prior knowledge of this
project — everything you assert must trace to a file you actually opened.

Report, concisely:

1. **What is this system?** What does it do, end to end, in one paragraph.
2. **How do I run it?** The exact commands to install deps, run the backend, run
   the test suite, and run the frontend. Cite where you found each.
3. **Environments.** What is production, what is dev, and what must never be
   cross-wired? Cite.
4. **Workflow.** If asked to make a code change, what is the required process?
   Cite.
5. **Orientation for two subsystems.** Where would you start reading to
   understand (a) the property/listing ingestion pipeline and (b) underwriting /
   deal pricing? Name the actual entry-point files you would open first, and say
   how you found them.
6. **DOC-vs-CODE AUDIT — the most important section.** Take the orientation docs
   (CLAUDE.md and anything it points to) and VERIFY their concrete claims
   against the actual repo. Check at least: the stated Python/tooling setup vs
   what the repo actually contains; the stated database migration head vs the
   actual latest migration file; any stated file paths, commands, or versions.
   Report every claim that is STALE, WRONG, or UNVERIFIABLE, with the doc's
   claim, the actual fact, and the file path proving it. Be exhaustive and
   specific — this is the deliverable.
7. **ORIENTATION FRICTION LOG.** Every point the repo failed you: missing
   signposting, contradictory instructions, a thing you needed but could not
   find, a dead end, or an instruction you could not follow on this machine.
8. **Rate 1-5**: could a fresh session with no memory operate this repo from
   committed files alone? Justify. A flattering report is a failed test.

Begin with the reading order you actually followed.
