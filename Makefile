.ONESHELL:
ENV_PREFIX=$(shell if [ -z "$$PIPENV_ACTIVE" ]; then pipenv --venv; else echo "$$ENV_PREFIX"; fi)/bin
DEV_MODE=$(shell grep "FLASK_ENV=development" .env && echo "true")
FILES="."


.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	@echo "Running using $(ENV_PREFIX)"
	@$(ENV_PREFIX)/python -V
	@$(ENV_PREFIX)/python -m site

.PHONY: virtualenv
virtualenv:       ## Create a virtual environment.
	@if [ "$(shell pipenv --venv > /dev/null)" ]; then echo "Virtual environment already exists"; else pipenv --python 3.10; fi

.PHONY: install
install:          ## Install the project in dev mode.
	@if [ "$(DEV_MODE)" ]; then pipenv install --dev; else pipenv install; fi

.PHONY: requirements
requirements:     ## Generate requirements.txt.
	@pipenv requirements > requirements.txt
	@pipenv requirements --dev-only >> requirements-dev.txt

.PHONY: run
run:              ## Run the project.
	@if [ "$(DEV_MODE)" ]; then $(ENV_PREFIX)/flask run; else $(ENV_PREFIX)/gunicorn; fi

.PHONY: fmt
fmt:              ## Format code using black & isort.
	$(ENV_PREFIX)/isort $(FILES)
	$(ENV_PREFIX)/black -l 79 $(FILES)

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)/flake8 $(FILES) || exit $$?
	$(ENV_PREFIX)/black -l 79 --check $(FILES) || exit $$?
	$(ENV_PREFIX)/mypy --ignore-missing-imports $(FILES) || exit $$?

.PHONY: test
test:             ## Run tests and generate coverage report.
	$(ENV_PREFIX)/pytest -v --cov-config .coveragerc --cov-report xml:cov.xml --cov=cookgpt -l --tb=short tests/ || exit $$?

.PHONY: watch
watch:            ## Run tests on every change.
	ls **/**.py | entr $(ENV_PREFIX)pytest -s -vvv -l --tb=long --maxfail=1 tests/

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find . -name __pycache__ -exec rm -rf {} +
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build


.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create a version tag and push to github"
	@PREV_BRANCH=$$(git rev-parse --abbrev-ref HEAD)
	@git checkout dev || exit $$?
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG} || exit $$?
	@echo "$${TAG}" > cookgpt/VERSION
	@$(ENV_PREFIX)/gitchangelog > HISTORY.md
	@git add cookgpt/VERSION HISTORY.md
	@git commit --no-verify -m "release: version $${TAG} 🚀" || exit $$?
	@git push -u origin HEAD --tags || exit $$?
	@git checkout $${PREV_BRANCH} || exit $$?
	@echo "Github Actions will detect the new tag and release the new version."

.PHONY: hooks
hooks:            ## Add git hooks to local environment
	@ln -f .githooks/pre-commit .git/hooks/pre-commit
