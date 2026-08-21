# Adaptive AI Lab — thin delegator. The FIS operations console is
# projects/fis/Makefile (run `make -C projects/fis help` or work from that
# directory); this file only wires the lab-level entry points together.
.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help test playbook-check site site-build site-preview site-deps fis-%

help: ## lab-level targets (FIS targets: make -C projects/fis help)
	@grep -E '^[a-zA-Z0-9_%-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'
	@echo "  fis-<target>       delegate <target> to projects/fis (e.g. make fis-ps)"

test: ## full FIS test suite + provenance verifiers (delegates to projects/fis)
	$(MAKE) -C projects/fis test
	cd projects/fis && .venv/bin/python scripts/r6_registry.py verify
	cd projects/fis && .venv/bin/python scripts/test_look_ledger.py verify

playbook-check: ## the playbook's 7-check release validator
	python3 playbook/tools/check_playbook.py

site-deps:
	@cd site && { [ -d node_modules ] && [ package-lock.json -ot node_modules ]; } || npm install

site: site-deps ## playbook website, local dev server with hot reload (http://localhost:4321)
	cd site && npm run dev

site-build: site-deps ## playbook website, reproducible production build (site/dist/ + search index + link validation)
	cd site && npm run build

site-preview: ## serve the last production build locally
	cd site && npm run preview

fis-%: ## delegate any target to projects/fis (make fis-ps, make fis-corpus-check, ...)
	$(MAKE) -C projects/fis $*
