# Adaptive AI Systems Playbook — build and validation entry points.
.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help check playbook-check site site-build site-preview site-deps

help: ## available targets
	@grep -E '^[a-zA-Z0-9_%-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

check: playbook-check site-build ## everything: validator + production build with link checking

playbook-check: ## the playbook's release validator (inventory, portability, links, ...)
	python3 playbook/tools/check_playbook.py

site-deps:
	@cd site && { [ -d node_modules ] && [ package-lock.json -ot node_modules ]; } || npm install

site: site-deps ## local dev server with hot reload (http://localhost:4321)
	cd site && npm run dev

site-build: site-deps ## production build (site/dist/ + search index + link validation)
	cd site && npm run build

site-preview: ## serve the last production build locally
	cd site && npm run preview
