# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-27

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

[Unreleased]: https://github.com/jwmossmoz/lumberjack/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jwmossmoz/lumberjack/releases/tag/v0.1.0
