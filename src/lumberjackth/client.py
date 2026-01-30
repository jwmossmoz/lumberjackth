"""Treeherder API client."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Self, TypeVar
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from lumberjackth.exceptions import (
    TreeherderAPIError,
    TreeherderAuthError,
    TreeherderNotFoundError,
    TreeherderRateLimitError,
)
from lumberjackth.models.core import (
    BugSuggestion,
    FailureByBug,
    FailureClassification,
    Job,
    JobLogUrl,
    OptionCollection,
    Push,
    Repository,
    TextLogError,
)
from lumberjackth.models.performance import (
    PerformanceAlertSummary,
    PerformanceFramework,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_SERVER_URL = "https://treeherder.mozilla.org"
API_VERSION = "1.0"
MAX_COUNT = 2000


class TreeherderClient:
    """Client for the Treeherder API.

    This client provides access to the Treeherder REST API, supporting both
    synchronous and asynchronous operations.

    Example:
        >>> client = TreeherderClient()
        >>> repos = client.get_repositories()
        >>> pushes = client.get_pushes("mozilla-central", count=10)
        >>> jobs = client.get_jobs("mozilla-central", push_id=12345)

    For async usage:
        >>> async with TreeherderClient() as client:
        ...     repos = await client.get_repositories_async()
    """

    def __init__(
        self,
        server_url: str = DEFAULT_SERVER_URL,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Treeherder client.

        Args:
            server_url: Base URL of the Treeherder instance.
            timeout: Request timeout in seconds.
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self._headers = {
            "Accept": f"application/json; version={API_VERSION}",
            "User-Agent": "lumberjackth/1.3.0",
        }
        self._sync_client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    def _get_sync_client(self) -> httpx.Client:
        """Get or create the synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                headers=self._headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create the asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                headers=self._headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._async_client

    def close(self) -> None:
        """Close the synchronous HTTP client."""
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        """Close the asynchronous HTTP client."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def _build_url(self, endpoint: str, project: str | None = None) -> str:
        """Build the full URL for an API endpoint."""
        if project:
            path = f"/api/project/{project}/{endpoint}/"
        else:
            path = f"/api/{endpoint}/"
        return urljoin(self.server_url, path)

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP errors and raise appropriate exceptions."""
        if response.is_success:
            return

        try:
            body = response.json()
        except Exception:
            body = response.text

        if response.status_code == 404:
            raise TreeherderNotFoundError(
                f"Resource not found: {response.url}",
                status_code=404,
                response_body=body,
            )
        if response.status_code in (401, 403):
            raise TreeherderAuthError(
                f"Authentication/authorization failed: {response.url}",
                status_code=response.status_code,
                response_body=body,
            )
        if response.status_code == 429:
            raise TreeherderRateLimitError(
                "Rate limit exceeded",
                status_code=429,
                response_body=body,
            )

        raise TreeherderAPIError(
            f"API error: {response.status_code}",
            status_code=response.status_code,
            response_body=body,
        )

    def _request(
        self,
        endpoint: str,
        project: str | None = None,
        **params: Any,
    ) -> dict[str, Any]:
        """Make a synchronous API request."""
        url = self._build_url(endpoint, project)
        # Filter out None values from params
        params = {k: v for k, v in params.items() if v is not None}

        logger.debug("GET %s params=%s", url, params)
        response = self._get_sync_client().get(url, params=params)
        self._handle_error(response)
        return response.json()

    async def _request_async(
        self,
        endpoint: str,
        project: str | None = None,
        **params: Any,
    ) -> dict[str, Any]:
        """Make an asynchronous API request."""
        url = self._build_url(endpoint, project)
        # Filter out None values from params
        params = {k: v for k, v in params.items() if v is not None}

        logger.debug("GET %s params=%s", url, params)
        response = await self._get_async_client().get(url, params=params)
        self._handle_error(response)
        return response.json()

    def _get_list(
        self,
        endpoint: str,
        project: str | None = None,
        count: int | None = None,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Get a list of results, handling pagination."""
        if count is not None and count <= MAX_COUNT:
            params["count"] = count
            data = self._request(endpoint, project, **params)
            return data.get("results", data) if isinstance(data, dict) else data

        # Handle pagination for large requests
        all_results: list[dict[str, Any]] = []
        offset = 0
        remaining = count

        while True:
            batch_count = min(MAX_COUNT, remaining) if remaining else MAX_COUNT
            params["count"] = batch_count
            params["offset"] = offset

            data = self._request(endpoint, project, **params)
            results = data.get("results", data) if isinstance(data, dict) else data

            all_results.extend(results)

            if len(results) < batch_count:
                break

            offset += len(results)
            if remaining:
                remaining -= len(results)
                if remaining <= 0:
                    break

        return all_results

    async def _get_list_async(
        self,
        endpoint: str,
        project: str | None = None,
        count: int | None = None,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Get a list of results asynchronously, handling pagination."""
        if count is not None and count <= MAX_COUNT:
            params["count"] = count
            data = await self._request_async(endpoint, project, **params)
            return data.get("results", data) if isinstance(data, dict) else data

        # Handle pagination for large requests
        all_results: list[dict[str, Any]] = []
        offset = 0
        remaining = count

        while True:
            batch_count = min(MAX_COUNT, remaining) if remaining else MAX_COUNT
            params["count"] = batch_count
            params["offset"] = offset

            data = await self._request_async(endpoint, project, **params)
            results = data.get("results", data) if isinstance(data, dict) else data

            all_results.extend(results)

            if len(results) < batch_count:
                break

            offset += len(results)
            if remaining:
                remaining -= len(results)
                if remaining <= 0:
                    break

        return all_results

    # -------------------------------------------------------------------------
    # Repository endpoints
    # -------------------------------------------------------------------------

    def get_repositories(self) -> list[Repository]:
        """Get all available repositories.

        Returns:
            List of Repository objects.
        """
        data = self._request("repository")
        return [Repository.model_validate(r) for r in data]

    async def get_repositories_async(self) -> list[Repository]:
        """Get all available repositories asynchronously."""
        data = await self._request_async("repository")
        return [Repository.model_validate(r) for r in data]

    def get_repository(self, name: str) -> Repository | None:
        """Get a specific repository by name.

        Args:
            name: Repository name (e.g., "mozilla-central").

        Returns:
            Repository object or None if not found.
        """
        repos = self.get_repositories()
        return next((r for r in repos if r.name == name), None)

    # -------------------------------------------------------------------------
    # Push endpoints
    # -------------------------------------------------------------------------

    def get_pushes(
        self,
        project: str,
        *,
        count: int | None = 10,
        revision: str | None = None,
        author: str | None = None,
        push_timestamp__gte: int | None = None,
        push_timestamp__lte: int | None = None,
    ) -> list[Push]:
        """Get pushes for a project.

        Args:
            project: Repository name (e.g., "mozilla-central").
            count: Maximum number of pushes to return.
            revision: Filter by revision hash.
            author: Filter by author email.
            push_timestamp__gte: Filter by minimum push timestamp.
            push_timestamp__lte: Filter by maximum push timestamp.

        Returns:
            List of Push objects.
        """
        data = self._get_list(
            "push",
            project,
            count=count,
            revision=revision,
            author=author,
            push_timestamp__gte=push_timestamp__gte,
            push_timestamp__lte=push_timestamp__lte,
        )
        return [Push.model_validate(p) for p in data]

    async def get_pushes_async(
        self,
        project: str,
        *,
        count: int | None = 10,
        revision: str | None = None,
        author: str | None = None,
    ) -> list[Push]:
        """Get pushes for a project asynchronously."""
        data = await self._get_list_async(
            "push",
            project,
            count=count,
            revision=revision,
            author=author,
        )
        return [Push.model_validate(p) for p in data]

    def get_push_by_revision(self, project: str, revision: str) -> Push | None:
        """Get a push by its revision hash.

        Args:
            project: Repository name.
            revision: Full or partial revision hash.

        Returns:
            Push object or None if not found.
        """
        pushes = self.get_pushes(project, revision=revision, count=1)
        return pushes[0] if pushes else None

    # -------------------------------------------------------------------------
    # Job endpoints
    # -------------------------------------------------------------------------

    def get_jobs(
        self,
        project: str,
        *,
        count: int | None = 100,
        push_id: int | None = None,
        job_guid: str | None = None,
        job_type_name: str | None = None,
        job_type_symbol: str | None = None,
        job_group_symbol: str | None = None,
        result: str | None = None,
        state: str | None = None,
        tier: int | None = None,
        who: str | None = None,
    ) -> list[Job]:
        """Get jobs for a project.

        Args:
            project: Repository name (e.g., "mozilla-central").
            count: Maximum number of jobs to return.
            push_id: Filter by push ID.
            job_guid: Filter by job GUID.
            job_type_name: Filter by job type name.
            job_type_symbol: Filter by job type symbol.
            job_group_symbol: Filter by job group symbol.
            result: Filter by result (e.g., "success", "testfailed").
            state: Filter by state (e.g., "completed", "running").
            tier: Filter by tier (1, 2, or 3).
            who: Filter by author email.

        Returns:
            List of Job objects.
        """
        data = self._get_list(
            "jobs",
            project,
            count=count,
            push_id=push_id,
            job_guid=job_guid,
            job_type_name=job_type_name,
            job_type_symbol=job_type_symbol,
            job_group_symbol=job_group_symbol,
            result=result,
            state=state,
            tier=tier,
            who=who,
        )
        return [Job.model_validate(j) for j in data]

    async def get_jobs_async(
        self,
        project: str,
        *,
        count: int | None = 100,
        push_id: int | None = None,
        job_guid: str | None = None,
        result: str | None = None,
        state: str | None = None,
    ) -> list[Job]:
        """Get jobs for a project asynchronously."""
        data = await self._get_list_async(
            "jobs",
            project,
            count=count,
            push_id=push_id,
            job_guid=job_guid,
            result=result,
            state=state,
        )
        return [Job.model_validate(j) for j in data]

    def get_job_by_guid(self, project: str, job_guid: str) -> Job | None:
        """Get a specific job by its GUID.

        Args:
            project: Repository name.
            job_guid: Job GUID (e.g., "abc123/0").

        Returns:
            Job object or None if not found.
        """
        jobs = self.get_jobs(project, job_guid=job_guid, count=1)
        return jobs[0] if jobs else None

    def get_job_log_urls(
        self,
        project: str,
        job_id: int,
    ) -> list[JobLogUrl]:
        """Get log URLs for a job.

        Args:
            project: Repository name.
            job_id: Job ID (not GUID).

        Returns:
            List of JobLogUrl objects.
        """
        data = self._request("job-log-url", project, job_id=job_id)
        results = data.get("results", data) if isinstance(data, dict) else data
        return [JobLogUrl.model_validate(log) for log in results]

    def get_job_log(
        self,
        project: str,
        job_id: int,
        log_name: str = "live_backing_log",
    ) -> str:
        """Fetch the raw log content for a job.

        Args:
            project: Repository name.
            job_id: Job ID.
            log_name: Name of the log to fetch (default: live_backing_log).
                      Common values: live_backing_log, errorsummary_json

        Returns:
            The log content as a string.

        Raises:
            TreeherderNotFoundError: If the log is not found.
        """
        log_urls = self.get_job_log_urls(project, job_id)
        for log in log_urls:
            if log.name == log_name:
                response = self._get_sync_client().get(log.url)
                self._handle_error(response)
                return response.text

        raise TreeherderNotFoundError(
            f"Log '{log_name}' not found for job {job_id}",
            status_code=404,
            response_body=None,
        )

    async def get_job_log_async(
        self,
        project: str,
        job_id: int,
        log_name: str = "live_backing_log",
    ) -> str:
        """Fetch the raw log content for a job asynchronously."""
        log_urls = self.get_job_log_urls(project, job_id)
        for log in log_urls:
            if log.name == log_name:
                response = await self._get_async_client().get(log.url)
                self._handle_error(response)
                return response.text

        raise TreeherderNotFoundError(
            f"Log '{log_name}' not found for job {job_id}",
            status_code=404,
            response_body=None,
        )

    def search_job_log(
        self,
        project: str,
        job_id: int,
        pattern: str,
        log_name: str = "live_backing_log",
        context_lines: int = 0,
    ) -> list[dict[str, Any]]:
        """Search a job's log for lines matching a regex pattern.

        Args:
            project: Repository name.
            job_id: Job ID.
            pattern: Regex pattern to search for.
            log_name: Name of the log to search.
            context_lines: Number of context lines before/after matches.

        Returns:
            List of dicts with 'line_number', 'line', and optionally 'context'.
        """
        import re  # noqa: PLC0415

        log_content = self.get_job_log(project, job_id, log_name)
        lines = log_content.splitlines()
        regex = re.compile(pattern)
        matches = []

        for i, line in enumerate(lines):
            if regex.search(line):
                match_info: dict[str, Any] = {
                    "line_number": i + 1,
                    "line": line,
                }
                if context_lines > 0:
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    match_info["context"] = lines[start:end]
                matches.append(match_info)

        return matches

    def get_text_log_errors(
        self,
        project: str,
        job_id: int,
    ) -> list[TextLogError]:
        """Get parsed error lines from a job's log.

        Args:
            project: Repository name.
            job_id: Job ID.

        Returns:
            List of TextLogError objects containing error lines.
        """
        url = f"{self.server_url}/api/project/{project}/jobs/{job_id}/text_log_errors/"
        response = self._get_sync_client().get(url)
        self._handle_error(response)
        data = response.json()
        return [TextLogError.model_validate(e) for e in data]

    async def get_text_log_errors_async(
        self,
        project: str,
        job_id: int,
    ) -> list[TextLogError]:
        """Get parsed error lines from a job's log asynchronously."""
        url = f"{self.server_url}/api/project/{project}/jobs/{job_id}/text_log_errors/"
        response = await self._get_async_client().get(url)
        self._handle_error(response)
        data = response.json()
        return [TextLogError.model_validate(e) for e in data]

    def get_bug_suggestions(
        self,
        project: str,
        job_id: int,
    ) -> list[BugSuggestion]:
        """Get bug suggestions for a failed job.

        Args:
            project: Repository name.
            job_id: Job ID.

        Returns:
            List of BugSuggestion objects with matching bugs for each error.
        """
        url = f"{self.server_url}/api/project/{project}/jobs/{job_id}/bug_suggestions/"
        response = self._get_sync_client().get(url)
        self._handle_error(response)
        data = response.json()
        return [BugSuggestion.model_validate(s) for s in data]

    async def get_bug_suggestions_async(
        self,
        project: str,
        job_id: int,
    ) -> list[BugSuggestion]:
        """Get bug suggestions for a failed job asynchronously."""
        url = f"{self.server_url}/api/project/{project}/jobs/{job_id}/bug_suggestions/"
        response = await self._get_async_client().get(url)
        self._handle_error(response)
        data = response.json()
        return [BugSuggestion.model_validate(s) for s in data]

    # -------------------------------------------------------------------------
    # Failures by bug endpoint
    # -------------------------------------------------------------------------

    def get_failures_by_bug(
        self,
        bug_id: int,
        *,
        startday: str | None = None,
        endday: str | None = None,
        tree: str = "all",
    ) -> list[FailureByBug]:
        """Get test failures associated with a bug.

        This endpoint aggregates failures across repositories, making it useful
        for investigating intermittent failures or tracking regressions.

        Args:
            bug_id: Bugzilla bug ID.
            startday: Start date in YYYY-MM-DD format. Defaults to 7 days ago.
            endday: End date in YYYY-MM-DD format. Defaults to today.
            tree: Repository filter. Use "all" for all repos, or specific repo
                  like "autoland", "mozilla-central".

        Returns:
            List of FailureByBug objects with failure details.
        """
        # API requires startday and endday - provide defaults
        if endday is None:
            endday = datetime.now(UTC).strftime("%Y-%m-%d")
        if startday is None:
            startday = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")

        url = f"{self.server_url}/api/failuresbybug/"
        params: dict[str, Any] = {
            "bug": bug_id,
            "tree": tree,
            "startday": startday,
            "endday": endday,
        }

        response = self._get_sync_client().get(url, params=params)
        self._handle_error(response)
        data = response.json()
        return [FailureByBug.model_validate(f) for f in data]

    async def get_failures_by_bug_async(
        self,
        bug_id: int,
        *,
        startday: str | None = None,
        endday: str | None = None,
        tree: str = "all",
    ) -> list[FailureByBug]:
        """Get test failures associated with a bug asynchronously."""
        # API requires startday and endday - provide defaults
        if endday is None:
            endday = datetime.now(UTC).strftime("%Y-%m-%d")
        if startday is None:
            startday = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")

        url = f"{self.server_url}/api/failuresbybug/"
        params: dict[str, Any] = {
            "bug": bug_id,
            "tree": tree,
            "startday": startday,
            "endday": endday,
        }

        response = await self._get_async_client().get(url, params=params)
        self._handle_error(response)
        data = response.json()
        return [FailureByBug.model_validate(f) for f in data]

    # -------------------------------------------------------------------------
    # Failure classification endpoints
    # -------------------------------------------------------------------------

    def get_failure_classifications(self) -> list[FailureClassification]:
        """Get all failure classification types.

        Returns:
            List of FailureClassification objects.
        """
        data = self._request("failureclassification")
        return [FailureClassification.model_validate(fc) for fc in data]

    # -------------------------------------------------------------------------
    # Option collection endpoints
    # -------------------------------------------------------------------------

    def get_option_collection_hash(self) -> list[OptionCollection]:
        """Get all option collection hash mappings.

        Option collections map build option combinations (like opt, debug, asan)
        to their hash identifiers used in job data.

        Returns:
            List of OptionCollection objects.
        """
        data = self._request("optioncollectionhash")
        return [OptionCollection.model_validate(oc) for oc in data]

    # -------------------------------------------------------------------------
    # Performance endpoints
    # -------------------------------------------------------------------------

    def get_performance_frameworks(self) -> list[PerformanceFramework]:
        """Get all performance testing frameworks.

        Returns:
            List of PerformanceFramework objects.
        """
        data = self._request("performance/framework")
        return [PerformanceFramework.model_validate(f) for f in data]

    def get_performance_alert_summaries(
        self,
        *,
        repository: str | None = None,
        framework: int | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> list[PerformanceAlertSummary]:
        """Get performance alert summaries.

        Args:
            repository: Filter by repository name.
            framework: Filter by framework ID.
            limit: Maximum number of results per page.
            page: Page number (1-indexed).

        Returns:
            List of PerformanceAlertSummary objects.
        """
        data = self._request(
            "performance/alertsummary",
            repository=repository,
            framework=framework,
            limit=limit,
            page=page,
        )
        results = data.get("results", [])
        return [PerformanceAlertSummary.model_validate(s) for s in results]

    # -------------------------------------------------------------------------
    # Machine platforms endpoint
    # -------------------------------------------------------------------------

    def get_machine_platforms(self) -> list[dict[str, Any]]:
        """Get all machine platforms.

        Returns:
            List of machine platform dictionaries.
        """
        data = self._request("machineplatforms")
        return data.get("results", data) if isinstance(data, dict) else data

    # -------------------------------------------------------------------------
    # Changelog endpoint
    # -------------------------------------------------------------------------

    def get_changelog(self) -> list[dict[str, Any]]:
        """Get the Treeherder changelog.

        Returns:
            List of changelog entries.
        """
        data = self._request("changelog")
        return data.get("results", data) if isinstance(data, dict) else data
