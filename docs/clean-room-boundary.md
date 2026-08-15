# Clean-Room Boundary

FIS is a learning and demonstration artifact. Its value depends on being provably
independent of any employer system. This document is the standing rule and the
answer to "how do I know none of your client's material is in here."

---

## The rule

**Nothing from Spidr — or any employer or client system — enters this repository.**

Not source code. Not API schemas. Not prompts. Not architecture documents. Not
credentials. Not customer data. Not runbooks. Not implementation details. Not
"inspired by" reconstructions of a real internal service.

Every service, field, workflow, identifier, test fixture and vendor simulator here
is designed independently from the public shape of the fintech domain.

---

## Why the domain still resembles real fintech

Because the *category* of problem is public knowledge. Duplicate webhook delivery,
idempotency keys, settlement/ledger reconciliation, KYC holds and authorization
reversals are described in the public documentation of every payment processor and
in standard industry literature. Modelling them is not disclosure.

The line is between **shape** and **specifics**:

| Legitimate | Prohibited |
|---|---|
| "Processors deliver webhooks that can duplicate" | Any specific employer's webhook payload schema |
| "Reconciliation compares processor and ledger amounts" | Any specific employer's reconciliation logic |
| "KYC vendors return status and reason codes" | Any specific vendor contract or field set |
| A fictional vendor named `veriscope` | A real vendor's actual response format |

If a design decision here can be traced to something learned *inside* an employer
rather than from public material, it does not belong in this repo.

---

## Synthetic data guarantees

Enforced by construction in `scenarios/generator/world.py`:

- **Names** are drawn from a deliberately fictional word list (`Marlow Ashgrove`,
  `Vesper Quillon`). No real-person name generator, no scraped list.
- **Dates of birth** are synthetic and structurally obvious.
- **Card numbers do not exist.** The `pan_token` field holds a placeholder token
  (`tok_<digits>`). There is no PAN field anywhere in the schema, so a real card
  number has nowhere to be stored even by mistake.
- **No SSNs, national IDs, addresses, phone numbers or emails** exist in the model.
- **Money is synthetic**, in minor units, in a fictional bank's ledger.
- **Vendors are invented**: `veriscope`, `trustloop`, `idmirror`.
- The bank is **Northstar Bank**, which does not exist.

Everything is deterministic from a seed, so the entire corpus can be regenerated
from nothing but the code — there is no imported dataset to audit.

---

## What may leave this machine

The frontier tier sends evidence bundles to a hosted model. That is acceptable
**only** because every byte of it is synthetic and generated locally.

The gateway carries a `DataPolicy` on every request and `ModelAdapter._check_policy`
refuses to send a `LOCAL_ONLY` payload to a non-local provider. Today nothing is
marked `LOCAL_ONLY` — the check exists so that pointing this platform at real data
later is a configuration change rather than an audit.

**If this codebase is ever aimed at real company data, that is a different system**
and needs its own review. The reusable asset is the method, not this fictional domain.

---

## Safety and scope disclaimers

- FIS is **not** an AML/KYC decision system and must not be described as one.
- It does **not** constitute compliance advice.
- All AI tools are **read-only**. There is no code path that moves money, approves
  a customer, or writes to a system of record. "Actions" are recommendation codes
  an operator would execute elsewhere.
- The `fis_tools` database role is read-only at the connection level
  (`default_transaction_read_only`), so even a defective handler cannot write.

---

## Reusable vs domain-specific

The point of the clean-room split is that the valuable half transfers to a real
client engagement unchanged, while the fintech half is disposable.

| Reusable platform asset | Replaced per client |
|---|---|
| Model gateway + adapters | Approved providers, model registry |
| Trajectory schema | Client task and outcome metadata |
| Tool broker interface | Client APIs and databases |
| Verifier framework | Client-specific deterministic checks |
| Eval runner + scorers | Client gold cases and business outcomes |
| Failure taxonomy | Client task ontology |
| Cost/latency accounting | Client economics and SLAs |
| **The fintech domain itself** | **Discarded entirely** |

---

## If in doubt

Ask: *"Could I have written this having never worked at the employer, using only
public documentation?"*

If no, it does not go in.
