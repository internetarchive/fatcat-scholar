
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c
TODAY ?= $(shell date --iso --utc)

.PHONY: help
help: ## Print info about all commands
	@echo "Commands:"
	@echo
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[01;32m%-20s\033[0m %s\n", $$1, $$2}'

.venv:
	python3 -mvenv .venv
	.venv/bin/pip install -e .[dev]

.PHONY: dep
dep: .venv ## Install dependencies using pip install -e to .venv

.PHONY: lint
lint: dep ## Run ruff check and mypy
	.venv/bin/ruff check src/scholar/ tests/
	.venv/bin/mypy src/scholar/ tests/ --ignore-missing-imports --disable-error-code call-arg --disable-error-code arg-type --disable-error-code assignment

.PHONY: pytype
pytype: dep ## Run slow pytype type check (not part of dev deps)
	.venv/bin/pytype src/scholar/

.PHONY: fmt
fmt: dep ## Run ruff format on all source code
	.venv/bin/ruff format src/scholar tests/

.PHONY: test
test: dep ## Run all tests and lints
	PIPENV_DONT_LOAD_ENV=1 ENV_FOR_DYNACONF=test .venv/bin/pytest

.PHONY: coverage
coverage: dep ## Run all tests with coverage
	PIPENV_DONT_LOAD_ENV=1 ENV_FOR_DYNACONF=test .venv/bin/pytest --cov --cov-report=term --cov-report=html

.PHONY: serve
serve: dep ## Run web service locally, with reloading
	ENV_FOR_DYNACONF=development .venv/bin/uvicorn scholar.web:app --reload --port 9819

.PHONY: serve-qa
serve-qa: dep ## Run web service locally, with reloading, but point search queries to QA search index
	ENV_FOR_DYNACONF=development-qa .venv/bin/uvicorn scholar.web:app --reload --port 9819

.PHONY: serve-gunicorn
serve-gunicorn: dep ## Run web service under gunicorn
	.venv/bin/gunicorn scholar.web:app -b 127.0.0.1:9819 -w 4 -k uvicorn.workers.UvicornWorker

.PHONY: fetch-works
fetch-works: dep ## Fetches some works from any release .json in the data dir
	cat data/release_*.json | jq . -c | .venv/bin/python -m scholar.work_pipeline run_releases | pv -l > data/work_intermediate.json

.PHONY: fetch-sim
fetch-sim: dep ## Fetches some (not all) SIM pages
	.venv/bin/python -m scholar.sim_pipeline run_issue_db --limit 500 | pv -l > data/sim_intermediate.json

.PHONY: dev-index
dev-index: dep ## Delete/Create DEV elasticsearch fulltext index locally
	http delete ":9200/dev_scholar_fulltext_v01" && true
	http put ":9200/dev_scholar_fulltext_v01?include_type_name=true" < schema/scholar_fulltext.v01.json
	http put ":9200/dev_scholar_fulltext_v01/_alias/dev_scholar_fulltext"
	cat data/sim_intermediate.json data/work_intermediate.json | .venv/bin/python -m scholar.transform run_transform | esbulk -verbose -size 200 -id key -w 4 -index dev_scholar_fulltext_v01 -type _doc

.PHONY: extract-i18n
extract-i18n:  dep ## Re-extract translation source strings (for weblate)
	.venv/bin/pybabel extract -F extra/i18n/babel.cfg -o extra/i18n/web_interface.pot src/scholar/

.PHONY: recompile-i18n
recompile-i18n: dep extract-i18n  ## Re-extract and compile all translation files (bypass weblate)
	.venv/bin/pybabel update -i extra/i18n/web_interface.pot -d src/scholar/translations
	.venv/bin/pybabel compile -d src/scholar/translations

data/$(TODAY)/sim_collections.tsv: dep
	mkdir -p data/$(TODAY)
	.venv/bin/ia search 'collection:periodicals collection:sim_microfilm mediatype:collection (pub_type:"Scholarly Journals" OR pub_type:"Historical Journals" OR pub_type:"Law Journals")' --itemlist | rg "^pub_" | pv -l > $@.wip
	mv $@.wip $@

data/$(TODAY)/sim_items.tsv: dep
	mkdir -p data/$(TODAY)
	.venv/bin/ia search 'collection:periodicals collection:sim_microfilm mediatype:texts !noindex:true (pub_type:"Scholarly Journals" OR pub_type:"Historical Journals" OR pub_type:"Law Journals")' --itemlist | rg "^sim_" | pv -l > $@.wip
	mv $@.wip $@

data/$(TODAY)/sim_collections.json: data/$(TODAY)/sim_collections.tsv dep
	cat data/$(TODAY)/sim_collections.tsv | .venv/bin/parallel -j20 ia metadata {} | jq . -c | pv -l > $@.wip
	mv $@.wip $@

data/$(TODAY)/sim_items.json: data/$(TODAY)/sim_items.tsv dep
	cat data/$(TODAY)/sim_items.tsv | .venv/bin/parallel -j20 ia metadata {} | jq -c 'del(.histograms, .rotations)' | pv -l > $@.wip
	mv $@.wip $@

data/$(TODAY)/issue_db.sqlite: data/$(TODAY)/sim_collections.json data/$(TODAY)/sim_items.json dep
	.venv/bin/python -m scholar.issue_db --db-file $@.wip init_db
	cat data/$(TODAY)/sim_collections.json | pv -l | .venv/bin/python -m scholar.issue_db --db-file $@.wip load_pubs -
	cat data/$(TODAY)/sim_items.json | pv -l | .venv/bin/python -m scholar.issue_db --db-file $@.wip load_issues -
	.venv/bin/python -m scholar.issue_db --db-file $@.wip load_counts
	mv $@.wip $@

data/issue_db.sqlite: data/$(TODAY)/issue_db.sqlite
	cp data/$(TODAY)/issue_db.sqlite data/issue_db.sqlite

.PHONY: issue-db
issue-db: data/issue_db.sqlite  ## Build SIM issue database with today's metadata, then move to default location

.PHONY: freeze
freeze: dep
	.venv/bin/pip-compile --generate-hashes -o requirements.txt
	.venv/bin/pip-compile --generate-hashes --extra dev -o dev.requirements.txt
	.venv/bin/pip-compile --generate-hashes --extra ci -o ci.requirements.txt

.PHONY: audit
audit: dep
	.venv/bin/pip-audit
