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

# Filter jobs by platform regex and duration
lj jobs autoland --push-id 12345 -p "linux.*64" --duration-min 60

# Get details for a specific job
lj job mozilla-central "abc123def/0" --logs

# List performance alerts
lj perf-alerts --repository autoland

# Query test failures by bug ID
lj failures 2012615 --tree autoland --platform windows11-64-24h2

# Show errors and bug suggestions for a failed job
lj errors autoland 545896732

# Fetch and search job logs
lj log autoland 545896732 --pattern "ERROR|FAIL" --context 3

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
| `log <project> <job_id>` | Fetch and search job logs |
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
- `-p, --platform` - Filter by platform (regex pattern, e.g., 'linux.*64')
- `-f, --filter` - Filter by job name (regex pattern, e.g., 'mochitest')
- `--duration-min` - Filter to jobs with duration >= N seconds
- `-n, --count` - Number of jobs to show (default: 20, or all when --push-id specified)

#### job
- `--logs` - Show log URLs

#### log
- `-p, --pattern` - Regex pattern to search for in the log
- `-c, --context` - Number of context lines around matches (with --pattern)
- `--log-name` - Name of log to fetch (default: live_backing_log)
- `--head` - Show only the first N lines
- `--tail` - Show only the last N lines

#### failures
- `-t, --tree` - Repository filter (all, autoland, mozilla-central, etc.)
- `-p, --platform` - Filter by platform (regex pattern, e.g., 'windows.*64')
- `-b, --build-type` - Filter by build type (regex pattern, e.g., 'asan')
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

# Fetch and search job logs
log_content = client.get_job_log("autoland", job_id=12345)
matches = client.search_job_log("autoland", job_id=12345, pattern="ERROR", context_lines=3)

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
| `/api/project/{project}/job-log-url/` | `get_job_log_urls()` | Get job log URLs |
| (log content URL) | `get_job_log()` | Fetch raw log content |
| (log content URL) | `search_job_log()` | Search log with regex |
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
make dev

# Run tests
make test

# Run linting and type checking
make lint

# Format code
make format

# Build package
make build
```

Or run commands directly with `uv run`:

```bash
uv run pytest
uv run ruff check .
uv run ty check src/
```

## License

MPL-2.0
