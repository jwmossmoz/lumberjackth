"""Tests for the TreeherderClient."""

from __future__ import annotations

import httpx
import pytest
import respx

from lumberjackth import TreeherderClient
from lumberjackth.exceptions import TreeherderAPIError, TreeherderNotFoundError


class TestTreeherderClient:
    """Tests for TreeherderClient."""

    def test_init_default_server(self) -> None:
        """Test client initializes with default server."""
        client = TreeherderClient()
        assert client.server_url == "https://treeherder.mozilla.org"

    def test_init_custom_server(self) -> None:
        """Test client initializes with custom server."""
        client = TreeherderClient(server_url="https://custom.example.com/")
        assert client.server_url == "https://custom.example.com"

    def test_build_url_no_project(self) -> None:
        """Test URL building without project."""
        client = TreeherderClient()
        url = client._build_url("repository")
        assert url == "https://treeherder.mozilla.org/api/repository/"

    def test_build_url_with_project(self) -> None:
        """Test URL building with project."""
        client = TreeherderClient()
        url = client._build_url("jobs", project="mozilla-central")
        assert url == "https://treeherder.mozilla.org/api/project/mozilla-central/jobs/"


class TestClientContextManager:
    """Tests for client context manager."""

    def test_sync_context_manager(self) -> None:
        """Test synchronous context manager."""
        with TreeherderClient() as client:
            assert client._sync_client is None  # Not created until used

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        """Test asynchronous context manager."""
        async with TreeherderClient() as client:
            assert client._async_client is None  # Not created until used


class TestRepositoryEndpoints:
    """Tests for repository endpoints."""

    @respx.mock
    def test_get_repositories(self) -> None:
        """Test fetching repositories."""
        mock_data = [
            {
                "id": 1,
                "repository_group": {"name": "development", "description": "Dev repos"},
                "name": "mozilla-central",
                "dvcs_type": "hg",
                "url": "https://hg.mozilla.org/mozilla-central",
                "branch": None,
                "codebase": "gecko",
                "description": "Main development",
                "active_status": "active",
                "life_cycle_order": 1,
                "performance_alerts_enabled": True,
                "expire_performance_data": False,
                "is_try_repo": False,
                "tc_root_url": "https://firefox-ci-tc.services.mozilla.com",
            }
        ]

        respx.get("https://treeherder.mozilla.org/api/repository/").mock(
            return_value=httpx.Response(200, json=mock_data)
        )

        with TreeherderClient() as client:
            repos = client.get_repositories()

        assert len(repos) == 1
        assert repos[0].name == "mozilla-central"
        assert repos[0].dvcs_type == "hg"
        assert repos[0].is_try_repo is False


class TestPushEndpoints:
    """Tests for push endpoints."""

    @respx.mock
    def test_get_pushes(self) -> None:
        """Test fetching pushes."""
        mock_data = {
            "results": [
                {
                    "id": 12345,
                    "revision": "abc123def456",
                    "author": "test@example.com",
                    "revisions": [],
                    "revision_count": 1,
                    "push_timestamp": 1700000000,
                    "repository_id": 1,
                }
            ]
        }

        respx.get("https://treeherder.mozilla.org/api/project/mozilla-central/push/").mock(
            return_value=httpx.Response(200, json=mock_data)
        )

        with TreeherderClient() as client:
            pushes = client.get_pushes("mozilla-central", count=1)

        assert len(pushes) == 1
        assert pushes[0].id == 12345
        assert pushes[0].revision == "abc123def456"


class TestJobEndpoints:
    """Tests for job endpoints."""

    @respx.mock
    def test_get_jobs(self) -> None:
        """Test fetching jobs."""
        mock_data = {
            "results": [
                {
                    "id": 1,
                    "job_guid": "test-guid/0",
                    "push_id": 12345,
                    "result_set_id": 12345,
                    "build_architecture": "x86_64",
                    "build_os": "linux",
                    "build_platform": "linux64",
                    "build_platform_id": 1,
                    "build_system_type": "taskcluster",
                    "job_group_id": 1,
                    "job_group_name": "Mochitest",
                    "job_group_symbol": "M",
                    "job_group_description": "",
                    "job_type_id": 1,
                    "job_type_name": "test-linux64/opt-mochitest-1",
                    "job_type_symbol": "1",
                    "job_type_description": "",
                    "machine_name": "test-machine",
                    "machine_platform_architecture": "x86_64",
                    "machine_platform_os": "linux",
                    "platform": "linux64",
                    "platform_option": "opt",
                    "option_collection_hash": "abc123",
                    "state": "completed",
                    "result": "success",
                    "failure_classification_id": 1,
                    "tier": 1,
                    "submit_timestamp": 1700000000,
                    "start_timestamp": 1700000100,
                    "end_timestamp": 1700000500,
                    "last_modified": "2023-11-14T00:00:00",
                    "reason": "scheduled",
                    "who": "test@example.com",
                    "ref_data_name": "test",
                    "signature": "sig123",
                    "task_id": "task123",
                    "retry_id": 0,
                }
            ]
        }

        respx.get("https://treeherder.mozilla.org/api/project/mozilla-central/jobs/").mock(
            return_value=httpx.Response(200, json=mock_data)
        )

        with TreeherderClient() as client:
            jobs = client.get_jobs("mozilla-central", count=1)

        assert len(jobs) == 1
        assert jobs[0].job_guid == "test-guid/0"
        assert jobs[0].result == "success"
        assert jobs[0].task_id == "task123"


class TestErrorHandling:
    """Tests for error handling."""

    @respx.mock
    def test_404_raises_not_found(self) -> None:
        """Test 404 response raises TreeherderNotFoundError."""
        respx.get("https://treeherder.mozilla.org/api/repository/").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        with TreeherderClient() as client:
            with pytest.raises(TreeherderNotFoundError):
                client.get_repositories()

    @respx.mock
    def test_500_raises_api_error(self) -> None:
        """Test 500 response raises TreeherderAPIError."""
        respx.get("https://treeherder.mozilla.org/api/repository/").mock(
            return_value=httpx.Response(500, json={"detail": "Server error"})
        )

        with TreeherderClient() as client:
            with pytest.raises(TreeherderAPIError):
                client.get_repositories()
