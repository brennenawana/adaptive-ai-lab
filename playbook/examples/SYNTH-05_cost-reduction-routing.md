# SYNTH-05: Cascading a Frontier-API Support System — and Refusing a Learned Router

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

The system already works, and that is the entire starting position. One managed
frontier-API model handles 100% of volume — it triages every incoming support ticket and
drafts a first response; the quality bar it holds has actually been measured; the only
thing wrong with it is the invoice. "Fernbank Software," a SaaS company, wants the same
quality for less money
across ~40,000 tickets a month. Everything below depends on that incumbent being
*measured* — without a trusted eval and a real baseline, this is not a cost-reduction
project at all, it is a project to find out what the incumbent is doing.

| [Project profile](../GLOSSARY.md#project-profile) field | Value |
|---|---|
| Business outcome | Cut cost per resolved ticket, no quality regression |
| Task population & volume | ~40,000 tickets/month: triage classification + first-response draft |
| Criticality / failure cost | Customer-visible; a wrong triage or bad draft costs agent rework, not safety |
| Quality/reliability target | Match the incumbent frontier-only system's measured pass rate |
| Latency / SLA | Draft ready within 30s of ticket creation |
| Privacy / security | Existing SaaS vendor data-handling terms; nothing new |
| Data & knowledge availability | 14 months of labeled ticket history (triage label + human-edited final response) |
| Tool / action permissions | Read-only (ticket + knowledge-base lookup); no write actions |
| Model candidates | Incumbent frontier API model; one cheaper hosted model as first-tier candidate |
| Owned / rentable compute | None — both tiers are managed APIs |
| Managed APIs | Two vendor endpoints (cheap tier, frontier tier) |
| Budget | Recurring API spend is the line item under negotiation |
| Staffing / time | 1 engineer, ~6 weeks |
| Deployment environment | Existing support-platform webhook integration |
| Observability constraints | Existing telemetry pipeline already logs ticket outcomes |
| Regulatory / compliance | None material |
| Existing evidence | 14 months production logs + existing eval suite (the quality bar) |
| Stakes / consequence tolerance | Tier 2 |

## Archetype & rigor tier

Routes to the cost-reduction-of-an-API-heavy-system archetype, QUICKSTART's D. Tier 2,
by profile fact: the decision is a cost/quality tradeoff on a routing configuration that
is customer-visible but reversible. Nothing safety-related and no regulator pushes it up
to Tier 3, and a real production incumbent — rather than an internal, low-blast-radius
pilot — pushes it past Tier 1.

## The decisive moves

1. **[Oracle analysis](../GLOSSARY.md#oracle-analysis) before any code.** Replay the 14
   months of historical tickets and ask, for each one, whether the cheap tier's output
   would have matched the human-edited final record. Assume a router that always picks
   the tier that succeeds, and you have a bound on the *maximum* saving any router —
   learned or deterministic — could ever achieve. The project proceeds past this step
   only once that ceiling comfortably exceeds what the build would cost.
2. **Deterministic gate is the default, and the profile earns it.** A task-level verifier
   already exists: the triage label is structured, and the response has a schema to
   conform to. Per chapter 08, that makes the default a
   [deterministic gate](../GLOSSARY.md#deterministic-gate) — explicit rules over
   verifiable properties of the output — rather than a learned classifier.
3. **[STOP CONDITION]** on the learned-router side path. A teammate independently
   prototypes a small classifier that answers a tempting question: *will the cheap tier
   succeed on this ticket?* On a first look it edges out the deterministic gate. Before it
   goes anywhere near production it has to clear the
   [leakage audit](../GLOSSARY.md#leakage-audit): hold out an entire group — here a group
   is a ticket template or category — train on the rest, and see whether the classifier
   still works on a group it has never seen; then check it against the score you get from
   group membership alone, the
   [class-identity ceiling](../GLOSSARY.md#class-identity-ceiling). Under
   leave-one-group-out it does not beat that ceiling. What it had learned was which
   template it was looking at, not whether the cheap tier would succeed on this particular
   ticket. **The learned router is refused**, and the deterministic gate from move 2
   remains the production design. The cascade and router literature warns about exactly
   this shape — routers can look strong in-distribution and collapse out of it
   [EXT-ROUTE-001] — and
   [SCENARIO-03](SCENARIO-03_learned-router-leakage.md) works the same failure through in
   full.
4. **[Break-even](../GLOSSARY.md#break-even) computed before rollout.** A gate is not
   free: it costs verification work on every ticket it inspects. Chapter 11's routing
   break-even formula gives the minimum share of traffic the cheap tier must handle
   before the gate's own verification overhead pays for itself. The measured cheap-tier
   share clears that minimum with margin.
5. **One frozen look, not an iterated one.** The cascade's threshold is frozen, then
   measured exactly once, on a fresh slice of live traffic that was never used to tune it,
   against an [MDE](../GLOSSARY.md#mde) declared in advance. That is
   [one-look discipline](../GLOSSARY.md#one-look-discipline). Tuning and then confirming
   on the same data produces a number that is no longer about anything but itself.
6. **[Shadow deployment](../GLOSSARY.md#shadow-deployment), then
   [canary](../GLOSSARY.md#canary-deployment).** The cascade shadows 100% of live traffic
   for two weeks — every decision logged, none of them served — then runs as a small
   canary with rollback armed, before full cutover. That is chapter 10's default promotion
   path.

## What was skipped and why

- **No fine-tuning.** The measured gap here is about routing and economics, which sits at
  ladder rung 6. It is not a capability gap, so the project never has cause to descend
  toward rung 7.
- **No pass^k reliability claims.** Tier 2, not Tier 3.
- **No new eval suite from scratch.** The incumbent frontier-only system's existing eval
  suite is reused as the frozen baseline (chapter 03) rather than rebuilt.
- **No demand ledger / hardware purchase question.** Both tiers are managed APIs, so only
  the break-even formula from chapter 11 applies, not its hardware machinery.
- **The learned router's build time is not recovered.** ~1.5 engineer-weeks went into the
  prototype and its audit. That cost is stated plainly as the price of testing the
  hypothesis, not written off the books.

## Outcome

- Effort: ~6 engineer-weeks total (3 oracle analysis + deterministic gate; 1.5
  learned-router side path + leakage audit; 1.5 shadow/canary rollout).
- The deterministic gate routes ~68% of ticket volume to the cheap tier, against an oracle
  ceiling of ~74%. Most of the available headroom is captured without a learned component
  anywhere in the system.
- Blended API cost per resolved ticket drops from a baseline of $0.090 to $0.041 — a 54%
  reduction — comfortably above the computed break-even share.
- On the frozen confirmation slice, the cascade's pass rate shows no regression outside
  the pre-declared MDE against the frontier-only baseline. That is reported as a bound,
  not oversold as proof of exact equivalence.

## Chapter trail

- [08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) —
  oracle analysis, deterministic gate, leakage audit, escalation
- [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) —
  one-look discipline, MDE, frozen confirmation
- [11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md) —
  routing break-even
- [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) — reused frozen
  baseline eval
- [10. Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md) —
  shadow-then-canary rollout
- [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) — ladder
  rung discipline (never descend past a routing-level fix that suffices)
- See also [SCENARIO-03](SCENARIO-03_learned-router-leakage.md) — the same refusal, worked
  through at length

---

> [Index](../README.md) · [Examples](README.md)
