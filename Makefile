.ONESHELL:
ENV_PREFIX=.venv/bin
FILES='.'
PYTEST_ARGS=--cov-config .coveragerc --cov-report xml --cov=cookgpt --cov-append --cov-report term-missing --cov-fail-under=95 --no-cov-on-fail


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

.PHONY: requirements
requirements:     ## Generate requirements files.
	@poetry export --without-hashes -o requirements.txt
	@poetry export --only dev --without-hashes -o requirements-dev.txt
	@poetry export --only test --without-hashes -o requirements-test.txt


.PHONY: init
init:          ## Initialize the project.
	@# check if virtual environment exists
	@if [ ! -d "$(ENV_PREFIX)" ]; then
		@echo "Creating virtual environment..."
		@python3 -m venv .venv
	fi
	@echo "Installing dependencies..."
	@poetry self add poetry-plugin-export
	@poetry install --with dev,test

.PHONY: run
run:              ## Run the project.	
	$(ENV_PREFIX)/gunicorn -c gunicorn.conf.py

.PHONY: test
test:             ## Run tests and generate coverage report.
	export FLASK_ENV=testing
	$(ENV_PREFIX)/coverage erase
	$(ENV_PREFIX)/pytest $(PYTEST_ARGS) tests/ || exit $$?

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find . -name __pycache__ -exec rm -rf {} +
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf .ruff_cache
	@rm -rf *.egg-info
	@rm -rf htmlcov


.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create a version tag and push to github"
	@PREV_BRANCH=$$(git rev-parse --abbrev-ref HEAD)
	@git checkout dev || exit $$?
	echo "Current version is $$(cat cookgpt/VERSION)"
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	echo "creating git tag : $${TAG}"
	@git tag $${TAG} || exit $$?
	@echo "$${TAG}" > cookgpt/VERSION
	@$(ENV_PREFIX)/gitchangelog > HISTORY.md
	echo "generating OpenAPI spec..."
	@$(ENV_PREFIX)/flask spec > openapi.json
	@git add cookgpt/VERSION HISTORY.md openapi.json
	@git commit --no-verify -m "release: version $${TAG} 🚀" || exit $$?
	@git push -u origin HEAD --tags || exit $$?
	@git checkout $${PREV_BRANCH} || exit $$?
	@echo "Github Actions will detect the new tag and release the new version."

.PHONY: hooks
hooks:            ## Add git hooks to local environment
	@ln -f .githooks/pre-commit .git/hooks/pre-commit

.PHONY: spec
spec:             ## Generate OpenAPI spec.
	@$(ENV_PREFIX)/flask spec > openapi.json
	echo "OpenAPI spec generated at openapi.json"