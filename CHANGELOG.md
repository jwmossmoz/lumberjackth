# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2026-02-02

### Added

- New CLI command `similar-jobs <project> <job_id>`: Find similar jobs (same job type from recent pushes)
  - Useful for comparing a failing job against recent passing runs
  - Shows job ID, push ID, author, result, duration, and task ID
  - `-n/--count` option to control number of results (default: 10)
  - JSON output support with `--json`
- New client methods:
  - `get_similar_jobs()`: Query `/api/project/{project}/jobs/{job_id}/similar_jobs/`
  - `get_similar_jobs_async()`: Async version of the above

## [1.3.0] - 2026-01-29

### Added

- New `--watch/-w` flag for `jobs` command to continuously monitor job status
- New `--interval/-i` flag to control watch refresh rate (default: 30 seconds)
- New `--revision/-r` flag for `jobs` command as alternative to `--push-id`
- Watch mode displays summary stats (job states and results)
- Watch mode highlights changes between refreshes (new jobs, status changes)
- Graceful Ctrl+C handling for watch mode

## [1.2.0] - 2026-01-28

### Added

- New CLI command `log <project> <job_id>`: Fetch and display job logs
  - Search logs with `--pattern` (regex support)
  - Show context lines around matches with `--context`
  - Display first/last N lines with `--head`/`--tail`
  - JSON output support with `--json`
- New client methods:
  - `get_job_log()`: Fetch raw log content from a job
  - `search_job_log()`: Search log content with regex patterns
- Enhanced `jobs` command filtering:
  - Platform regex filtering with `-p/--platform`
  - Job name regex filtering with `-f/--filter`
  - Duration filtering with `--duration-min`
- Enhanced `failures` command with regex-based filtering

## [1.1.0] - 2026-01-28

### Added

- New CLI command `failures <bug_id>`: Query test failures by bug ID across repositories
  - Filter by platform (`-p`), build type (`-b`), tree (`-t`), and date range (`-s`, `-e`)
  - Shows unique error patterns across all failures
- New CLI command `errors <project> <job_id>`: Show error lines and bug suggestions for a failed job
- New client methods:
  - `get_failures_by_bug()`: Query `/api/failuresbybug/` endpoint
  - `get_text_log_errors()`: Query `/api/project/{project}/jobs/{job_id}/text_log_errors/`
  - `get_bug_suggestions()`: Query `/api/project/{project}/jobs/{job_id}/bug_suggestions/`
- New models: `FailureByBug`, `TextLogError`, `BugSuggestion`, `BugMatch`

## [1.0.6] - 2026-01-27

### Changed

- `jobs` command now returns all jobs (up to 2000) when filtering by `--push-id`, instead of defaulting to 20

## [1.0.5] - 2026-01-27

### Fixed

- Allow `unscheduled` as a valid job state in the `Job` model

## [1.0.4] - 2026-01-27

### Added

- `get_option_collection_hash()` method for fetching option collection mappings (feature parity with legacy treeherder-client)

## [1.0.3] - 2026-01-27

### Changed

- Switched back to uv_build backend (simpler than hatchling)
- Renamed package directory from `src/lumberjack` to `src/lumberjackth` for consistency

## [1.0.2] - 2026-01-27

### Fixed

- Fixed build by switching from uv_build to hatchling backend

## [1.0.1] - 2026-01-27

### Changed

- Renamed PyPI package to `lumberjackth`
- Added security CI job with actionlint and zizmor
- Added pre-commit hooks configuration
- Pinned all GitHub Actions to commit SHAs

## [1.0.0] - 2026-01-27

### Added

- Initial release
- `TreeherderClient` with sync and async support
- CLI commands: `repos`, `pushes`, `jobs`, `job`, `perf-alerts`, `perf-frameworks`
- Pydantic models for all API responses
- Full type hints throughout
- Support for Treeherder API endpoints:
  - `/api/repository/` - List repositories
  - `/api/project/{project}/push/` - List pushes
  - `/api/project/{project}/jobs/` - List jobs
  - `/api/project/{project}/job-log-url/` - Get job logs
  - `/api/failureclassification/` - Failure types
  - `/api/performance/framework/` - Performance frameworks
  - `/api/performance/alertsummary/` - Performance alerts
  - `/api/machineplatforms/` - Machine platforms
  - `/api/changelog/` - Treeherder changelog

[Unreleased]: https://github.com/jwmossmoz/lumberjackth/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/jwmossmoz/lumberjackth/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/jwmossmoz/lumberjackth/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/jwmossmoz/lumberjackth/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.6...v1.1.0
[1.0.6]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jwmossmoz/lumberjackth/releases/tag/v1.0.0
