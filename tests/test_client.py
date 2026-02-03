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


class TestOptionCollectionEndpoints:
    """Tests for option collection endpoints."""

    @respx.mock
    def test_get_option_collection_hash(self) -> None:
        """Test fetching option collection hashes."""
        mock_data = [
            {
                "option_collection_hash": "abc123",
                "options": [{"name": "opt"}],
            },
            {
                "option_collection_hash": "def456",
                "options": [{"name": "debug"}, {"name": "asan"}],
            },
        ]

        respx.get("https://treeherder.mozilla.org/api/optioncollectionhash/").mock(
            return_value=httpx.Response(200, json=mock_data)
        )

        with TreeherderClient() as client:
            collections = client.get_option_collection_hash()

        assert len(collections) == 2
        assert collections[0].option_collection_hash == "abc123"
        assert collections[0].options == [{"name": "opt"}]
        assert collections[1].option_collection_hash == "def456"


class TestFailuresByBugEndpoint:
    """Tests for failures by bug endpoint."""

    @respx.mock
    def test_get_failures_by_bug(self) -> None:
        """Test fetching failures by bug ID."""
        mock_data = [
            {
                "push_time": "2026-01-28 14:44:08",
                "platform": "windows11-64-24h2",
                "revision": "abc123",
                "test_suite": "opt-mochitest-browser-chrome-1",
                "tree": "autoland",
                "build_type": "asan",
                "job_id": 12345,
                "bug_id": 2012615,
                "machine_name": "vm-test",
                "lines": ["TEST-UNEXPECTED-FAIL | test.js | Test timed out"],
                "task_id": "abc123def",
            }
        ]

        respx.get("https://treeherder.mozilla.org/api/failuresbybug/").mock(
            return_value=httpx.Response(200, json=mock_data)
        )

        with TreeherderClient() as client:
            failures = client.get_failures_by_bug(
                2012615, startday="2026-01-27", endday="2026-01-28", tree="autoland"
            )

        assert len(failures) == 1
        assert failures[0].bug_id == 2012615
        assert failures[0].platform == "windows11-64-24h2"
        assert failures[0].build_type == "asan"
        assert len(failures[0].lines) == 1


class TestTextLogErrorsEndpoint:
    """Tests for text log errors endpoint."""

    @respx.mock
    def test_get_text_log_errors(self) -> None:
        """Test fetching text log errors for a job."""
        mock_data = [
            {
                "id": 12345,
                "line": "TEST-UNEXPECTED-FAIL | test.js | Test timed out",
                "line_number": 100,
                "new_failure": True,
                "job": 54321,
            }
        ]

        respx.get(
            "https://treeherder.mozilla.org/api/project/autoland/jobs/54321/text_log_errors/"
        ).mock(return_value=httpx.Response(200, json=mock_data))

        with TreeherderClient() as client:
            errors = client.get_text_log_errors("autoland", 54321)

        assert len(errors) == 1
        assert errors[0].id == 12345
        assert errors[0].new_failure is True
        assert errors[0].line_number == 100


class TestBugSuggestionsEndpoint:
    """Tests for bug suggestions endpoint."""

    @respx.mock
    def test_get_bug_suggestions(self) -> None:
        """Test fetching bug suggestions for a job."""
        mock_data = [
            {
                "search": "TEST-UNEXPECTED-FAIL | test.js | Test timed out",
                "search_terms": ["test.js"],
                "path_end": "test.js",
                "bugs": {
                    "open_recent": [
                        {
                            "id": 123456,
                            "status": "NEW",
                            "resolution": "",
                            "summary": "Intermittent test.js failure",
                            "dupe_of": None,
                            "crash_signature": "",
                            "keywords": "",
                            "whiteboard": "",
                        }
                    ],
                    "all_others": [],
                },
                "line_number": 100,
                "counter": 1,
                "failure_new_in_rev": False,
            }
        ]

        respx.get(
            "https://treeherder.mozilla.org/api/project/autoland/jobs/54321/bug_suggestions/"
        ).mock(return_value=httpx.Response(200, json=mock_data))

        with TreeherderClient() as client:
            suggestions = client.get_bug_suggestions("autoland", 54321)

        assert len(suggestions) == 1
        assert suggestions[0].search_terms == ["test.js"]
        assert suggestions[0].line_number == 100
        assert len(suggestions[0].bugs["open_recent"]) == 1
        assert suggestions[0].bugs["open_recent"][0].id == 123456


class TestSimilarJobsEndpoint:
    """Tests for similar jobs endpoint."""

    @respx.mock
    def test_get_similar_jobs(self) -> None:
        """Test fetching similar jobs for a job."""
        mock_data = {
            "results": [
                {
                    "id": 546767320,
                    "job_guid": "52fc3bdd-b53e-42a9-b272-c6c2717ca875/0",
                    "push_id": 1822012,
                    "result_set_id": 1822012,
                    "build_architecture": "-",
                    "build_os": "-",
                    "build_platform": "windows11-64-24h2",
                    "build_platform_id": 1002,
                    "build_system_type": "taskcluster",
                    "job_group_id": 448,
                    "job_group_name": "Mochitests",
                    "job_group_symbol": "M",
                    "job_group_description": "",
                    "job_type_id": 390669,
                    "job_type_name": "test-windows11-64-24h2-asan/opt-mochitest-browser-chrome-14",
                    "job_type_symbol": "bc14",
                    "job_type_description": "",
                    "machine_name": "vm-test",
                    "machine_platform_architecture": "-",
                    "machine_platform_os": "-",
                    "platform": "windows11-64-24h2",
                    "platform_option": "asan",
                    "option_collection_hash": "abc123",
                    "state": "completed",
                    "result": "success",
                    "failure_classification_id": 1,
                    "tier": 1,
                    "submit_timestamp": 1770084882,
                    "start_timestamp": 1770086211,
                    "end_timestamp": 1770087584,
                    "last_modified": "2026-02-03T02:59:44.644439",
                    "reason": "scheduled",
                    "who": "test@example.com",
                    "ref_data_name": "abc123",
                    "signature": "abc123",
                    "task_id": "Uvw73bU-QqmycsbCcXyodQ",
                    "retry_id": 0,
                },
            ],
            "meta": {"offset": 0, "count": 1, "repository": "try"},
        }

        respx.get(
            "https://treeherder.mozilla.org/api/project/try/jobs/546769427/similar_jobs/"
        ).mock(return_value=httpx.Response(200, json=mock_data))

        with TreeherderClient() as client:
            similar = client.get_similar_jobs("try", 546769427, count=5)

        assert len(similar) == 1
        assert similar[0].id == 546767320
        assert similar[0].result == "success"
        assert "mochitest-browser-chrome-14" in similar[0].job_type_name
        assert similar[0].task_id == "Uvw73bU-QqmycsbCcXyodQ"


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


