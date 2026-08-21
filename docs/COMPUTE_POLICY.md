# Compute Policy

> STATUS: CURRENT / NORMATIVE at the lab level. Extracted 2026-08-21 from
> `AI_SYSTEMS_LAB_MASTER_PLAN.md` §8 (now `projects/fis/PROJECT_PLAN.md`) during
> the repository restructuring. One policy and one demand ledger per lab, not per
> project (`playbook/templates/COMPUTE_DEMAND_LEDGER.md` doctrine). The demand
> instrument is `GPU_HOURS_LEDGER.md` in this directory. Per-project operational
> facts (owned nodes, ports, runtime workarounds) live in each project's plan —
> for FIS: `projects/fis/PROJECT_PLAN.md` §8.

Adopted from the adversarially-corrected hardware study
(`../research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md` §3.5), verified
against measured lab demand; the buy-nothing verdict re-affirmed by M0's rented
benchmark.

- **Rent, don't buy, now.** Second node per multi-arm milestone (~$5–12,
  Secure-tier 3090/A6000 class; captures the full measured 8.8 h overlap saving)
  with pre-registered cross-node arm placement. Training jobs rented ($5–30 each).
- **The $4 benchmark first**: pinned artifact + pinned build on rented 3090 and
  5090 — measures the only number the purchase decision turns on. (Executed in M0.)
- **GPU-hours/month ledger** (`GPU_HOURS_LEDGER.md`, opened by M0, append-only).
  **Purchase trigger** (pre-committed): 3 consecutive months > ~$150/mo rented
  spend, or a committed always-on client serving tier. On trigger: **one**
  benchmark-chosen GPU (default used 3090) on a minimal native-Linux host
  (~$2,050–2,700), with a thermal/decode acceptance test before it becomes an
  execution system.
- **Bandwidth lever** (only compresses the dominant chain): 5090-class, post-R7 and
  post-bubble — buy at ≤~$2.5K street or rent at $0.99/hr; never at ~$4,900
  mid-crunch.
- **DGX Spark** becomes correct only under the pre-registered conditions (any two
  of: capacity-bound MoE/agent residency; single-box CUDA 70B QLoRA/long-context
  need; price ≤~$3.5K; power/acoustics dominate; client targets Spark). Track
  quarterly.
- **Capacity** (48 GB pooling / 128 GB) and cloud training: rent per session until
  the ledger proves sustained demand. **Re-verify all prices at order time** — the
  2026 memory crunch makes every recorded price a floor with weeks of shelf life.
