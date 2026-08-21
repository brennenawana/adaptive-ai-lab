# Adaptive AI Lab — thin delegator. The FIS operations console is
# projects/fis/Makefile (run `make -C projects/fis help` or work from that
# directory); this file only wires the lab-level entry points together.
.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help test playbook-check fis-%

help: ## lab-level targets (FIS targets: make -C projects/fis help)
	@grep -E '^[a-zA-Z0-9_%-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'
	@echo "  fis-<target>       delegate <target> to projects/fis (e.g. make fis-ps)"

test: ## full FIS test suite + provenance verifiers (delegates to projects/fis)
	$(MAKE) -C projects/fis test
	cd projects/fis && .venv/bin/python scripts/r6_registry.py verify
	cd projects/fis && .venv/bin/python scripts/test_look_ledger.py verify

playbook-check: ## the playbook's 7-check release validator
	python3 playbook/tools/check_playbook.py

fis-%: ## delegate any target to projects/fis (make fis-ps, make fis-corpus-check, ...)
	$(MAKE) -C projects/fis $*
