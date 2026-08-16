.DEFAULT_GOAL := help
SHELL := /bin/bash
PY := .venv/bin/python
COMPOSE := sudo -n docker compose -f infra/compose.yaml
PSQL := sudo -n docker exec -i fis-postgres psql -U fis -d fis

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
	  awk -F':.*?## ' '{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- infra
.PHONY: up-core down-core up-full up-artifacts ps logs
up-core: ## Start Postgres+pgvector (5433) and NATS JetStream (4222)
	$(COMPOSE) --profile core up -d
down-core: ## Stop the core profile
	$(COMPOSE) --profile core down
up-full: ## Core + everything else
	$(COMPOSE) --profile full up -d
up-artifacts: ## Add MinIO (only needed once trajectories store payloads)
	$(COMPOSE) --profile artifacts up -d
ps: ## Container status
	sudo -n docker ps --filter name=fis- --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
logs: ## Tail core logs
	$(COMPOSE) --profile core logs -f --tail=50

.PHONY: migrate
migrate: ## Apply all migrations in order (idempotent except role creation)
	@for f in infra/migrations/*.sql; do \
	  echo "--- $$f"; $(PSQL) -v ON_ERROR_STOP=1 -q < $$f || true; \
	done

# ---------------------------------------------------------------- model
.PHONY: serve-local stop-local model-health
serve-local: ## Start the local specialist on 8082 (8080/8081 stay free)
	# Invoked via `bash` rather than executed directly: editing this repo through
	# a Windows UNC path drops the Unix exec bit, which made this fail with a bare
	# "Permission denied". Calling the interpreter makes the mode irrelevant.
	bash ./infra/serve-local-model.sh
stop-local: ## Stop it
	@pkill -f 'llama-serve[r] .*--port 8082' && echo stopped || echo "not running"
model-health: ## Is the local endpoint up?
	@curl -s --max-time 3 http://127.0.0.1:8082/health || echo "DOWN"

# ---------------------------------------------------------------- routing gateway (R1+)
# NeMo Switchyard sits BENEATH the FIS gateway contract: an OpenAI-compatible hop
# on 4000 in front of the same llama.cpp on 8082. It owns transport, backend
# selection inside a profile, and per-request stats. It does not own scenario truth,
# evidence rules, scoring, or the trajectory record — see infra/switchyard/README.md.
.PHONY: serve-switchyard stop-switchyard switchyard-health switchyard-stats
serve-switchyard: ## Start Switchyard on 4000 with infra/switchyard/routes.yaml (passthrough to 8082)
	bash ./infra/switchyard/serve.sh
stop-switchyard: ## Stop it
	@pkill -f 'switchyard serv[e] .*--port 4000' && echo stopped || echo "not running"
switchyard-health: ## Listener up, and which route ids it serves
	@curl -s --max-time 3 http://127.0.0.1:4000/health || echo "DOWN"; echo
	@curl -s --max-time 3 http://127.0.0.1:4000/v1/models | $(PY) -c 'import sys,json; print("routes:", [m["id"] for m in json.load(sys.stdin)["data"]])' 2>/dev/null || true
switchyard-stats: ## Gateway-side per-model counters (requests, tokens, latency)
	@curl -s --max-time 3 http://127.0.0.1:4000/v1/stats | $(PY) -m json.tool

# ---------------------------------------------------------------- data
.PHONY: scenarios scenarios-dry corpus
scenarios-dry: ## Build scenarios in memory, write nothing
	$(PY) -m scenarios.generator.run --dry-run --per-class 1
corpus: ## Regenerate the full frozen corpus (96 test / 48 dev / 144 train)
	# --reset on the FIRST split only: it truncates the scenario tables and purges
	# the streams, so the corpus is replaced rather than added to. Regenerating on
	# top of an existing corpus collides primary keys, and a surviving dedupe ledger
	# would make S01's first delivery look like a duplicate.
	#
	# learning.* is deliberately NOT truncated — that is where prior run scores live.
	$(PY) -m scenarios.generator.run --split test  --per-class 8 --reset
	$(PY) -m scenarios.generator.run --split dev   --per-class 4
	$(PY) -m scenarios.generator.run --split train --per-class 12

# ---------------------------------------------------------------- evals
# Every arm is resumable: subscription rate limits WILL interrupt a long run, and
# re-running a partial set against a full one is how you get a wrong conclusion.
# ---------------------------------------------------------------- E6
# Variant SELECTION happens on dev, never on test.
#
# E6 compares several prompts and keeps the best. Doing that on the test split is
# tuning against the test set by definition — the guide's own rule — and it would
# quietly convert the frozen suite into a training signal. Dev exists for this.
# `eval-e6-confirm` then runs the chosen variant on test exactly once.
.PHONY: eval-e6-dev eval-e6-confirm
eval-e6-dev: ## E6 — score all three prompt variants on the DEV split
	$(PY) -m evals.runner.run_eval --arm E6 --model-ref local-specialist --split dev \
	  --prompt baseline              --run-id E6-A-baseline-dev  --resume
	$(PY) -m evals.runner.run_eval --arm E6 --model-ref local-specialist --split dev \
	  --prompt cause_action_table    --run-id E6-B-table-dev     --resume
	$(PY) -m evals.runner.run_eval --arm E6 --model-ref local-specialist --split dev \
	  --prompt cause_action_directed --run-id E6-C-directed-dev  --resume
.PHONY: eval-e6b-dev
eval-e6b-dev: ## E6b — citation-recovery 2x2 on DEV (C already run, is the control)
	# E6 raised diagnosis but dropped evidence recall to 61.1%, which is now the
	# binding constraint. Two factors: WHERE the citation rules sit (recency) and
	# WHAT they ask for (eliminative evidence). E6-C-directed-dev is cell 1.
	$(PY) -m evals.runner.run_eval --arm E6b --model-ref local-specialist --split dev \
	  --prompt cite_last             --run-id E6b-E-citelast-dev   --resume
	$(PY) -m evals.runner.run_eval --arm E6b --model-ref local-specialist --split dev \
	  --prompt cite_eliminative      --run-id E6b-F-elim-dev       --resume
	$(PY) -m evals.runner.run_eval --arm E6b --model-ref local-specialist --split dev \
	  --prompt cite_last_eliminative --run-id E6b-G-both-dev       --resume

eval-e6-confirm: ## E6 — run the winning variant on TEST once (set PROMPT=...)
	@test -n "$(PROMPT)" || { echo "usage: make eval-e6-confirm PROMPT=cause_action_directed"; exit 1; }
	$(PY) -m evals.runner.run_eval --arm E6 --model-ref local-specialist --split test \
	  --prompt $(PROMPT) --run-id E6-$(PROMPT)-96 --resume

# ---------------------------------------------------------------- R-series (routing)
# R1 is a zero-semantic-change TRANSPORT experiment: same prompt (the frozen E6
# winner), same evidence, same model, same decoding, same grammar, same scorer —
# only the path differs. The direct arm is re-run alongside rather than borrowed
# from E6-C-directed-dev so that direct-vs-direct measures the nondeterminism floor
# under the SAME code, and direct-vs-switchyard is judged against that floor.
.PHONY: eval-r1-dev r1-compare
eval-r1-dev: ## R1 — frozen weak baseline on DEV, direct path then Switchyard passthrough
	$(PY) -m evals.runner.run_eval --arm R1 --model-ref local-specialist --split dev \
	  --prompt cause_action_directed --run-id R1-direct-dev --resume
	$(PY) -m evals.runner.run_eval --arm R1 --model-ref local-specialist-switchyard --split dev \
	  --prompt cause_action_directed --run-id R1-switchyard-dev --resume
r1-compare: ## R1 — per-scenario equivalence report (direct vs Switchyard, plus direct vs E6-C control)
	$(PY) scripts/compare_routes.py --a R1-direct-dev --b R1-switchyard-dev
	$(PY) scripts/compare_routes.py --a E6-C-directed-dev --b R1-direct-dev

# R2 pairs the frozen weak arm with the strong arm ON DEV. The oracle map is a
# selection tool; the script refuses the test split without --allow-test.
.PHONY: eval-e4-dev routing-oracle
eval-e4-dev: ## Strong arm on DEV (needed once for R2 pairing)
	$(PY) -m evals.runner.run_eval --arm E4 --model-ref claude-frontier --split dev \
	  --run-id E4-v2-dev --resume
routing-oracle: ## R2 — paired weak/strong opportunity map on DEV
	$(PY) scripts/routing_oracle.py --weak E6-C-directed-dev --strong E4-v2-dev --split dev

.PHONY: reachability
reachability: ## Can the fixed-evidence plan reach every case's required evidence?
	# Run after `make corpus`, before trusting any score. A class capped below the
	# recall threshold is a harness bug that reads exactly like model weakness.
	$(PY) scripts/evidence_reachability.py --split test

.PHONY: eval-e2 eval-e4 eval-smoke report
# run-ids carry the suite version. `E2-local-96` is the PRE-migration reference and
# must stay reachable and unconfusable: the corpus it scored no longer exists, so a
# run id that could be mistaken for it would silently invite a comparison across the
# one line in this project's history that cannot be compared across.
eval-e2: ## E2 — local specialist, fixed evidence
	$(PY) -m evals.runner.run_eval --arm E2 --model-ref local-specialist --split test \
	  --run-id E2-v2-96 --resume
eval-e4: ## E4 — frontier ceiling, same evidence contract
	$(PY) -m evals.runner.run_eval --arm E4 --model-ref claude-frontier --split test \
	  --run-id E4-v2-96 --resume
eval-smoke: ## Fast sanity run (3 cases, local)
	$(PY) -m evals.runner.run_eval --arm SMOKE --model-ref local-specialist --split dev --limit 3
report: ## Cross-arm comparison table
	$(PY) -m evals.runner.compare

# ---------------------------------------------------------------- dev
.PHONY: test lint gateway-smoke
test: ## Unit tests
	$(PY) -m pytest tests/ -q
lint: ## Ruff
	.venv/bin/ruff check . || true
gateway-smoke: ## One request through every registered model
	$(PY) scripts/gateway_smoke.py
