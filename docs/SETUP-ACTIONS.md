# FIS Setup — Actions That Require You

Everything here needs your hands (root, a browser login, a GUI, or a physical decision).
Once these are done I can build the entire Fintech Integration Sandbox without further input.

Ordered by blocking severity. **A1 is the big one** — it unblocks about 80% of the rest.

---

## A. Blocking — I cannot proceed past repo scaffolding

### A1. Grant passwordless sudo in WSL — ✅ **DONE** (applied 2026-08-15)

`/etc/sudoers.d/wall-nopasswd` is installed (`0440 root:root`), validated with
`visudo -c` before and after install, and verified: `sudo -n true` succeeds as `wall`.

**Why the manual attempt failed.** Typing `sudo` at a PowerShell prompt runs
`C:\WINDOWS\system32\sudo.exe` — Windows 11's own Sudo, which elevates *Windows*
processes and has no connection to WSL. Running PowerShell as Administrator doesn't
help either: Windows admin and Linux root are separate permission systems. Linux
commands must run inside the Ubuntu shell, and Linux `sudo` wants the password set
when Ubuntu was first installed — not the Windows password.

The route that avoids the password entirely, and what was actually used:
```powershell
wsl -d Ubuntu-24.04 -u root -- <command>     # root in WSL, no password, no elevation
```

**To undo:** `wsl -d Ubuntu-24.04 -u root -- rm /etc/sudoers.d/wall-nopasswd`

---

### A2. Create a long-lived Claude subscription token  ⏱️ ~1 minute

You chose to drive the frontier tier through your Claude subscription instead of an API
key. That works (validated below), but the model gateway needs auth that doesn't expire
mid-eval-run and doesn't pop a browser.

```bash
claude setup-token
```

This is the officially supported path for programmatic subscription auth. It prints a
long-lived token. **Paste it into `.env` in the repo when I create it** (I'll gitignore
`.env`), or tell me and I'll write a placeholder you fill in.

Without this, a token expiry midway through a 200-case eval run stops the run and needs
you to re-login — which defeats "no input needed".

---

### A3. Install and log in to Codex CLI  ⏱️ ~3 minutes

You said you have a ChatGPT login too. The binary isn't installed on this machine — I
found `C:\Users\4kind-work\.codex\config.toml` (it only holds a Unity MCP entry) but no
`codex` executable on Windows or in WSL, and no `auth.json`.

In **WSL**:
```bash
npm install -g @openai/codex     # or: brew install codex
codex login                      # opens a browser; uses your ChatGPT plan
codex --version
```

Then confirm non-interactive mode answers:
```bash
codex exec "Reply with exactly: OK"
```

**This one is optional.** It buys a second frontier provider so the experiment matrix
can compare ceilings across vendors rather than measuring one model's ceiling. If you'd
rather skip it, say so and I'll build the gateway with the Codex adapter stubbed behind
the same interface — nothing else is blocked.

---

### A4. Free up GPU headroom before eval and training runs  ⏱️ ongoing

`nvidia-smi` currently shows **~5.0 GB of 16 GB VRAM already consumed** by desktop apps:
OBS, Unity Editor + Unity Hub, Warudo (×2 processes), Discord, Chrome, the NVIDIA
overlay, and Parsec.

That leaves ~11 GB. The guide's profiles want:

| Profile | VRAM target | Reachable today? |
|---|---|---|
| Balanced AI (4B–8B local model) | 8–13 GB | ✅ yes |
| AI experiment (8B–14B, eval batches) | 13–15 GB | ❌ needs apps closed |
| Training (QLoRA) | as much of 16 GB as possible | ❌ needs apps closed |

Only you can close these. Nothing breaks if you don't — I'll simply cap the local model
at the 4B–8B class, which is the guide's recommended starting envelope anyway. But when
we reach **E7 (QLoRA)** in week 6, the training run will need the GPU mostly to itself.

No action needed now. Just be ready to close OBS/Unity/Warudo when I flag a training run.

---

## B. Quick confirmations (30 seconds total, non-blocking)

### B1. Git identity in WSL is unset
```bash
git config --global user.name  "Your Name"
git config --global user.email "brennen@xargz.com"
```

### B2. Do you want a GitHub remote?
`gh` is installed on Windows and authenticated. Tell me one of:
- **Local only** — I'll `git init` and commit locally (default if you don't answer)
- **Private GitHub repo** — I'll create `fintech-integration-sandbox` and push

Note the clean-room rule from the guide: this repo must contain **no** Spidr source,
schemas, prompts, credentials, or customer data. Everything synthetic and independently
designed. A private repo is fine; a public one is also fine given that constraint, but
private is the safer default.

---

## C. Decisions you already made (recorded, no action needed)

| Decision | Choice |
|---|---|
| Package installs | Passwordless sudo → I install everything |
| Container runtime | Docker Engine natively in WSL (free, systemd already on) |
| Repo location | WSL: `~/fintech-integration-sandbox` |
| Frontier tier | Subscription CLIs (Claude Code + Codex), **no API keys** |

---

## D. What I do once A1 lands — no further input from you

1. `apt install` Docker Engine + Compose, pgvector, jq, cmake, build deps; add you to the
   `docker` group; `systemctl enable --now docker`
2. Scaffold `~/fintech-integration-sandbox` to the guide's layout, copy these three HTML
   design docs into `docs/`, `git init`
