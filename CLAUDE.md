# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lumberjack (`lumberjackth`) is a modern CLI and Python client for [Mozilla Treeherder](https://treeherder.mozilla.org/). It provides typed Python interfaces and command-line tools to query CI job results, pushes, and performance data from Treeherder.

## Development Commands

```bash
# Install dependencies
uv sync --all-groups

# Run tests with coverage
uv run pytest

# Run a single test file or test
uv run pytest tests/test_client.py
uv run pytest tests/test_client.py::TestRepositoryEndpoints::test_get_repositories

# Linting
uv run ruff check .
uv run ruff format --check .

# Type checking
uv run ty check src/

# Auto-fix lint issues
uv run ruff check --fix .
uv run ruff format .
```

## Architecture

```
src/lumberjackth/
├── __init__.py      # Package exports (TreeherderClient, exceptions, __version__)
├── client.py        # TreeherderClient - main API client (sync + async)
├── cli.py           # Click-based CLI commands (lumberjack/lj)
├── exceptions.py    # Exception hierarchy (LumberjackError base)
└── models/
    ├── core.py         # Pydantic models: Repository, Push, Job, JobLogUrl
    ├── performance.py  # Pydantic models: PerformanceAlertSummary, PerformanceFramework
    └── taskcluster.py  # Pydantic models: TaskclusterMetadata
```

### Key Patterns

- **TreeherderClient** (`client.py`): Supports both sync and async via `httpx`. Uses lazy client initialization - HTTP clients are created on first use, not at init. Handles pagination automatically for large result sets (MAX_COUNT=2000).

- **Models**: All use Pydantic with `extra="ignore"` to tolerate API changes. Models have computed properties (e.g., `Job.duration_seconds`, `Push.push_datetime`).

- **CLI**: Uses Click with Rich for table output. Global `--json` flag for machine-readable output. Entry points are `lumberjack` and `lj` (alias).

## Testing

Tests use `respx` to mock httpx requests. Test files mirror the module structure:
- `tests/test_client.py` - Client and API endpoint tests

Async tests are marked with `@pytest.mark.asyncio` and use `asyncio_mode = "auto"`.

## Version Management

Version is tracked in three places (update all for releases):
1. `pyproject.toml` - `version = "X.Y.Z"`
2. `src/lumberjackth/__init__.py` - `__version__ = "X.Y.Z"`
3. `src/lumberjackth/client.py` - User-Agent string

See `RELEASING.md` for full release process.

## Treeherder API

The client wraps these endpoints (base URL: `https://treeherder.mozilla.org/api/`):
- `/repository/` - List repositories
- `/project/{project}/push/` - List pushes for a repository
- `/project/{project}/jobs/` - List jobs
- `/project/{project}/job-log-url/` - Get job log URLs
- `/failureclassification/` - Failure types
- `/performance/framework/` - Performance frameworks
- `/performance/alertsummary/` - Performance alerts
