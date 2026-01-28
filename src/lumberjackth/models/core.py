"""Core Pydantic models for Treeherder API responses."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class RepositoryGroup(BaseModel):
    """Repository group information."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: str


class Repository(BaseModel):
    """Treeherder repository."""

    model_config = ConfigDict(extra="ignore")

    id: int
    repository_group: RepositoryGroup
    name: str
    dvcs_type: Literal["hg", "git"]
    url: str
    branch: str | None = None
    codebase: str
    description: str
    active_status: Literal["active", "inactive"]
    life_cycle_order: int | None = None
    performance_alerts_enabled: bool
    expire_performance_data: bool
    is_try_repo: bool
    tc_root_url: str


class Revision(BaseModel):
    """A single revision in a push."""

    model_config = ConfigDict(extra="ignore")

    result_set_id: int
    repository_id: int
    revision: str
    author: str
    comments: str


class Push(BaseModel):
    """A push (result set) containing one or more revisions."""

    model_config = ConfigDict(extra="ignore")

    id: int
    revision: str
    author: str
    revisions: list[Revision]
    revision_count: int
    push_timestamp: int
    repository_id: int

    @property
    def push_datetime(self) -> datetime:
        """Return push timestamp as datetime."""
        return datetime.fromtimestamp(self.push_timestamp, tz=UTC)


class Job(BaseModel):
    """A CI job."""

    model_config = ConfigDict(extra="ignore")

    id: int
    job_guid: str
    push_id: int
    result_set_id: int

    # Build info
    build_architecture: str
    build_os: str
    build_platform: str
    build_platform_id: int
    build_system_type: str

    # Job type info
    job_group_id: int
    job_group_name: str
    job_group_symbol: str
    job_group_description: str
    job_type_id: int
    job_type_name: str
    job_type_symbol: str
    job_type_description: str

    # Machine info
    machine_name: str
    machine_platform_architecture: str
    machine_platform_os: str

    # Platform info
    platform: str
    platform_option: str | None = None
    option_collection_hash: str

    # Status
    state: Literal["pending", "running", "completed", "unscheduled"]
    result: str
    failure_classification_id: int
    tier: int

    # Timestamps
    submit_timestamp: int
    start_timestamp: int
    end_timestamp: int
    last_modified: str

    # Metadata
    reason: str
    who: str
    ref_data_name: str
    signature: str

    # Taskcluster info
    task_id: str | None = None
    retry_id: int | None = None

    @property
    def submit_datetime(self) -> datetime:
        """Return submit timestamp as datetime."""
        return datetime.fromtimestamp(self.submit_timestamp, tz=UTC)

    @property
    def start_datetime(self) -> datetime:
        """Return start timestamp as datetime."""
        return datetime.fromtimestamp(self.start_timestamp, tz=UTC)

    @property
    def end_datetime(self) -> datetime:
        """Return end timestamp as datetime."""
        return datetime.fromtimestamp(self.end_timestamp, tz=UTC)

    @property
    def duration_seconds(self) -> int:
        """Return job duration in seconds."""
        return self.end_timestamp - self.start_timestamp


class JobLogUrl(BaseModel):
    """Job log URL information."""

    model_config = ConfigDict(extra="ignore")

    id: int
    job_id: int
    name: str
    url: str
    parse_status: str


class FailureClassification(BaseModel):
    """Failure classification type."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    description: str


class OptionCollection(BaseModel):
    """Option collection (build options like opt, debug, etc.)."""

    model_config = ConfigDict(extra="ignore")

    option_collection_hash: str
    options: list[dict[str, str]]


class FailureByBug(BaseModel):
    """A test failure associated with a bug.

    Returned by the /api/failuresbybug/ endpoint, which aggregates
    failures across repositories filtered by bug ID.
    """

    model_config = ConfigDict(extra="ignore")

    push_time: str
    platform: str
    revision: str
    test_suite: str
    tree: str
    build_type: str
    job_id: int
    bug_id: int
    machine_name: str
    lines: list[str]
    task_id: str


class TextLogError(BaseModel):
    """An error line from a job's log.

    Returned by the /api/project/{project}/jobs/{job_id}/text_log_errors/ endpoint.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    line: str
    line_number: int
    new_failure: bool
    job: int


class BugMatch(BaseModel):
    """A bug that matches an error line."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    status: str = ""
    resolution: str = ""
    summary: str
    dupe_of: int | None = None
    crash_signature: str = ""
    keywords: str = ""
    whiteboard: str = ""
    internal_id: int | None = None
    occurrences: int | None = None


class BugSuggestion(BaseModel):
    """Bug suggestions for a failure line.

    Returned by the /api/project/{project}/jobs/{job_id}/bug_suggestions/ endpoint.
    """

    model_config = ConfigDict(extra="ignore")

    search: str
    search_terms: list[str]
    path_end: str | None = None
    bugs: dict[str, list[BugMatch]]
    line_number: int
    counter: int | None = None
    failure_new_in_rev: bool = False
