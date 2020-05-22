
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

.PHONY: help
help: ## Print info about all commands
	@echo "Commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[01;32m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: test
test: ## Run all tests and lints
	ENV_FOR_DYNACONF=test pipenv run pytest
	pipenv run mypy fatcat_scholar/*.py tests/ --ignore-missing-imports

.PHONY: dev
dev: ## Run web service locally, with reloading
	ENV_FOR_DYNACONF=dev pipenv run uvicorn fatcat_scholar.web:app --reload --port 9819

.PHONY: run
run: ## Run web service under gunicorn
	pipenv run gunicorn fatcat_scholar.web:app -w 4 -k uvicorn.workers.UvicornWorker

.PHONY: fetch-works
fetch-works: ## Fetches some works from any release .json in the data dir
	cat data/release_*.json | jq . -c | pipenv run python -m fatcat_scholar.work_pipeline run_releases | pv -l > data/work_intermediate.json

.PHONY: fetch-sim
fetch-sim: ## Fetches some SIM pages
	pipenv run python -m fatcat_scholar.sim_pipeline run_issue_db --limit 500 | pv -l > data/sim_intermediate.json

.PHONY: dev-index
dev-index: ## Delete/Create DEV elasticsearch fulltext index locally
	http delete ":9200/dev_scholar_fulltext_v01" && true
	http put ":9200/dev_scholar_fulltext_v01?include_type_name=true" < schema/scholar_fulltext.v01.json
	http put ":9200/dev_scholar_fulltext_v01/_alias/dev_scholar_fulltext"
	cat data/sim_intermediate.json data/work_intermediate.json | pipenv run python -m fatcat_scholar.transform run_transform | esbulk -verbose -size 200 -id key -w 4 -index dev_scholar_fulltext_v01 -type _doc

.PHONY: update-i18n
update-i18n: ## Re-extract and compile translation files
	pipenv run pybabel extract -F extra/i18n/babel.cfg -o extra/i18n/web_interface.pot fatcat_scholar/
	pipenv run pybabel update -i extra/i18n/web_interface.pot -d fatcat_scholar/translations
	pipenv run pybabel compile -d fatcat_scholar/translations
