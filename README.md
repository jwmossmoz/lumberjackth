# Lumberjack

A modern CLI and Python client for [Mozilla Treeherder](https://treeherder.mozilla.org/).

Treeherder is a reporting dashboard for Mozilla checkins. It allows users to see the results of automatic builds and their respective tests. Lumberjack provides a clean, typed Python interface and command-line tool to query this data.

## Installation

```bash
pip install lumberjackth
# or with uv
uv pip install lumberjackth
```

## CLI Usage

Lumberjack provides the `lj` command (or `lumberjack` as an alias):

```bash
# List repositories
lj repos

# List recent pushes for mozilla-central
lj pushes mozilla-central

# List jobs for a specific push
lj jobs mozilla-central --push-id 12345

# Get details for a specific job
lj job mozilla-central "abc123def/0" --logs

# List performance alerts
lj perf-alerts --repository autoland

# Query test failures by bug ID
lj failures 2012615 --tree autoland --platform windows11-64-24h2

# Show errors and bug suggestions for a failed job
lj errors autoland 545896732

# Output as JSON
lj --json pushes mozilla-central -n 5
```

### Available Commands

| Command | Description |
|---------|-------------|
| `repos` | List available repositories |
| `pushes <project>` | List pushes for a project |
| `jobs <project>` | List jobs for a project |
| `job <project> <guid>` | Get details for a specific job |
| `failures <bug_id>` | List test failures associated with a bug |
| `errors <project> <job_id>` | Show error lines and bug suggestions |
| `perf-alerts` | List performance alert summaries |
| `perf-frameworks` | List performance testing frameworks |

Run with `uvx` for zero-install execution:

```bash
uvx --from lumberjackth lj repos
uvx --from lumberjackth lj failures 2012615 -t autoland
```

### Global Options

- `-s, --server URL` - Treeherder server URL (default: https://treeherder.mozilla.org)
- `--json` - Output as JSON instead of tables
- `--version` - Show version

### Command Options

#### repos
- `--active/--all` - Show only active repositories (default: active)

#### pushes
- `-n, --count` - Number of pushes to show (default: 10)
- `-r, --revision` - Filter by revision
- `-a, --author` - Filter by author email

#### jobs
- `--push-id` - Filter by push ID
- `--guid` - Filter by job GUID
- `--result` - Filter by result (success, testfailed, busted, etc.)
- `--state` - Filter by state (pending, running, completed)
- `--tier` - Filter by tier (1, 2, or 3)
- `-n, --count` - Number of jobs to show (default: 20, or all when --push-id specified)

#### job
- `--logs` - Show log URLs

#### failures
- `-t, --tree` - Repository filter (all, autoland, mozilla-central, etc.)
- `-p, --platform` - Filter by platform (e.g., windows11-64-24h2, linux)
- `-b, --build-type` - Filter by build type (e.g., asan, debug, opt)
- `-s, --startday` - Start date YYYY-MM-DD (default: 7 days ago)
- `-e, --endday` - End date YYYY-MM-DD (default: today)
- `-n, --count` - Limit number of results

#### errors
- `--suggestions/--no-suggestions` - Show bug suggestions (default: on)

#### perf-alerts
- `-r, --repository` - Filter by repository
- `-f, --framework` - Filter by framework ID
- `-n, --limit` - Number of alerts to show

## Python API

```python
from lumberjackth import TreeherderClient

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

# Query failures by bug ID (useful for investigating intermittents)
failures = client.get_failures_by_bug(2012615, tree="autoland")
for f in failures:
    print(f"{f.platform} {f.build_type}: {f.test_suite}")

# Get error lines and bug suggestions for a failed job
errors = client.get_text_log_errors("autoland", job_id=12345)
suggestions = client.get_bug_suggestions("autoland", job_id=12345)

# Performance alerts
alerts = client.get_performance_alert_summaries(repository="autoland")
for alert in alerts:
    print(f"{alert.repository}: {alert.regression_count} regressions")
```

### Async Support

```python
import asyncio
from lumberjackth import TreeherderClient

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
| `/api/project/{project}/jobs/{id}/text_log_errors/` | `get_text_log_errors()` | Get error lines from job |
| `/api/project/{project}/jobs/{id}/bug_suggestions/` | `get_bug_suggestions()` | Get bug suggestions |
| `/api/failuresbybug/` | `get_failures_by_bug()` | Query failures by bug ID |
| `/api/failureclassification/` | `get_failure_classifications()` | Failure types |
| `/api/optioncollectionhash/` | `get_option_collection_hash()` | Option collections |
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
git clone https://github.com/jwmossmoz/lumberjackth.git
cd lumberjackth

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
