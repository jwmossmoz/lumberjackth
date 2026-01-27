"""Command-line interface for Lumberjack."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from lumberjack import TreeherderClient, __version__
from lumberjack.exceptions import LumberjackError

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
@click.option("--guid", help="Filter by job GUID.")
@click.option("--result", help="Filter by result (success, testfailed, etc.).")
@click.option("--state", help="Filter by state (pending, running, completed).")
@click.option("--tier", type=int, help="Filter by tier (1, 2, or 3).")
@click.option("-n", "--count", default=20, help="Number of jobs to show.")
@click.pass_context
def jobs(
    ctx: click.Context,
    project: str,
    push_id: int | None,
    guid: str | None,
    result: str | None,
    state: str | None,
    tier: int | None,
    count: int,
) -> None:
    """List jobs for a project.

    PROJECT is the repository name (e.g., mozilla-central, autoland).
    """
    client: TreeherderClient = ctx.obj["client"]

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

        if ctx.obj["json"]:
            output_json(job_list)
            return

        if not job_list:
            console.print(f"No jobs found for [cyan]{project}[/cyan]")
            return

        table = Table(title=f"Jobs for {project}")
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
                job.job_type_name[:50] + "..."
                if len(job.job_type_name) > 50
                else job.job_type_name,
                job.platform,
                job.state,
                f"[{result_style}]{job.result}[/{result_style}]" if result_style else job.result,
                duration,
            )

        console.print(table)

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


if __name__ == "__main__":
    main()
