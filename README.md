# Adaptive AI Systems Playbook

An evidence-driven, project-independent methodology for designing, evaluating,
optimizing, deploying, and continuously improving AI systems.

It answers one question, repeatedly, at every stage of a project: **what should I do
next, and what evidence would justify it?** Fifteen chapters cover the arc from
deciding what to build, through building something that can measure it, running
experiments whose answers you can act on, choosing models and runtimes, optimizing,
deploying, and knowing when to stop.

Every rule states how much weight it can bear — `consensus`, `strong-evidence`, or
`inference` — so you can tell what is established from what is merely reasoned.

| I want to… | Go to |
|---|---|
| Start a new AI project with the methodology | [`playbook/QUICKSTART.md`](playbook/QUICKSTART.md) |
| Read the methodology | [`playbook/`](playbook/README.md) |
| Read it as a website (search, glossary popovers) | `make site` — see [`site/README.md`](site/README.md) |
| See the evidence behind it | [`playbook/references/SOURCES.md`](playbook/references/SOURCES.md) |
| Read the worked scenarios | [`playbook/examples/`](playbook/examples/README.md) |
| Look up a term | [`playbook/GLOSSARY.md`](playbook/GLOSSARY.md) |

## What's here

- **`playbook/`** — the book itself: chapters 00–14, a glossary, nine reusable
  artifact templates, the source ledger, and the worked examples.
- **`site/`** — a static reading interface over `playbook/`, built with Astro. It
  holds no content of its own; every page is generated from the Markdown at build
  time.

## Scenarios are illustrations, not evidence

Everything in [`playbook/examples/`](playbook/examples/README.md) is invented — every
project, number, and name. Each scenario takes a rule the book argues for, shows a
team ignoring it for reasonable-sounding motives, and follows what that cost.

They illustrate rules. They are never the evidence for them. Where the book claims
something is established, the support is an external source in the ledger.

## Checks

```
make playbook-check   # the playbook's release validator (inventory, portability, links, …)
make site             # build the site (also validates every rendered link)
```

## Writing

[`playbook/STYLE.md`](playbook/STYLE.md) holds the writing principles the book is
held to, and the tests a review checks against. It is authoring guidance and is not
published as part of the book.
