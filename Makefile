.PHONY: dev lint format test build clean

dev:
	uv sync --all-groups

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run ty check src/

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest

build:
	uv build

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
