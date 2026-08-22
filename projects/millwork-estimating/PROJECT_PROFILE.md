# Project Profile — Millwork Estimating

Draft intake against [`../../playbook/templates/PROJECT_PROFILE.md`](../../playbook/templates/PROJECT_PROFILE.md).
Unknowns are deliberate. Revisit when a real engagement and historical project data
exist.

## 1. Business outcome

Reduce estimator effort and review time while maintaining or improving scope
completeness, quantity/pricing accuracy, and proposal quality. Secondary business
outcome: improve opportunity underwriting when the company may win/structure a
contract and transfer/assign it rather than self-perform.

## 2. Task population & volume

Commercial and residential architectural millwork/cabinetry bids: casework,
counters, wall/ceiling paneling, die walls, trim/moldings, upholstery, finishes,
shop labor, installation, travel, drafting/CNC, exclusions, and proposal production.
Volume and project-size distribution: **unknown**.

## 3. Criticality / failure cost

Consequential financial workflow. Material failures include missed scope, wrong
quantity, wrong material/finish, stale-revision use, labor/install underestimation,
missed qualification/exclusion, arithmetic/rollup error, and unsupported confident
claims. Final human approval reduces per-output blast radius but does not remove the
business consequence of systematic errors.

## 4. Quality / reliability target

**Unknown until historical examples establish a human baseline.** Initial target is
not autonomous estimation; it is bounded assistance that reduces review work without
increasing commercially material errors. Behavioral compatibility with the incumbent
human workflow is likely important at first because outputs feed existing Bluebeam /
Excel / proposal review habits.

## 5. Latency / throughput / SLA

Primarily batch/offline work bounded by bid deadlines rather than interactive latency.
Required turnaround, concurrency, and deadline distribution: **unknown**.

## 6. Privacy / security / data residency

Bid drawings, specifications, pricing, customer/project identities, and contracts may
be confidential or commercially sensitive. Managed-API admissibility and retention
requirements must be resolved with the client before real data is sent to any provider.

## 7. Data & knowledge availability

Currently available:
- one prospect-supplied process description;
- public surrogate bid/drawing/estimate/proposal/job-cost examples;
- general industry standards/guidance.

Needed:
- completed historical project chains;
- actual takeoff/Bid Recap templates;
- price/labor rule sources;
- actual outcomes/corrections where available.

## 8. Tool / action permissions

Discovery: read-only analysis only. Initial prototype should keep document access
read-only and keep proposal/bid writes as drafts requiring explicit human approval.
Autonomous submission is out of scope until separately earned.

## 9. Model candidates

Initial candidate regime: top-tier multimodal managed APIs (Claude/OpenAI/Gemini or
comparable current frontier systems), selected or fixed through project evals rather
than benchmark reputation alone. Strong local multimodal/open models may be tested as
R&D proxies. A local proxy is not promoted merely because it is cheaper.

## 10. Owned compute

Available local inference hardware for this project: **not yet a project dependency / ownership decision unresolved**.

## 11. Rentable compute

Available in principle for occasional local-model or training experiments; exact
provider/security tier and budget: **unknown**.

## 12. Managed APIs

Frontier managed APIs are the default admissible technical hypothesis, subject to the
privacy answer in field 6 and project-specific evaluation.

## 13. Capex budget

No project-specific hardware purchase is required to begin. Any hardware decision
should be justified by a compute-demand ledger and/or measured proxy-transfer value,
not by the existence of this project.

## 14. Recurring budget

**Unknown.** API cost can be treated as a service delivery cost if quality and client
economics justify it; cost optimization follows a measured quality baseline.

## 15. Utilization / growth expectations

**Unknown.** Need bids/month, project size, pages/project, revisions/project, and
expected concurrent estimates.

## 16. Staffing / time

Engineering owner plus AI coding/agent tooling are available. Client estimator and
management availability for domain review, labeling, and acceptance testing:
**unknown and likely the binding scarce resource**.

## 17. Deployment environment

Likely a service/tool layer around the client's existing document workflow rather than
replacement of all incumbent software. Exact cloud/on-prem/desktop integration target:
**unknown**.

## 18. Observability constraints

We want per-run execution-system identity, source-document revision, source citations,
structured outputs, verifier outcomes, human correction severity, review time, and
final disposition. Retention/redaction constraints: **unknown**.

## 19. Regulatory / compliance

Project documents may include prevailing-wage/Davis-Bacon, union, AWI/QCP,
pre-approved-vendor, laboratory-casework, and other contract requirements. Those are
inputs to estimating; whether the AI system itself has additional regulatory/audit
requirements is **unknown**.

## 20. Existing evidence

No trusted AI eval and no automated incumbent system yet. Existing human process is
described in `source/client/Estimating Process.txt` but has not been quantitatively
baselined. The public surrogate corpus is useful for schema/workflow hypotheses only;
it is not a substitute for client ground truth.

## 21. Stakes / consequence tolerance

- **Discovery/research:** Tier 1 while results are internal and reversible.
- **Any decision about client adoption, bid quality, pricing, or production use:**
  Tier 2 (consequential) at minimum, even with mandatory human review.
- Escalate if contractual/privacy/audit constraints make Tier 3 appropriate.
