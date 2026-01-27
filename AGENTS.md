# Repository Guidelines

## Project Structure & Module Organization
- `src/lumberjackth/` contains the library and CLI implementation. Key modules include `client.py` (Treeherder client), `cli.py` (Click CLI), `models/` (Pydantic models), and `exceptions.py`.
- `tests/` holds pytest suites that mirror module structure (for example, `tests/test_client.py`).
- `dist/` is build output; do not edit by hand.
- Repo metadata and tooling live in `pyproject.toml`, `.pre-commit-config.yaml`, and `.github/`.

## Build, Test, and Development Commands
- `uv sync --all-groups` — install all dev, lint, test, and audit dependencies.
- `uv run pytest` — run the full test suite with coverage.
- `uv run pytest tests/test_client.py::TestRepositoryEndpoints::test_get_repositories` — run a focused test.
- `uv run ruff check .` and `uv run ruff format --check .` — lint and formatting checks.
- `uv run ty check src/` — static type checking.
- `uv run ruff check --fix .` and `uv run ruff format .` — auto-fix lint/format issues.

## Coding Style & Naming Conventions
- Python formatting and linting are enforced by Ruff; max line length is 100.
- Target runtime is Python 3.11+; align type hints with `ty` checks.
- Module and test names use `snake_case`; classes use `PascalCase`.
- Prefer explicit, typed models via Pydantic in `src/lumberjackth/models/`.

## Testing Guidelines
- Pytest is the primary framework; coverage is enabled via `pytest-cov`.
- Async tests use `@pytest.mark.asyncio` (configured with `asyncio_mode = "auto"`).
- Mock HTTP calls with `respx` when exercising `httpx` interactions.

## Commit & Pull Request Guidelines
- Commit messages follow an imperative style seen in history (for example, “Add …”, “Update …”, “Release vX.Y.Z”).
- Include issue references when relevant (for example, “(#7)”).
- PRs should describe behavior changes, include test evidence (command output), and call out any API/CLI changes.

## Versioning & Release Notes
- Version is tracked in `pyproject.toml`, `src/lumberjackth/__init__.py`, and the user-agent string in `src/lumberjackth/client.py`.
- Update `CHANGELOG.md` entries and keep `uv.lock` in sync when releasing.
