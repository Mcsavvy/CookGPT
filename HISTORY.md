Changelog
=========


0.6.0 (2023-11-06)
------------------

New
~~~
- Feat: Add user_id and user_name to AuthInfoSchema. [mcsavvy]


0.5.5 (2023-11-01)
------------------

Changes
~~~~~~~
- Refactor: generate OpenAPI spec. [mcsavvy]


0.5.4 (2023-11-01)
------------------

New
~~~
- Feat: Added API description. [mcsavvy]


0.5.3 (2023-11-01)
------------------

Changes
~~~~~~~
- Chore: update Makefile for release command. [mcsavvy]
- Refactor: Simplify user query in login function. [mcsavvy]
- Refactor: Improve password hashing and authentication. [mcsavvy]


0.5.2 (2023-10-29)
------------------

New
~~~
- Feat: Add gevent to dependencies. [mcsavvy]

Changes
~~~~~~~
- Chore: added code coverage. [mcsavvy]
- Refactor: Remove password validators. [mcsavvy]
- Chore: add test for creating user without last name. [mcsavvy]
- Refactor: made lastname optional. [mcsavvy]
- Chore: Update environment and Procfile configurations. [mcsavvy]

Docs
~~~~
- Docs: Update Cookgpt API documentation. [mcsavvy]


0.5.1 (2023-10-23)
------------------

Changes
~~~~~~~
- Chore: added coverage. [mcsavvy]

Fix
~~~
- Chat/threads now returns user scoped threads. [mcsavvy]

  Fixes #30


0.5.0 (2023-10-14)
------------------

New
~~~
- Feat(chat): Implicit thread creation. [Isaac Olumide Ogunfolaju]
- Feat(makefile): Add OpenAPI spec generation. [Isaac Olumide
  Ogunfolaju]

Changes
~~~~~~~
- Chore: generated coverage. [Isaac Olumide Ogunfolaju]
- Refactor: Simplify logic for creating a new thread. [Isaac Olumide
  Ogunfolaju]
- Chore(openapi): generated openapi spec. [Isaac Olumide Ogunfolaju]

Fix
~~~
- Update default thread title to "New Thread" [Isaac Olumide Ogunfolaju]

Docs
~~~~
- Docs: update docs_path to root directory. [Isaac Olumide Ogunfolaju]

Tests
~~~~~
- Test: Test implicit thread creation. [Isaac Olumide Ogunfolaju]
- Test: test add_message method with no thread_id or previous_chat.
  [Isaac Olumide Ogunfolaju]
- Test: Split test into multiple methods. [Isaac Olumide Ogunfolaju]

Other
~~~~~
- Implicit Thread Creation. [github-actions[bot]]


0.4.2 (2023-10-14)
------------------
- Build: Add setup-python action and generate changelog. [Isaac Olumide
  Ogunfolaju]


0.4.1 (2023-10-14)
------------------

Changes
~~~~~~~
- Chore: Update deploy workflow and release workflow. [Isaac Olumide
  Ogunfolaju]
- Chore(ci): update merge method to merge. [Isaac Olumide Ogunfolaju]
- Refactor: improve release message script. [Isaac Olumide Ogunfolaju]

Fix
~~~
- Fix(workflow): installed gitchangelog in release.yml. [Isaac Olumide
  Ogunfolaju]

Other
~~~~~
- Bump version to 0.4.0. [github-actions[bot]]
- Bump version to 0.3.0. [github-actions[bot]]
- Bump version to 0.2.4. [github-actions[bot]]


0.4.0 (2023-10-13)
------------------
- Chat Threads. [Isaac Olumide Ogunfolaju]


0.3.0 (2023-10-02)
------------------
- Streaming Response 💥💫 [mcsavvy]


0.2.4 (2023-09-29)
------------------

Changes
~~~~~~~
- Chore(spec): regenerated openapi schema. [mcsavvy]
- Refactor(workflow): change heroku app. [mcsavvy]

