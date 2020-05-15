
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

.PHONY: help
help: ## Print info about all commands
	@echo "Commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[01;32m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: test
test: ## Run all tests and lints
	pipenv run pytest
	pipenv run mypy fatcat_scholar/*.py tests/ --ignore-missing-imports

.PHONY: dev
dev: ## Run web service locally, with reloading
	pipenv run uvicorn fatcat_scholar.web:app --reload

.PHONY: run
run: ## Run web service under gunicorn
	pipenv run gunicorn fatcat_scholar.web:app -w 4 -k uvicorn.workers.UvicornWorker

.PHONY: reset-index-dev
reset-index-dev: ## Delete/Create DEV elasticsearch fulltext index locally
	http delete :9200/dev_scholar_fulltext_v01 && true
	http put ":9200/qa_scholar_fulltext_v01?include_type_name=false" < schema/scholar_fulltext.v01.json
	http delete :9200/dev_scholar_fulltext && true
	http put :9200/dev_scholar_fulltext_v01/_alias/dev_scholar_fulltext