3. Write the six foundational schemas (task, specialist, tool, trajectory, model manifest,
   eval) — the guide's "first thing I would implement"
4. Stand up Postgres + pgvector + NATS via Compose on **non-conflicting ports** (your
   existing `thewall` Postgres on 5432 and Redis on 6379 stay untouched; FIS gets its own
   instance on 5433)
5. Pull a 4–8B instruct model with real tool-calling support and serve it OpenAI-compatible
   via your existing CUDA llama.cpp build on a free port (8080 stays reserved for Bonsai,
   8081 for your Qwen3.8-27B server)
6. Build the model gateway with three adapters behind one contract: local llama.cpp,
   Claude-subscription CLI, Codex CLI
7. Build the 9 FIS services, the seeded scenario generator with hidden ground truth, the
   read-only tool broker, the deterministic verifier, the trajectory store, and the eval runner
8. Run E0→E3, then E4/E5 once A2 is done

---

## Appendix — Why the subscription-CLI frontier tier works, and what it costs you

I validated this end-to-end rather than assuming it. Findings:

**It works.** `claude -p --output-format json` returns the answer plus full telemetry:
token counts, per-model cost, `duration_api_ms`, `ttft_ms`, `session_id`, `stop_reason`.
`--json-schema` enforces our investigator output contract and returns a validated
`structured_output` object — the frontier-tier equivalent of llama.cpp's GBNF grammar.
So the trajectory schema loses **nothing**.

**But the default invocation is unusable for a controlled experiment.** A bare
`claude -p "Reply with exactly: OK"` consumed **33,633 input tokens** and reported
**$0.337** — because it loads the whole Claude Code agent harness (system prompt, tool
schemas, CLAUDE.md, skill listings). That is measuring Claude Code, not the model.

**The fix, validated:**
```bash
claude -p "<evidence bundle>" \
  --model opus \
  --system-prompt "<FIS investigator contract>" \
  --tools "" --disable-slash-commands --strict-mcp-config \
  --safe-mode --no-session-persistence \
  --json-schema '<investigator output schema>' \
  --output-format json --max-budget-usd 0.50
```
Result: **685** input tokens instead of 33,633, **$0.0356** instead of $0.337, correct
answer, schema-valid output. That is a legitimate controlled comparison against the local
model — same evidence, same contract, no tool asymmetry.

> Do **not** use `--bare`. It looks like the right flag but its help text says Anthropic
> auth becomes "strictly `ANTHROPIC_API_KEY` or apiKeyHelper — OAuth and keychain are
> never read", which defeats subscription auth. `--safe-mode` is the correct flag: it
> strips CLAUDE.md, skills, plugins, hooks and MCP while leaving auth working normally.

### Considerations you asked about

1. **Cost-per-successful-case becomes a shadow metric.** Your marginal cost on a
   subscription is effectively zero, so if the KPI used real spend the cloud tier would
   look free and "intelligence density" would be meaningless. I'll record two columns:
   the CLI's reported `total_cost_usd`, and a **reference list-price cost** recomputed
   from token counts (Opus 5 $5/$25 per MTok, Sonnet 5 $3/$15, Haiku 4.5 $1/$5). The
   KPI uses the reference figure so local-vs-cloud economics stay honest.

2. **Latency is contaminated by process startup.** Wall clock 4.9 s vs `duration_ms`
   1.7 s on the trivial call — roughly 2.2 s of Node/CLI startup per invocation. Against
   a local llama.cpp HTTP endpoint that's a systematic bias. I'll record `duration_api_ms`
   and wall-clock separately and report both, so P50/P95 comparisons aren't misleading.

3. **A second model shows up in your telemetry.** Both runs invoked
   `claude-haiku-4-5` alongside the main model (~$0.0006) — a Claude Code internal
   side-task. I'll filter `modelUsage` to the canonical model for per-case attribution
   so it doesn't pollute the numbers.

4. **Tool-strategy vs reasoning.** With `--tools ""` the frontier model can't call FIS
   tools, so E4 measures **reasoning given fixed evidence** — which is exactly the
   guide's "replay the same evidence to a stronger model" design. If we also want to
   measure frontier *tool selection*, I can expose the FIS tool broker as an MCP server
   and pass it via `--mcp-config`, giving the frontier tier the same tools. I'd suggest
   doing that as a separate experiment arm rather than conflating the two.

5. **Rate limits, not cost, are the real constraint.** Subscription plans have rolling
   windows. A 200-case eval across several experiment arms will hit them. I'll build the
   eval runner **checkpointed and resumable** with low concurrency and exponential
   backoff, so a rate-limit pause costs you a wait, not a lost run. `--max-budget-usd`
   goes on every call as a runaway guard.

6. **No temperature or seed control.** The CLI exposes `--effort` but not sampling
   params, so frontier-tier runs aren't bit-reproducible. Local llama.cpp runs are. I'll
   note this in the experiment log rather than pretend the two are equally reproducible.

7. **This is a supported path, not a workaround.** `-p`/`--print` is the documented
   non-interactive mode and `claude setup-token` exists specifically for subscription-based
   programmatic auth. The practical ceiling is your plan's rate limits.

8. **The gateway keeps an API-key adapter behind the same interface.** If you ever want
   bit-reproducible frontier runs or higher throughput, dropping in a key is a config
   change, not a rewrite — which is exactly what the Canonical Architecture demands:
   *"Nothing in the business logic should care where the model physically lives."*