Fix
~~~
- Missing import. [mcsavvy]
- Fix(ci): Updated bump doc id. [mcsavvy]

Other
~~~~~
- Merge 8912804e2de31ea4492f4151614a656c9ff30e12 into
  877ea26be07928294028d781b15149791135c120. [mcsavvy]
- Merge pull request #19 from Mcsavvy/dev. [mcsavvy]

  Bump version to 0.2.3
- Bump version to 0.2.2. [github-actions[bot]]
- Bump version to 0.2.1. [github-actions[bot]]
- Bump version to 0.2.0. [github-actions[bot]]


0.2.3 (2023-09-29)
------------------

Changes
~~~~~~~
- Chore: change gunicorn bind & server url. [mcsavvy]

Fix
~~~
- Create a workaround for user_type bug. [mcsavvy]


0.2.2 (2023-08-28)
------------------

New
~~~
- LLM Response Streaming. [mcsavvy]

Changes
~~~~~~~
- Chore(coverage): configured coverage. [mcsavvy]

Fix
~~~
- API Definition. [mcsavvy]

Other
~~~~~
- Merged changes. [mcsavvy]


0.2.0 (2023-08-26)
------------------

Breaking Changes
~~~~~~~~~~~~~~~~
- BREAKING CHANGE: removed user info. [mcsavvy]

  - removed `UserInfo` database model
  - removed enums and schemas

  User info came from a different app and I do not see a reason to
  maintain or refactor it.

New
~~~
- Feat: add .gitchangelog.rc file. [mcsavvy]
- Feat(ci): Add API documentation deployment and API diff check.
  [mcsavvy]
- Feature: added openapi specifications. [mcsavvy]
- Feat: Add devcontainer.json for Python 3. [mcsavvy]
- Feat(utils): add utility functions for API response management.
  [mcsavvy]
- Feat: added chatbot  💬🤖 [mcsavvy]
- Feat: Update dependencies. [mcsavvy]

Changes
~~~~~~~
- Refactor: Remove unused make targets and clean up Makefile. [mcsavvy]
- Chore(deploy.yml): Update env_file to .env.production. [mcsavvy]
- Chore: Update workflow names. [mcsavvy]
- Chore: Update activation script for different environments. [mcsavvy]
- Ci: Upload coverage reports to Codecov. [mcsavvy]
- Chore: Update prompts for ai chatbot. [mcsavvy]
- Refactor(auth): modified user types. [mcsavvy]

  - removed patient
  - replaced  with
- Refactor(config): move hooks to validators, add custom settings class.
  [mcsavvy]
- Refactor(config): remove unused hooks and simplify tests. [mcsavvy]
- Chore(db): created intial migration script. [mcsavvy]
- Chore: deleted old tests. [mcsavvy]
- Chore: pinned project dependencies. [mcsavvy]
- Refactor(app): refactor app initialization and configuration.
  [mcsavvy]
- Refactor: improved authentication logic. [mcsavvy]
- Chore: moved user logic into auth. [mcsavvy]
- Chore: Update exclude paths in pyproject.toml. [mcsavvy]
- Refactor: improve extensions & remove unused. [mcsavvy]
- Chore: Update VSCode launch and settings configurations. [mcsavvy]
- Chore: Update settings.toml. [mcsavvy]
- Refactor(config): refactor config file and add hooks. [mcsavvy]
- Chore: removed all migration scripts. [mcsavvy]
- Chore: Update .gitignore file. [mcsavvy]
- Chore: Remove LICENSE and MANIFEST.in files. [mcsavvy]
- Chore: Add pyproject.toml configuration file. [mcsavvy]
- Refactor: improve Makefile formatting and linting. [mcsavvy]
- Chore: Update python version and install command. [mcsavvy]

Fix
~~~
- Export ENV_PREFIX after activation. [mcsavvy]

Docs
~~~~
- Docs: Add documentation for user_type field. [mcsavvy]
- Docs: Update AI assistant description in API documentation. [mcsavvy]
- Docs: add Openapi Specification Docs. [mcsavvy]

