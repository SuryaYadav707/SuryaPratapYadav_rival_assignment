import pytest
import os
import json
from function import analyze_api_logs  # Use the correct function

# ---------------------- FIXTURE ---------------------- #

@pytest.fixture(scope="module")
def sample_test_logs():
    """Loads the test data."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'test_data', 'sample_small.json')

    if not os.path.exists(file_path):
        pytest.fail(f"Test data file not found: {file_path}")

    with open(file_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def report(sample_test_logs):
    return analyze_api_logs(sample_test_logs)

# ---------------------- TESTS ---------------------- #

def test_summary_stats(report):
    """Validate total requests and average response time."""
    total_requests = report['summary']['total_requests']
    assert total_requests > 0

    # Use total_response_time as in function.py output
    total_time = sum(ep['total_response_time_ms'] for ep in report['endpoint_stats'])
    expected_avg = total_time / total_requests

    assert report['summary']['avg_response_time_ms'] == pytest.approx(
        expected_avg, abs=1e-6
    )


def test_error_count(report):
    """Check error counts match endpoint stats."""
    total_errors = sum(ep['error_count'] for ep in report['endpoint_stats'])
    if 'total_errors' in report['summary']:
        # optional check if summary includes it
        assert report['summary']['total_errors'] == total_errors
    else:
        assert total_errors >= 0  # at least non-negative


def test_endpoint_presence(report):
    """Ensure endpoint_stats is a list and optionally contains endpoints."""
    assert isinstance(report["endpoint_stats"], list)
    # Only check length if the report actually has logs
    total_requests = report['summary']['total_requests']
    if total_requests > 0:
        assert len(report["endpoint_stats"]) > 0


def test_hourly_distribution(report):
    """Hourly distribution should be dict."""
    dist = report["hourly_distribution"]
    assert isinstance(dist, dict)
    # basic check: keys like "10:00" exist
    for k, v in dist.items():
        assert isinstance(k, str)
        assert isinstance(v, int)


def test_performance_issues(report):
    """Performance issues should be a list of dicts."""
    issues = report["performance_issues"]
    assert isinstance(issues, list)
    for item in issues:
        for key in ["type", "endpoint", "severity"]:
            assert key in item


def test_cost_analysis_structure(report):
    """Verify cost analysis contains required keys."""
    cost = report["cost_analysis"]
    for key in ["total_cost_usd", "cost_breakdown", "cost_by_endpoint", "optimization_potential_usd"]:
        assert key in cost


def test_cost_breakdown(report):
    """Check cost breakdown keys."""
    breakdown = report["cost_analysis"]["cost_breakdown"]
    for key in ["execution_costs", "memory_costs", "request_costs"]:
        assert key in breakdown


def test_rate_limit_violations(report):
    """Rate limit violations exist as a dict with expected keys."""
    rl = report.get("rate_limit_violations")
    assert isinstance(rl, dict)
    for key in ["user_violations", "endpoint_violations", "total_violations"]:
        assert key in rl


def test_recommendations(report):
    """Recommendations exist as a list of strings."""
    recs = report.get("recommendations", [])
    assert isinstance(recs, list)
    for r in recs:
        assert isinstance(r, str)


def test_final_structure(report):
    """Ensure final report contains all main sections."""
    expected_keys = {
        "summary",
        "endpoint_stats",
        "hourly_distribution",
        "performance_issues",
        "cost_analysis",
        "rate_limit_violations",
        "recommendations",
        "top_users_by_requests",
    }
    assert set(report.keys()) == expected_keys
