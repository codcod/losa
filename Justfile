export PYTHONPATH := "."

ARGS_TEST := env("_UV_RUN_ARGS_TEST", "")

@_:
   just --list

# Run demo (application/serve not required)
[group('demo')]
demo:
    uv run python ./scripts/demo.py

# Run demo for models (application needs to be serving)
[group('demo')]
demo-models:
    uv run python ./scripts/demo_models.py

# Run demo for architecture (application needs to be serving)
[group('demo')]
demo-architecture:
    uv run python ./scripts/demo_architecture.py

# Start PostgreSQL in Docker
[group('project')]
start-db:
    docker-compose up -d postgres

# Initialize database, run after starting the database
[group('project')]
init-db:
    uv run python ./scripts/run.py --init-db

# Run the application server, after initializing the database
[group('project')]
serve:
    uv run python ./scripts/run.py

# Update dependencies
[group('lifecycle')]
update:
    uv sync --upgrade

# Ensure project virtualenv is up to date
[group('lifecycle')]
install:
    uv sync --group dev

# Remove temporary files
[group('lifecycle')]
clean:
    rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
    find . -type d -name "__pycache__" -exec rm -r {} +

# Remove temporary files, incl. virtualenv
[group('lifecycle')]
clean-all: clean
    rm -rf .venv

# Recreate project virtualenv from nothing
[group('lifecycle')]
fresh: clean-all install

# Run pylint for errors only
[group('qa')]
pylint:
    @echo "Running pylint... It will take a while."
    @uv pip install pylint
    uv run pylint .

# Run linters and formatters
[group('qa')]
lint:
    uvx black src tests scripts examples
    uvx ruff check src tests scripts examples --fix --unsafe-fixes

# Run tests
[group('qa')]
test *args:
    uv run {{ ARGS_TEST }} -m pytest {{ args }}

_cov *args:
    uv run -m coverage {{ args }}

# Run tests and measure coverage
[group('qa')]
@cov:
    just _cov erase
    just _cov run -m pytest tests
    just _cov report

# Check types
[group('qa')]
typing:
    uvx ty check --python .venv src

# Perform all checks
[group('qa')]
check-all: lint cov typing

# vim: set filetype=Makefile ts=4 sw=4 et:
