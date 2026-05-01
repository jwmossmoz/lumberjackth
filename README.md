# Lumberjack — Deprecated

> **This project is deprecated.** Use [`treeherder-cli`](https://github.com/padenot/treeherder-cli) instead.

`lumberjackth` is no longer maintained. Active development of a Treeherder CLI for Firefox CI work has moved to Paul Adenot's `treeherder-cli`, which covers revision-based failure analysis, comparison, history, log searching, artifact downloads, and watch mode.

For features `treeherder-cli` does not cover (push listing, failures-by-bug, error-line bug suggestions, performance alerts, repository listing), call the [Treeherder REST API](https://treeherder.readthedocs.io/) directly.

## Switch to treeherder-cli

```bash
cargo install --git https://github.com/padenot/treeherder-cli
```

### Command equivalents

| Old (`lj`) | New |
|------------|-----|
| `lj pushes <project>` | `curl -s -A "Mozilla/5.0" "https://treeherder.mozilla.org/api/project/<project>/push/?count=10"` |
| `lj jobs <project> --push-id <id>` | `curl -s -A "Mozilla/5.0" "https://treeherder.mozilla.org/api/project/<project>/jobs/?push_id=<id>&count=2000"` |
| `lj job <project> <guid>` | `treeherder-cli <revision> --filter <name> --json` |
| `lj log <project> <job_id> -p <pattern>` | `treeherder-cli <revision> --fetch-logs --pattern <pattern>` |
| `lj failures <bug_id>` | `curl -s -A "Mozilla/5.0" "https://treeherder.mozilla.org/api/failuresbybug/?bug=<bug_id>"` |
| `lj errors <project> <job_id>` | `curl -s -A "Mozilla/5.0" "https://treeherder.mozilla.org/api/project/<project>/jobs/<job_id>/bug_suggestions/"` |
| `lj perf-alerts` | `curl -s -A "Mozilla/5.0" "https://treeherder.mozilla.org/api/performance/alertsummary/?limit=10"` |
| `lj jobs <project> -r <revision> --watch` | `treeherder-cli <revision> --repo <project> --watch --notify` |
| `lj similar-jobs <project> <job_id>` | `treeherder-cli --similar-history <job_id> --repo <project> --json` |

## License

MPL-2.0
