# tests/test_edge_cases.py

import pytest
from datetime import datetime
from collections import defaultdict
import config
from function import analyze_api_logs

# --- Mocks and Helpers ---

# Helper to generate a basic valid log entry
def generate_log(timestamp, endpoint, status_code, time_ms, user_id="user_a", size_bytes=500):
    return {
        "timestamp": timestamp, 
        "endpoint": endpoint, 
        "method": "GET", 
        "response_time_ms": time_ms, 
        "status_code": status_code, 
        "user_id": user_id, 
        "request_size_bytes": 100, 
        "response_size_bytes": size_bytes
    }

# --- Fixtures ---

@pytest.fixture
def empty_logs():
    return []

@pytest.fixture
def invalid_logs():
    return [
        {"timestamp": "INVALID_TIME", "endpoint": "/a", "status_code": 200, "user_id": "u1", "response_time_ms": 100, "response_size_bytes": 100, "request_size_bytes": 100},
        {"endpoint": "/b", "status_code": 200, "user_id": "u2", "response_time_ms": 100, "response_size_bytes": 100, "request_size_bytes": 100, "timestamp": "2025-01-01T00:00:00Z"},
        generate_log("2025-01-01T00:00:01Z", "/c", 200, -100), # Negative time
        generate_log("2025-01-01T00:00:02Z", "/d", "200a", 100), # Non-numeric status code (Tests the fix in utils.py)
    ]

@pytest.fixture
def single_error_log():
    # A single log with a 500 status to test error rate logic
    return [generate_log("2025-01-01T00:00:00Z", "/error", 500, 100, size_bytes=10000)]

# --- Tests ---

def test_empty_log_input(empty_logs):
    """Test analysis function with an empty list."""
    report = analyze_api_logs(empty_logs)
    assert report['summary']['total_requests'] == 0
    assert report['recommendations'][0] == "No logs received for analysis."
    assert report['cost_analysis']['total_cost_usd'] == 0.0
    assert report['rate_limit_violations']['total_violations'] == 0

def test_invalid_log_handling(invalid_logs):
    """Test that invalid logs are correctly skipped and the report is not empty. (FIXED)"""
    valid_log = generate_log("2025-01-01T00:00:03Z", "/valid", 200, 100)
    logs = invalid_logs + [valid_log]
    report = analyze_api_logs(logs)
    
    # Only the single valid log should be processed
    assert report['summary']['total_requests'] == 1
    assert report['endpoint_stats'][0]['endpoint'] == "/valid"
    
    # FIX: Assert that the recommendations list is empty, confirming no issues were flagged 
    # and the default "No logs" message was not returned.
    assert report['recommendations'] == []

def test_single_error_log(single_error_log):
    """Test 100% error rate calculation and optimization potential."""
    report = analyze_api_logs(single_error_log)
    assert report['summary']['total_requests'] == 1
    assert report['summary']['error_rate_percentage'] == 100.0
    
    # Cost check (1 request, 100ms time, 10KB size)
    cost = 1 * config.COST_PER_REQUEST + 100 * config.COST_PER_MS_EXECUTION + config.MEMORY_COST_TIERS_BYTES[1][1]
    
    assert report['cost_analysis']['cost_by_endpoint'][0]['cost_per_request'] == pytest.approx(cost)
    # Optimization potential should equal the total cost of this single error request
    assert report['cost_analysis']['optimization_potential_usd'] == pytest.approx(cost, abs=1e-2)

def test_time_range_handling():
    """Test that time range is correctly calculated and formatted."""
    logs = [
        generate_log("2025-01-01T10:30:00Z", "/fast", 200, 50),
        generate_log("2025-01-01T10:30:05Z", "/slow", 200, 1500), # 5 seconds later
        generate_log("2025-01-01T10:30:01Z", "/mid", 200, 100),
    ]
    report = analyze_api_logs(logs)
    
    assert report['summary']['time_range']['start'] == "2025-01-01T10:30:00Z"
    assert report['summary']['time_range']['end'] == "2025-01-01T10:30:05Z"
    assert report['summary']['total_requests'] == 3