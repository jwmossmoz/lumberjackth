"""Command-line interface for Lumberjack."""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from lumberjackth import TreeherderClient, __version__
from lumberjackth.exceptions import LumberjackError

console = Console()
error_console = Console(stderr=True)


def format_timestamp(ts: int) -> str:
    """Format a Unix timestamp as a human-readable string."""
    dt = datetime.fromtimestamp(ts, tz=UTC)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def format_duration(seconds: int) -> str:
    """Format duration in seconds as human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def output_json(data: Any) -> None:
    """Output data as JSON."""
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif isinstance(data, list) and data and hasattr(data[0], "model_dump"):
        data = [item.model_dump() for item in data]
    click.echo(json.dumps(data, indent=2, default=str))


def _display_failures_table(failure_list: list[Any], bug_id: int) -> None:
    """Display failures in a table format."""
    table = Table(title=f"Failures for Bug {bug_id}")
    table.add_column("Time", style="dim")
    table.add_column("Tree", style="cyan")
    table.add_column("Platform")
    table.add_column("Build")
    table.add_column("Test Suite")
    table.add_column("Task ID", style="dim")

    for failure in failure_list:
        test_suite = failure.test_suite
        if len(test_suite) > 40:
            test_suite = test_suite[:40] + "..."
        table.add_row(
            failure.push_time[:16],
            failure.tree,
            failure.platform,
            failure.build_type,
            test_suite,
            failure.task_id[:12],
        )

    console.print(table)
    console.print(f"\nTotal: [bold]{len(failure_list)}[/bold] failures")


def _display_error_patterns(failure_list: list[Any]) -> None:
    """Display unique error patterns from failures."""
    all_lines: set[str] = set()
    for f in failure_list:
        all_lines.update(f.lines)
    if not all_lines:
        return

    console.print("\n[bold]Unique error patterns:[/bold]")
    for line in sorted(all_lines)[:10]:
        display_line = line[:100] + "..." if len(line) > 100 else line
        console.print(f"  [red]•[/red] {display_line}")
    if len(all_lines) > 10:
        console.print(f"  ... and {len(all_lines) - 10} more")


def _display_bug_suggestions(suggestion_list: list[Any]) -> None:
    """Display bug suggestions for errors."""
    if not suggestion_list:
        return

    console.print("[bold]Bug Suggestions:[/bold]\n")
    for sugg in suggestion_list:
        new_marker = "[yellow]NEW[/yellow] " if sugg.failure_new_in_rev else ""
        console.print(f"  {new_marker}[dim]Line {sugg.line_number}:[/dim] {sugg.search[:80]}")
        open_bugs = sugg.bugs.get("open_recent", [])
        for bug in open_bugs[:3]:
            if bug.id:
                console.print(f"    [cyan]Bug {bug.id}[/cyan]: {bug.summary[:60]}")
            else:
                console.print(f"    [dim]{bug.summary[:70]}[/dim]")
        console.print()


def _display_log_matches(matches: list[dict[str, Any]], pattern: str, context: int) -> None:
    """Display log search matches with optional context."""
    console.print(f"\n[bold]Found {len(matches)} matches[/bold] for pattern: {pattern}\n")
    for match in matches:
        console.print(f"[dim]Line {match['line_number']}:[/dim]")
        if context > 0 and "context" in match:
            for ctx_line in match["context"]:
                if ctx_line == match["line"]:
                    console.print(f"  [yellow]>{ctx_line}[/yellow]")
                else:
                    console.print(f"   {ctx_line}")
        else:
            console.print(f"  [yellow]{match['line']}[/yellow]")
        console.print()


def _get_log_lines(
    log_content: str,
    head: int | None,
    tail: int | None,
) -> list[str]:
    """Extract lines from log content with optional head/tail limits."""
    lines = log_content.splitlines()
    if head:
        return lines[:head]
    if tail:
        return lines[-tail:]
    return lines


def _filter_jobs(
    job_list: list[Any],
    platform: str | None,
    job_filter: str | None,
    duration_min: int | None,
) -> list[Any]:
    """Apply client-side filters to job list."""
    import re  # noqa: PLC0415

    if platform:
        platform_re = re.compile(platform, re.IGNORECASE)
        job_list = [j for j in job_list if platform_re.search(j.platform)]

    if job_filter:
        filter_re = re.compile(job_filter, re.IGNORECASE)
        job_list = [j for j in job_list if filter_re.search(j.job_type_name)]

    if duration_min:
        job_list = [j for j in job_list if j.duration_seconds >= duration_min]

    return job_list


def _filter_failures(
    failure_list: list[Any],
    platform: str | None,
    build_type: str | None,
    count: int | None,
) -> list[Any]:
    """Apply client-side filters to failure list."""
    import re  # noqa: PLC0415

    if platform:
        platform_re = re.compile(platform, re.IGNORECASE)
        failure_list = [f for f in failure_list if platform_re.search(f.platform)]

    if build_type:
        build_re = re.compile(build_type, re.IGNORECASE)
        failure_list = [f for f in failure_list if build_re.search(f.build_type)]

    if count:
        failure_list = failure_list[:count]

    return failure_list


def _display_jobs_table(job_list: list[Any], project: str, title_suffix: str = "") -> None:
    """Display jobs in a table format."""
    title = f"Jobs for {project}"
    if title_suffix:
        title = f"{title} {title_suffix}"

    table = Table(title=title)
    table.add_column("ID", style="dim")
    table.add_column("Symbol", style="cyan")
    table.add_column("Name")
    table.add_column("Platform")
    table.add_column("State")
    table.add_column("Result")
    table.add_column("Duration", justify="right")

    for job in job_list:
        result_style = ""
        if job.result == "success":
            result_style = "green"
        elif job.result in ("testfailed", "busted", "exception"):
            result_style = "red"
        elif job.result == "retry":
            result_style = "yellow"

        duration = ""
        if job.state == "completed":
            duration = format_duration(job.duration_seconds)

        table.add_row(
            str(job.id),
            f"{job.job_group_symbol}({job.job_type_symbol})",
            job.job_type_name[:50] + "..." if len(job.job_type_name) > 50 else job.job_type_name,
            job.platform,
            job.state,
            f"[{result_style}]{job.result}[/{result_style}]" if result_style else job.result,
            duration,
        )

    console.print(table)


def _watch_jobs(
    client: TreeherderClient,
    project: str,
    push_id: int | None,
    guid: str | None,
    result: str | None,
    state: str | None,
    tier: int | None,
    platform: str | None,
    job_filter: str | None,
    duration_min: int | None,
    count: int,
    interval: int,
) -> None:
    """Watch jobs with periodic refresh."""
    previous_jobs: dict[int, tuple[str, str]] = {}  # job_id -> (state, result)

    console.print(
        f"[dim]Watching jobs (refresh every {interval}s, press Ctrl+C to stop)...[/dim]\n"
    )

    try:
        iteration = 0
        while True:
            iteration += 1

            # Fetch current jobs
            job_list = client.get_jobs(
                project,
                count=count,
                push_id=push_id,
                job_guid=guid,
                result=result,
                state=state,
                tier=tier,
            )

            # Apply client-side filters
            job_list = _filter_jobs(job_list, platform, job_filter, duration_min)

            # Track changes
            current_jobs = {job.id: (job.state, job.result) for job in job_list}
            new_jobs = [job for job in job_list if job.id not in previous_jobs]
            changed_jobs = [
                job
                for job in job_list
                if job.id in previous_jobs and previous_jobs[job.id] != current_jobs[job.id]
            ]

            # Clear screen and display
            console.clear()
            timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
            suffix = f"(refresh #{iteration} at {timestamp})"

            _display_jobs_table(job_list, project, suffix)

            # Show summary stats
            total = len(job_list)
            by_state = {}
            by_result = {}
            for job in job_list:
                by_state[job.state] = by_state.get(job.state, 0) + 1
                by_result[job.result] = by_result.get(job.result, 0) + 1

            console.print(f"\n[bold]Summary:[/bold] {total} jobs")
            console.print(f"  States: {', '.join(f'{k}={v}' for k, v in sorted(by_state.items()))}")
            console.print(
                f"  Results: {', '.join(f'{k}={v}' for k, v in sorted(by_result.items()))}"
            )

            # Show changes since last refresh
            if iteration > 1:
                if new_jobs:
                    console.print(f"\n[yellow]New jobs:[/yellow] {len(new_jobs)}")
                if changed_jobs:
                    console.print(f"[yellow]Changed jobs:[/yellow] {len(changed_jobs)}")
                    for job in changed_jobs[:5]:  # Show first 5 changes
                        old_state, old_result = previous_jobs[job.id]
                        console.print(
                            f"  • {job.job_type_name[:40]}: "
                            f"{old_state}/{old_result} → {job.state}/{job.result}"
                        )
                    if len(changed_jobs) > 5:
                        console.print(f"  ... and {len(changed_jobs) - 5} more")

            console.print(f"\n[dim]Next refresh in {interval}s (Ctrl+C to stop)[/dim]")

            previous_jobs = current_jobs
            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped watching[/yellow]")
    except LumberjackError as e:
        error_console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@click.group()
@click.option(
    "--server",
    "-s",
    default="https://treeherder.mozilla.org",
    help="Treeherder server URL.",
    envvar="TREEHERDER_URL",
)
@click.option(
    "--json",
    "output_format",
    is_flag=True,
    help="Output as JSON.",
)
@click.version_option(version=__version__, prog_name="lumberjack")
@click.pass_context
def main(ctx: click.Context, server: str, output_format: bool) -> None:
    """Lumberjack - A modern CLI for Mozilla Treeherder.

    Query pushes, jobs, and performance data from Treeherder.
    """
    ctx.ensure_object(dict)
    ctx.obj["client"] = TreeherderClient(server_url=server)
    ctx.obj["json"] = output_format


@main.command("repos")
@click.option("--active/--all", default=True, help="Show only active repositories.")
@click.pass_context
def repos(ctx: click.Context, active: bool) -> None:
    """List available repositories."""
    client: TreeherderClient = ctx.obj["client"]

    try:
        repositories = client.get_repositories()
        if active:
            repositories = [r for r in repositories if r.active_status == "active"]

        if ctx.obj["json"]:
            output_json(repositories)
            return

        table = Table(title="Repositories")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Group")
        table.add_column("Try?")
        table.add_column("Perf Alerts?")

        for repo in sorted(repositories, key=lambda r: r.name):
            table.add_row(
                repo.name,
                repo.dvcs_type,
                repo.repository_group.name,
                "Yes" if repo.is_try_repo else "",
                "Yes" if repo.performance_alerts_enabled else "",
            )

        console.print(table)

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("pushes")
@click.argument("project")
@click.option("-n", "--count", default=10, help="Number of pushes to show.")
@click.option("-r", "--revision", help="Filter by revision.")
@click.option("-a", "--author", help="Filter by author email.")
@click.pass_context
def pushes(
    ctx: click.Context,
    project: str,
    count: int,
    revision: str | None,
    author: str | None,
) -> None:
    """List pushes for a project.

    PROJECT is the repository name (e.g., mozilla-central, autoland).
    """
    client: TreeherderClient = ctx.obj["client"]

    try:
        push_list = client.get_pushes(
            project,
            count=count,
            revision=revision,
            author=author,
        )

        if ctx.obj["json"]:
            output_json(push_list)
            return

        if not push_list:
            console.print(f"No pushes found for [cyan]{project}[/cyan]")
            return

        table = Table(title=f"Pushes for {project}")
        table.add_column("ID", style="dim")
        table.add_column("Revision", style="cyan")
        table.add_column("Author")
        table.add_column("Time")
        table.add_column("Commits", justify="right")

        for push in push_list:
            table.add_row(
                str(push.id),
                push.revision[:12],
                push.author,
                format_timestamp(push.push_timestamp),
                str(push.revision_count),
            )

        console.print(table)

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("jobs")
@click.argument("project")
@click.option("--push-id", type=int, help="Filter by push ID.")
@click.option("--revision", "-r", help="Filter by revision (alternative to --push-id).")
@click.option("--guid", help="Filter by job GUID.")
@click.option("--result", help="Filter by result (success, testfailed, etc.).")
@click.option("--state", help="Filter by state (pending, running, completed).")
@click.option("--tier", type=int, help="Filter by tier (1, 2, or 3).")
@click.option(
    "-p",
    "--platform",
    help="Filter by platform (regex pattern, e.g., 'linux.*64').",
)
@click.option(
    "-f",
    "--filter",
    "job_filter",
    help="Filter by job name (regex pattern, e.g., 'mochitest').",
)
@click.option(
    "--duration-min",
    type=int,
    help="Filter to jobs with duration >= N seconds.",
)
@click.option(
    "-n",
    "--count",
    default=None,
    type=int,
    help="Number of jobs to show (default: 20, or all when --push-id is specified).",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch for job updates (refreshes periodically).",
)
@click.option(
    "--interval",
    "-i",
    default=30,
    type=int,
    help="Refresh interval in seconds when using --watch (default: 30).",
)
@click.pass_context
def jobs(
    ctx: click.Context,
    project: str,
    push_id: int | None,
    revision: str | None,
    guid: str | None,
    result: str | None,
    state: str | None,
    tier: int | None,
    platform: str | None,
    job_filter: str | None,
    duration_min: int | None,
    count: int | None,
    watch: bool,
    interval: int,
) -> None:
    """List jobs for a project.

    PROJECT is the repository name (e.g., mozilla-central, autoland).

    Examples:

    \b
        # Watch jobs for a specific revision
        lj jobs try --revision abc123 --watch

    \b
        # Watch only test failures
        lj jobs autoland --push-id 12345 --result testfailed --watch
    """
    client: TreeherderClient = ctx.obj["client"]

    # Resolve revision to push_id if provided
    if revision and not push_id:
        try:
            push_list = client.get_pushes(project, count=1, revision=revision)
            if not push_list:
                error_console.print(f"[red]Error:[/red] No push found for revision {revision}")
                sys.exit(1)
            push_id = push_list[0].id
        except LumberjackError as e:
            error_console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    # Default to all jobs when filtering by push_id, otherwise 20
    if count is None:
        count = 2000 if push_id else 20

    if watch:
        if ctx.obj["json"]:
            error_console.print("[red]Error:[/red] --watch is not compatible with --json")
            sys.exit(1)
        _watch_jobs(
            client,
            project,
            push_id,
            guid,
            result,
            state,
            tier,
            platform,
            job_filter,
            duration_min,
            count,
            interval,
        )
        return

    try:
        job_list = client.get_jobs(
            project,
            count=count,
            push_id=push_id,
            job_guid=guid,
            result=result,
            state=state,
            tier=tier,
        )

        # Apply client-side filters
        job_list = _filter_jobs(job_list, platform, job_filter, duration_min)

        if ctx.obj["json"]:
            output_json(job_list)
            return

        if not job_list:
            console.print(f"No jobs found for [cyan]{project}[/cyan]")
            return

        _display_jobs_table(job_list, project)

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("job")
@click.argument("project")
@click.argument("job_guid")
@click.option("--logs", is_flag=True, help="Show log URLs.")
@click.pass_context
def job(ctx: click.Context, project: str, job_guid: str, logs: bool) -> None:
    """Get details for a specific job.

    PROJECT is the repository name.
    JOB_GUID is the job's GUID (e.g., abc123def/0).
    """
    client: TreeherderClient = ctx.obj["client"]

    try:
        job_data = client.get_job_by_guid(project, job_guid)

        if not job_data:
            error_console.print(f"[red]Job not found:[/red] {job_guid}")
            sys.exit(1)

        if ctx.obj["json"]:
            data = job_data.model_dump()
            if logs:
                log_urls = client.get_job_log_urls(project, job_data.id)
                data["log_urls"] = [log.model_dump() for log in log_urls]
            output_json(data)
            return

        console.print(f"\n[bold]Job Details[/bold]: {job_guid}\n")
        console.print(f"  [cyan]ID:[/cyan] {job_data.id}")
        console.print(f"  [cyan]Type:[/cyan] {job_data.job_type_name}")
        console.print(
            f"  [cyan]Symbol:[/cyan] {job_data.job_group_symbol}({job_data.job_type_symbol})"
        )
        console.print(f"  [cyan]Platform:[/cyan] {job_data.platform}")
        console.print(f"  [cyan]State:[/cyan] {job_data.state}")
        console.print(f"  [cyan]Result:[/cyan] {job_data.result}")
        console.print(f"  [cyan]Tier:[/cyan] {job_data.tier}")
        console.print(f"  [cyan]Push ID:[/cyan] {job_data.push_id}")
        console.print(f"  [cyan]Submitted:[/cyan] {format_timestamp(job_data.submit_timestamp)}")
        console.print(f"  [cyan]Started:[/cyan] {format_timestamp(job_data.start_timestamp)}")
        console.print(f"  [cyan]Ended:[/cyan] {format_timestamp(job_data.end_timestamp)}")
        if job_data.state == "completed":
            console.print(f"  [cyan]Duration:[/cyan] {format_duration(job_data.duration_seconds)}")
        if job_data.task_id:
            console.print(f"  [cyan]Task ID:[/cyan] {job_data.task_id}")
            console.print(
                f"  [cyan]Task URL:[/cyan] https://firefox-ci-tc.services.mozilla.com/tasks/{job_data.task_id}"
            )

        if logs:
            log_urls = client.get_job_log_urls(project, job_data.id)
            if log_urls:
                console.print("\n[bold]Log URLs:[/bold]")
                for log in log_urls:
                    console.print(f"  - {log.name}: {log.url}")

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("perf-alerts")
@click.option("-r", "--repository", help="Filter by repository.")
@click.option("-f", "--framework", type=int, help="Filter by framework ID.")
@click.option("-n", "--limit", default=20, help="Number of alerts to show.")
@click.pass_context
def perf_alerts(
    ctx: click.Context,
    repository: str | None,
    framework: int | None,
    limit: int,
) -> None:
    """List performance alert summaries."""
    client: TreeherderClient = ctx.obj["client"]

    try:
        summaries = client.get_performance_alert_summaries(
            repository=repository,
            framework=framework,
            limit=limit,
        )

        if ctx.obj["json"]:
            output_json(summaries)
            return

        if not summaries:
            console.print("No performance alert summaries found")
            return

        table = Table(title="Performance Alert Summaries")
        table.add_column("ID", style="dim")
        table.add_column("Repository", style="cyan")
        table.add_column("Revision")
        table.add_column("Created")
        table.add_column("Regressions", justify="right", style="red")
        table.add_column("Improvements", justify="right", style="green")

        for summary in summaries:
            table.add_row(
                str(summary.id),
                summary.repository,
                summary.original_revision[:12] if summary.original_revision else "-",
                summary.created.strftime("%Y-%m-%d %H:%M"),
                str(summary.regression_count),
                str(summary.improvement_count),
            )

        console.print(table)

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("perf-frameworks")
@click.pass_context
def perf_frameworks(ctx: click.Context) -> None:
    """List performance testing frameworks."""
    client: TreeherderClient = ctx.obj["client"]

    try:
        frameworks = client.get_performance_frameworks()

        if ctx.obj["json"]:
            output_json(frameworks)
            return

        table = Table(title="Performance Frameworks")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")

        for fw in frameworks:
            table.add_row(str(fw.id), fw.name)

        console.print(table)

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("failures")
@click.argument("bug_id", type=int)
@click.option(
    "-s",
    "--startday",
    help="Start date (YYYY-MM-DD). Defaults to 7 days ago.",
)
@click.option(
    "-e",
    "--endday",
    help="End date (YYYY-MM-DD). Defaults to today.",
)
@click.option(
    "-t",
    "--tree",
    default="all",
    help="Repository filter (all, autoland, mozilla-central, etc.).",
)
@click.option(
    "-p",
    "--platform",
    help="Filter by platform (regex pattern, e.g., 'windows.*64', 'linux').",
)
@click.option(
    "-b",
    "--build-type",
    help="Filter by build type (regex pattern, e.g., 'asan', 'debug').",
)
@click.option(
    "-n",
    "--count",
    type=int,
    help="Limit number of results shown.",
)
@click.pass_context
def failures(
    ctx: click.Context,
    bug_id: int,
    startday: str | None,
    endday: str | None,
    tree: str,
    platform: str | None,
    build_type: str | None,
    count: int | None,
) -> None:
    """List test failures associated with a bug.

    BUG_ID is the Bugzilla bug number.

    This command queries failures across all repositories, useful for
    investigating intermittent failures or tracking image rollout regressions.

    Examples:

    \b
        # All failures for bug 2012615 in the last 7 days
        lj failures 2012615

    \b
        # Filter to windows asan failures on autoland
        lj failures 2012615 -t autoland -p windows11-64-24h2 -b asan

    \b
        # Failures in a specific date range
        lj failures 2012615 -s 2026-01-26 -e 2026-01-28
    """
    client: TreeherderClient = ctx.obj["client"]

    try:
        failure_list = client.get_failures_by_bug(
            bug_id,
            startday=startday,
            endday=endday,
            tree=tree,
        )

        # Apply client-side filters (regex-based)
        failure_list = _filter_failures(failure_list, platform, build_type, count)

        if ctx.obj["json"]:
            output_json(failure_list)
            return

        if not failure_list:
            console.print(f"No failures found for bug [cyan]{bug_id}[/cyan]")
            return

        _display_failures_table(failure_list, bug_id)
        _display_error_patterns(failure_list)

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("errors")
@click.argument("project")
@click.argument("job_id", type=int)
@click.option("--suggestions/--no-suggestions", default=True, help="Show bug suggestions.")
@click.pass_context
def errors(
    ctx: click.Context,
    project: str,
    job_id: int,
    suggestions: bool,
) -> None:
    """Show error lines and bug suggestions for a failed job.

    PROJECT is the repository name (e.g., autoland).
    JOB_ID is the numeric job ID (not the task ID).

    Examples:

    \b
        # Show errors for job 545896732 on autoland
        lj errors autoland 545896732

    \b
        # Just errors, no bug suggestions
        lj errors autoland 545896732 --no-suggestions
    """
    client: TreeherderClient = ctx.obj["client"]

    try:
        error_list = client.get_text_log_errors(project, job_id)

        if ctx.obj["json"]:
            data: dict[str, Any] = {"errors": [e.model_dump() for e in error_list]}
            if suggestions:
                suggestion_list = client.get_bug_suggestions(project, job_id)
                data["suggestions"] = [s.model_dump() for s in suggestion_list]
            output_json(data)
            return

        if not error_list:
            console.print(f"No errors found for job [cyan]{job_id}[/cyan]")
            return

        console.print(f"\n[bold]Errors for Job {job_id}[/bold] ({project})\n")

        for err in error_list:
            new_marker = "[yellow]NEW[/yellow] " if err.new_failure else ""
            console.print(f"  {new_marker}[dim]Line {err.line_number}:[/dim]")
            console.print(f"    [red]{err.line}[/red]\n")

        if suggestions:
            suggestion_list = client.get_bug_suggestions(project, job_id)
            _display_bug_suggestions(suggestion_list)

    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("log")
@click.argument("project")
@click.argument("job_id", type=int)
@click.option(
    "-p",
    "--pattern",
    help="Regex pattern to search for in the log.",
)
@click.option(
    "-c",
    "--context",
    type=int,
    default=0,
    help="Number of context lines around matches (with --pattern).",
)
@click.option(
    "--log-name",
    default="live_backing_log",
    help="Name of log to fetch (default: live_backing_log).",
)
@click.option(
    "--head",
    type=int,
    help="Show only the first N lines.",
)
@click.option(
    "--tail",
    type=int,
    help="Show only the last N lines.",
)
@click.pass_context
def log(
    ctx: click.Context,
    project: str,
    job_id: int,
    pattern: str | None,
    context: int,
    log_name: str,
    head: int | None,
    tail: int | None,
) -> None:
    """Fetch and display a job's log.

    PROJECT is the repository name (e.g., autoland).
    JOB_ID is the numeric job ID.

    Examples:

    \b
        # View full log
        lj log autoland 545896732

    \b
        # Search for errors
        lj log autoland 545896732 --pattern "ERROR|FAIL"

    \b
        # Search with context lines
        lj log autoland 545896732 -p "assertion" -c 5

    \b
        # View last 100 lines
        lj log autoland 545896732 --tail 100

    \b
        # Output as JSON (useful with --pattern)
        lj --json log autoland 545896732 -p "TEST-UNEXPECTED"
    """
    client: TreeherderClient = ctx.obj["client"]

    if head and tail:
        error_console.print("[red]Error:[/red] Cannot use both --head and --tail")
        sys.exit(1)

    try:
        if pattern:
            _handle_log_search(client, ctx, project, job_id, pattern, context, log_name)
        else:
            _handle_log_display(client, ctx, project, job_id, log_name, head, tail)
    except LumberjackError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _handle_log_search(
    client: TreeherderClient,
    ctx: click.Context,
    project: str,
    job_id: int,
    pattern: str,
    context: int,
    log_name: str,
) -> None:
    """Handle log search mode."""
    matches = client.search_job_log(
        project, job_id, pattern, log_name=log_name, context_lines=context
    )

    if ctx.obj["json"]:
        output_json({"matches": matches, "total": len(matches)})
        return

    if not matches:
        console.print(f"No matches found for pattern [cyan]{pattern}[/cyan]")
        return

    _display_log_matches(matches, pattern, context)


def _handle_log_display(
    client: TreeherderClient,
    ctx: click.Context,
    project: str,
    job_id: int,
    log_name: str,
    head: int | None,
    tail: int | None,
) -> None:
    """Handle full log display mode."""
    log_content = client.get_job_log(project, job_id, log_name=log_name)
    lines = _get_log_lines(log_content, head, tail)

    if ctx.obj["json"]:
        output_json({"log": "\n".join(lines), "line_count": len(lines)})
        return

    for line in lines:
        click.echo(line)


if __name__ == "__main__":
    main()
