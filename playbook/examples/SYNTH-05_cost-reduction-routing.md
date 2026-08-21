# SYNTH-05: Cascading a Frontier-API Support System — and Refusing a Learned Router

> [Index](../README.md) · [Examples](README.md)

**Synthetic worked example — all names and numbers invented.**

## Profile summary

"Fernbank Software," a SaaS company, triages and drafts first responses to
customer support tickets using one managed frontier-API model for 100% of
volume. The quality bar is already established — the system has a production
track record and an existing eval suite. The team wants to cut serving cost
without moving that bar.

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

Routes to the cost-reduction-of-an-API-heavy-system archetype. Tier 2, by
profile fact: the decision is a cost/quality tradeoff on a customer-visible
but reversible routing configuration, with no safety or regulatory angle to
push it to Tier 3, and a real production incumbent (not an internal,
low-blast-radius pilot) to push it past Tier 1.

## The decisive moves

1. **[Oracle analysis](../GLOSSARY.md#oracle-analysis) before any code.**
   Replay the 14 months of historical tickets: for each one, would the cheap
   tier's output have matched the human-edited final record? This bounds the
   *maximum* saving any router — learned or deterministic — could ever
   achieve. Only once that ceiling comfortably exceeds the build cost does
   the project proceed past this step.
2. **Deterministic gate is the default, and the profile earns it.** A
   task-level verifier already exists (structured triage label + response
   schema conformance), so per chapter 08 the default is a
   [deterministic gate](../GLOSSARY.md#deterministic-gate) — explicit rules
   over verifiable output signals — not a learned classifier.
3. **[STOP CONDITION]** on the learned-router side path. A teammate
   independently prototypes a small classifier ("will the cheap tier succeed
   on this ticket?") because it edges out the deterministic gate on a first
   look. Before it is allowed anywhere near production it goes through the
   [leakage audit](../GLOSSARY.md#leakage-audit): group-identity ceiling
   comparison and leave-one-group-out validation, where "group" is ticket
   template/category. Result: the classifier does not beat the
   [class-identity ceiling](../GLOSSARY.md#class-identity-ceiling) under
   leave-one-group-out — it learned which template it was looking at, not
   whether the cheap tier would actually succeed on it. **The learned router
   is refused**; the deterministic gate from move 2 remains the production
   design. The cascade/learned-router literature's own caution — routers can
   look strong in-distribution and collapse out-of-distribution
   [EXT-ROUTE-001] — is exactly what the audit catches here, and a fuller
   worked instance of the same failure lives in
   [CASE-003](CASE-003_learned-router-leakage.md).
4. **[Break-even](../GLOSSARY.md#break-even) computed before rollout.** The
   minimum share of traffic the cheap tier must handle for the gate's own
   verification overhead to pay for itself is derived from the routing
   break-even formula (chapter 11); the measured cheap-tier share clears it
   with margin.
5. **One frozen look, not an iterated one.** Per
   [one-look discipline](../GLOSSARY.md#one-look-discipline), the cascade's
   threshold is frozen and then measured exactly once on a fresh slice of
   live traffic that was never used to tune it, against a pre-declared
   [MDE](../GLOSSARY.md#mde) — not tuned-then-confirmed-on-the-same-data.
6. **[Shadow deployment](../GLOSSARY.md#shadow-deployment), then
   [canary](../GLOSSARY.md#canary-deployment).** The cascade shadows 100% of
   live traffic for two weeks (logged, never served), then runs as a small
   canary with rollback armed, before full cutover — chapter 10's default
   promotion path.

## What was skipped and why

- **No fine-tuning.** The measured gap here is routing/economics, sitting at
  ladder rung 6, not a capability gap; the project never has cause to
  descend toward rung 7.
- **No pass^k reliability claims.** Tier 2, not Tier 3.
- **No new eval suite from scratch.** The incumbent frontier-only system's
  existing eval suite is reused as the frozen baseline (chapter 03) rather
  than rebuilt.
- **No demand ledger / hardware purchase question.** Both tiers are managed
  APIs; only the break-even formula from chapter 11 applies, not its
  hardware machinery.
- **The learned router's build time is not recovered.** ~1.5 engineer-weeks
  went into the prototype and its audit. That cost is stated plainly as the
  price of testing the hypothesis, not written off the books.

## Outcome

- Effort: ~6 engineer-weeks total (3 oracle analysis + deterministic gate;
  1.5 learned-router side path + leakage audit; 1.5 shadow/canary rollout).
- The deterministic gate routes ~68% of ticket volume to the cheap tier,
  against an oracle ceiling of ~74% — most of the available headroom is
  captured without a learned component.
- Blended API cost per resolved ticket drops from a baseline of $0.090 to
  $0.041 — a 54% reduction — comfortably above the computed break-even
  share.
- On the frozen confirmation slice, the cascade's pass rate shows no
  regression outside the pre-declared MDE against the frontier-only
  baseline; the result is reported as a bound, not oversold as proof of
  exact equivalence.

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
- See also [CASE-003](CASE-003_learned-router-leakage.md) — the measured
  instance this refusal parallels

---

[Index](../README.md) · [Examples](README.md)
