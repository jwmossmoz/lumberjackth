# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.5...HEAD
[1.0.5]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jwmossmoz/lumberjackth/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jwmossmoz/lumberjackth/releases/tag/v1.0.0
