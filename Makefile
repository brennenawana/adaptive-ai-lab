.DEFAULT_GOAL := help
SHELL := /bin/bash
PY := .venv/bin/python
COMPOSE := sudo -n docker compose -f infra/compose.yaml
PSQL := sudo -n docker exec -i fis-postgres psql -U fis -d fis

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
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
eval-e6-confirm: ## E6 — run the winning variant on TEST once (set PROMPT=...)
	@test -n "$(PROMPT)" || { echo "usage: make eval-e6-confirm PROMPT=cause_action_directed"; exit 1; }
	$(PY) -m evals.runner.run_eval --arm E6 --model-ref local-specialist --split test \
	  --prompt $(PROMPT) --run-id E6-$(PROMPT)-96 --resume

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
