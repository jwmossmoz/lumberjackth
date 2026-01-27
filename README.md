# Lumberjack

A modern CLI and Python client for [Mozilla Treeherder](https://treeherder.mozilla.org/).

Treeherder is a reporting dashboard for Mozilla checkins. It allows users to see the results of automatic builds and their respective tests. Lumberjack provides a clean, typed Python interface and command-line tool to query this data.

## Installation

```bash
pip install lumberjack
# or with uv
uv pip install lumberjack
```

## CLI Usage

Lumberjack provides the `lumberjack` command (or `lj` for short):

```bash
# List repositories
lumberjack repos

# List recent pushes for mozilla-central
lumberjack pushes mozilla-central

# List jobs for a specific push
lumberjack jobs mozilla-central --push-id 12345

# Get details for a specific job
lumberjack job mozilla-central "abc123def/0" --logs

# List performance alerts
lumberjack perf-alerts --repository autoland

# Output as JSON
lumberjack --json pushes mozilla-central -n 5
```

### Available Commands

| Command | Description |
|---------|-------------|
| `repos` | List available repositories |
| `pushes <project>` | List pushes for a project |
| `jobs <project>` | List jobs for a project |
| `job <project> <guid>` | Get details for a specific job |
| `perf-alerts` | List performance alert summaries |
| `perf-frameworks` | List performance testing frameworks |

### Options

- `-s, --server URL` - Treeherder server URL (default: https://treeherder.mozilla.org)
- `--json` - Output as JSON instead of tables
- `--version` - Show version

## Python API

```python
from lumberjack import TreeherderClient

# Create a client
client = TreeherderClient()

# List repositories
repos = client.get_repositories()
for repo in repos:
    print(f"{repo.name} ({repo.dvcs_type})")

# Get pushes for mozilla-central
pushes = client.get_pushes("mozilla-central", count=10)
for push in pushes:
    print(f"{push.revision[:12]} by {push.author}")

# Get jobs for a push
jobs = client.get_jobs("mozilla-central", push_id=pushes[0].id)
for job in jobs:
    print(f"{job.job_type_name}: {job.result}")

# Get a specific job by GUID
job = client.get_job_by_guid("mozilla-central", "abc123def/0")
if job:
    print(f"Duration: {job.duration_seconds}s")

# Get log URLs for a job
logs = client.get_job_log_urls("mozilla-central", job.id)
for log in logs:
    print(f"{log.name}: {log.url}")

# Performance alerts
alerts = client.get_performance_alert_summaries(repository="autoland")
for alert in alerts:
    print(f"{alert.repository}: {alert.regression_count} regressions")
```

### Async Support

```python
import asyncio
from lumberjack import TreeherderClient

async def main():
    async with TreeherderClient() as client:
        repos = await client.get_repositories_async()
        pushes = await client.get_pushes_async("mozilla-central", count=5)
        print(f"Found {len(pushes)} pushes")

asyncio.run(main())
```

## API Coverage

Lumberjack supports the following Treeherder API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/repository/` | `get_repositories()` | List repositories |
| `/api/project/{project}/push/` | `get_pushes()` | List pushes |
| `/api/project/{project}/jobs/` | `get_jobs()` | List jobs |
| `/api/project/{project}/job-log-url/` | `get_job_log_urls()` | Get job logs |
| `/api/failureclassification/` | `get_failure_classifications()` | Failure types |
| `/api/performance/framework/` | `get_performance_frameworks()` | Perf frameworks |
| `/api/performance/alertsummary/` | `get_performance_alert_summaries()` | Perf alerts |
| `/api/machineplatforms/` | `get_machine_platforms()` | Machine platforms |
| `/api/changelog/` | `get_changelog()` | Treeherder changelog |

## Comparison to treeherder-client

Lumberjack is a modern replacement for the `treeherder-client` package, which hasn't been updated since 2019:

| Feature | treeherder-client | lumberjack |
|---------|------------------|------------|
| Python version | 2.7+ | 3.11+ |
| Type hints | No | Yes (full) |
| Async support | No | Yes |
| CLI | No | Yes |
| Pydantic models | No | Yes |
| Performance API | Partial | Full |
| Active maintenance | No | Yes |

## Development

```bash
# Clone the repository
git clone https://github.com/jwmossmoz/lumberjack.git
cd lumberjack

# Install dependencies
uv sync --all-groups

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run ty check src/
```

## License

MPL-2.0
