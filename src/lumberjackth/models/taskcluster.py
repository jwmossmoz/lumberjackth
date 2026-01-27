"""Taskcluster-related Pydantic models for Treeherder API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TaskclusterMetadata(BaseModel):
    """Taskcluster metadata for a job."""

    model_config = ConfigDict(extra="ignore")

    task_id: str
    retry_id: int = 0

    @property
    def task_url(self) -> str:
        """Return URL to the Taskcluster task."""
        return f"https://firefox-ci-tc.services.mozilla.com/tasks/{self.task_id}"

    @property
    def task_url_with_retry(self) -> str:
        """Return URL to the specific run of the task."""
        return (
            f"https://firefox-ci-tc.services.mozilla.com/tasks/{self.task_id}/runs/{self.retry_id}"
        )