Tests
~~~~~
- Tests: tested entire codebase. [mcsavvy]

Style
~~~~~
- Style: update formatting of fake_data.py. [mcsavvy]
- Style: simplify timedelta conversion in to_timedelta function.
  [mcsavvy]
- Style: reorder import statements in __init__.py. [mcsavvy]
- Style: Improve code quality. [mcsavvy]


0.1.13 (2023-07-28)
-------------------
- Tested Config Extension. [mcsavvy]
- Refactor config.py to use lowercase env variable. [mcsavvy]
- Refactored BaseModel. [mcsavvy]

  - made  not nullable
  - made  not nullable
- Added Config Extension. [mcsavvy]
- Added Management Script. [mcsavvy]
- Added Release Command To Procfile. [mcsavvy]
- Refactored JtwToken Model. [mcsavvy]

  - made `access_token` not nullable
  - made `active` not nullable
- Added Initial Migration. [mcsavvy]


0.1.12 (2023-07-25)
-------------------
- Fixed Workflow. [mcsavvy]


0.1.11 (2023-07-25)
-------------------
- Added Python Version Constraint. [mcsavvy]


0.1.10 (2023-07-25)
-------------------
- Added Heroku Git Remote. [mcsavvy]


0.1.9 (2023-07-25)
------------------
- Update Heroku app name to "my-kitchen-power" [mcsavvy]


0.1.6 (2023-07-23)
------------------
- Update Python version to 3.9.16. [mcsavvy]
- Removed Python Version Constraint. [mcsavvy]
- Release a new version and create a PR to main branch. [mcsavvy]
- Add automerge action for pull requests into dev branch. [mcsavvy]
- Added Deployment Workflow. [mcsavvy]


0.1.5 (2023-07-21)
------------------
- Updated Permissions For Release Workflow. [mcsavvy]
- Add SQLA to Flask Admin. [mcsavvy]
- Added Tests For Authentication. [mcsavvy]
- Added Validators For User Data. [mcsavvy]
- Fix linter and test commands in Makefile. [mcsavvy]
- Refactored User Model. [mcsavvy]

  - Added Serialization
  - Added Validation
  - Added support for jwt tokens
- Refactored BaseModel. [mcsavvy]

  - Added CreateError & UpdateError
  - Added serializable_keys attribute
- Refactor auth initialization and user loader. [mcsavvy]
- Add cov.xml to .gitignore. [mcsavvy]
- Use .venv file for virtual environment prefix. [mcsavvy]
- Added Git pre-commit Hook. [mcsavvy]
- Added Dependency For Migrations. [mcsavvy]
- Run tests with coverage report in XML format. [mcsavvy]
- Add "active" and "access_token" to serializable keys. [mcsavvy]
- Added Authentication Blueprint. [mcsavvy]
- Update JWT configuration and database URIs. [mcsavvy]
- Add VS Code launch and settings configurations. [mcsavvy]
- Added Migration & Customized Database Class. [mcsavvy]
- Update lint and test targets in Makefile. [mcsavvy]


0.1.4 (2023-07-12)
------------------
- Refactor test_api.py and conftest.py. [mcsavvy]
- Added githooks. [mcsavvy]


0.1.1 (2023-07-11)
------------------
- Refactor tests and release workflows. [mcsavvy]
- Add release workflow and update code formatting and linting. [mcsavvy]
- Update Python version to 3.10.5. [mcsavvy]
- Modified main workflow. [mcsavvy]
- Delete Unused Workflows. [mcsavvy]
- Added User App. [mcsavvy]
- Configured application entrypoint. [mcsavvy]
- Added application config file. [mcsavvy]
- Added Makefile. [mcsavvy]
- Configured Extensions. [mcsavvy]
- Renamed models.py -> base.py. [mcsavvy]
- Added project deps. [mcsavvy]
- Ignored all databases. [mcsavvy]
- Removed unused files. [mcsavvy]
- ✅ Ready to clone and code. [Mcsavvy]
- Initial commit. [† dave †]


