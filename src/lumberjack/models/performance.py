"""Performance-related Pydantic models for Treeherder API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PerformanceFramework(BaseModel):
    """Performance testing framework (e.g., talos, build_metrics)."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class SeriesSignature(BaseModel):
    """Performance series signature identifying a specific test."""

    model_config = ConfigDict(extra="ignore")

    id: int
    framework_id: int
    signature_hash: str
    machine_platform: str
    suite: str
    test: str | None = None
    lower_is_better: bool
    has_subtests: bool
    option_collection_hash: str
    tags: list[str] = []
    extra_options: list[str] = []
    measurement_unit: str | None = None
    suite_public_name: str | None = None
    test_public_name: str | None = None


class TaskclusterMetadataRef(BaseModel):
    """Taskcluster task reference in performance data."""

    model_config = ConfigDict(extra="ignore")

    task_id: str
    retry_id: int


class BackfillRecord(BaseModel):
    """Backfill record for performance alerts."""

    model_config = ConfigDict(extra="ignore")

    context: str | None = None
    status: int | None = None
    total_actions_triggered: int | None = None
    total_backfills_failed: int | None = None
    total_backfills_successful: int | None = None
    total_backfills_in_progress: int | None = None


class PerformanceAlert(BaseModel):
    """A performance alert indicating a regression or improvement."""

    model_config = ConfigDict(extra="ignore")

    id: int
    status: int
    series_signature: SeriesSignature
    taskcluster_metadata: TaskclusterMetadataRef | None = None
    prev_taskcluster_metadata: TaskclusterMetadataRef | None = None
    profile_url: str | None = None
    prev_profile_url: str | None = None
    is_regression: bool
    prev_value: float
    new_value: float
    t_value: float
    amount_abs: float
    amount_pct: float
    summary_id: int
    related_summary_id: int | None = None
    manually_created: bool
    classifier: str | None = None
    starred: bool
    classifier_email: str | None = None
    backfill_record: BackfillRecord | None = None

    @property
    def change_description(self) -> str:
        """Human-readable description of the change."""
        direction = "regression" if self.is_regression else "improvement"
        return f"{self.amount_pct:.1f}% {direction} ({self.prev_value:.2f} -> {self.new_value:.2f})"


class PerformanceAlertSummary(BaseModel):
    """Summary of performance alerts for a push."""

    model_config = ConfigDict(extra="ignore")

    id: int
    push_id: int
    prev_push_id: int | None = None
    original_revision: str | None = None
    created: datetime
    first_triaged: datetime | None = None
    triage_due_date: datetime | None = None
    repository: str
    framework: int
    alerts: list[PerformanceAlert] = []

    @property
    def regression_count(self) -> int:
        """Count of regression alerts."""
        return sum(1 for a in self.alerts if a.is_regression)

    @property
    def improvement_count(self) -> int:
        """Count of improvement alerts."""
        return sum(1 for a in self.alerts if not a.is_regression)