class TestJobLogEndpoints:
    """Tests for job log endpoints."""

    @respx.mock
    def test_get_job_log(self) -> None:
        """Test fetching job log content."""
        log_urls_mock = [
            {
                "id": 1,
                "job_id": 12345,
                "name": "live_backing_log",
                "url": "https://example.com/log.txt",
                "parse_status": "parsed",
            }
        ]
        log_content = "Line 1: Starting test\nLine 2: Running test\nLine 3: Test passed"

        respx.get("https://treeherder.mozilla.org/api/project/autoland/job-log-url/").mock(
            return_value=httpx.Response(200, json=log_urls_mock)
        )

        respx.get("https://example.com/log.txt").mock(
            return_value=httpx.Response(200, text=log_content)
        )

        with TreeherderClient() as client:
            result = client.get_job_log("autoland", 12345)

        assert result == log_content
        assert "Line 1" in result

    @respx.mock
    def test_get_job_log_not_found(self) -> None:
        """Test get_job_log raises error when log name not found."""
        log_urls_mock = [
            {
                "id": 1,
                "job_id": 12345,
                "name": "errorsummary_json",
                "url": "https://example.com/errors.json",
                "parse_status": "parsed",
            }
        ]

        respx.get("https://treeherder.mozilla.org/api/project/autoland/job-log-url/").mock(
            return_value=httpx.Response(200, json=log_urls_mock)
        )

        with TreeherderClient() as client:
            with pytest.raises(TreeherderNotFoundError) as exc_info:
                client.get_job_log("autoland", 12345, log_name="live_backing_log")

        assert "live_backing_log" in str(exc_info.value)

    @respx.mock
    def test_search_job_log(self) -> None:
        """Test searching job log for patterns."""
        log_urls_mock = [
            {
                "id": 1,
                "job_id": 12345,
                "name": "live_backing_log",
                "url": "https://example.com/log.txt",
                "parse_status": "parsed",
            }
        ]
        log_content = """Line 1: Starting test
Line 2: TEST-UNEXPECTED-FAIL | test.js | Assertion failed
Line 3: Running cleanup
Line 4: TEST-UNEXPECTED-FAIL | other.js | Timeout
Line 5: Test finished"""

        respx.get("https://treeherder.mozilla.org/api/project/autoland/job-log-url/").mock(
            return_value=httpx.Response(200, json=log_urls_mock)
        )

        respx.get("https://example.com/log.txt").mock(
            return_value=httpx.Response(200, text=log_content)
        )

        with TreeherderClient() as client:
            matches = client.search_job_log("autoland", 12345, "TEST-UNEXPECTED-FAIL")

        assert len(matches) == 2
        assert matches[0]["line_number"] == 2
        assert "Assertion failed" in matches[0]["line"]
        assert matches[1]["line_number"] == 4
        assert "Timeout" in matches[1]["line"]

    @respx.mock
    def test_search_job_log_with_context(self) -> None:
        """Test searching job log with context lines."""
        log_urls_mock = [
            {
                "id": 1,
                "job_id": 12345,
                "name": "live_backing_log",
                "url": "https://example.com/log.txt",
                "parse_status": "parsed",
            }
        ]
        log_content = """Line 1: Before
Line 2: ERROR here
Line 3: After"""

        respx.get("https://treeherder.mozilla.org/api/project/autoland/job-log-url/").mock(
            return_value=httpx.Response(200, json=log_urls_mock)
        )

        respx.get("https://example.com/log.txt").mock(
            return_value=httpx.Response(200, text=log_content)
        )

        with TreeherderClient() as client:
            matches = client.search_job_log("autoland", 12345, "ERROR", context_lines=1)

        assert len(matches) == 1
        assert matches[0]["line_number"] == 2
        assert "context" in matches[0]
        assert len(matches[0]["context"]) == 3
        assert "Line 1: Before" in matches[0]["context"]
        assert "Line 3: After" in matches[0]["context"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_job_log_async(self) -> None:
        """Test fetching job log content asynchronously."""
        log_urls_mock = [
            {
                "id": 1,
                "job_id": 12345,
                "name": "live_backing_log",
                "url": "https://example.com/log.txt",
                "parse_status": "parsed",
            }
        ]
        log_content = "Async log content"

        respx.get("https://treeherder.mozilla.org/api/project/autoland/job-log-url/").mock(
            return_value=httpx.Response(200, json=log_urls_mock)
        )

        respx.get("https://example.com/log.txt").mock(
            return_value=httpx.Response(200, text=log_content)
        )

        async with TreeherderClient() as client:
            result = await client.get_job_log_async("autoland", 12345)

        assert result == log_content
