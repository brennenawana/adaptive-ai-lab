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
corpus: ## Generate the full frozen corpus (96 test / 48 dev / 144 train)
	$(PY) -m scenarios.generator.run --split test  --per-class 8
	$(PY) -m scenarios.generator.run --split dev   --per-class 4
	$(PY) -m scenarios.generator.run --split train --per-class 12

# ---------------------------------------------------------------- evals
# Every arm is resumable: subscription rate limits WILL interrupt a long run, and
# re-running a partial set against a full one is how you get a wrong conclusion.
.PHONY: eval-e2 eval-e4 eval-smoke report
eval-e2: ## E2 — local specialist, fixed evidence
	$(PY) -m evals.runner.run_eval --arm E2 --model-ref local-specialist --split test --resume
eval-e4: ## E4 — frontier ceiling, same evidence contract
	$(PY) -m evals.runner.run_eval --arm E4 --model-ref claude-frontier --split test --resume
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
