# utils.py

from datetime import datetime, timezone, timedelta 
from collections import defaultdict
from typing import Union, Final, Any
import config
import math


def get_memory_cost(response_size_bytes: int) -> float:
    """Calculates the accurate memory cost for a single request based on response size tiers."""
    for max_bytes, cost in config.MEMORY_COST_TIERS_BYTES:
        if response_size_bytes <= max_bytes:
            return cost
            
    # Fallback to highest tier cost if somehow larger than the max defined tier
    return config.MEMORY_COST_TIERS_BYTES[-1][1] 

def parse_timestamp(ts_str: str) -> Union[datetime, None]:
    """Parses a timestamp string into a timezone-aware datetime object (Fix for Pylance/Python < 3.10)."""
    try:
        dt = datetime.strptime(ts_str, config.TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None

def validate_log_entry(log: dict) -> Union[dict, None]:
    """
    Validates and cleans a single log entry, returning None if invalid.
    """
    required_fields: Final[list[str]] = [
        "timestamp", "endpoint", "method", "response_time_ms", 
        "status_code", "user_id", "request_size_bytes", "response_size_bytes"
    ]
    
    for field in required_fields:
        if field not in log:
            return None 

    # Validate response time and sizes (must be non-negative integers)
    try:
        log["response_time_ms"] = int(log["response_time_ms"])
        log["request_size_bytes"] = int(log["request_size_bytes"])
        log["response_size_bytes"] = int(log["response_size_bytes"])
        
        if log["response_time_ms"] < 0 or log["request_size_bytes"] < 0 or log["response_size_bytes"] < 0:
            return None
    except ValueError:
        return None
        
    # Validate timestamp
    log_dt = parse_timestamp(log["timestamp"])
    if not log_dt:
        return None
        
    log["timestamp"] = log_dt # Store datetime object
    log["status_code"] = int(log["status_code"]) # Ensure status code is int

    return log

def calculate_empty_cost() -> dict:
     return {
        "total_cost_usd": 0.0,
        "cost_breakdown": {
            "request_costs": 0.0,
            "execution_costs": 0.0,
            "memory_costs": 0.0
        },
        "cost_by_endpoint": [],
        "optimization_potential_usd": 0.0 # Remains zero as default/placeholder
    }

def create_empty_report() -> dict:
    """Generates the expected output structure for an empty input array."""
    now = datetime.now(timezone.utc).strftime(config.TIMESTAMP_FORMAT)
    return {
        "summary": {
            "total_requests": 0,
            "time_range": {"start": now, "end": now},
            "avg_response_time_ms": 0.0,
            "error_rate_percentage": 0.0
        },
        "endpoint_stats": [],
        "performance_issues": [],
        "recommendations": ["No logs received for analysis."],
        "hourly_distribution": {},
        "top_users_by_requests": [],
        "cost_analysis": calculate_empty_cost(),
        "rate_limit_violations": {"user_violations": [], "endpoint_violations": [], "total_violations": 0} # NEW FIELD
    }

def calculate_summary(total_requests: int, total_response_time: float, error_count: int, timestamps: list[datetime]) -> dict:
    """Calculates the overall summary statistics."""
    if total_requests == 0:
        return create_empty_report()["summary"]
        
    avg_response_time = total_response_time / total_requests
    error_rate = (error_count / total_requests) * 100
    
    # FIX: Correct sorting of datetime objects (removed .str)
    timestamps.sort() 
    start_time = timestamps[0].strftime(config.TIMESTAMP_FORMAT) if timestamps else ""
    end_time = timestamps[-1].strftime(config.TIMESTAMP_FORMAT) if timestamps else ""

    return {
        "total_requests": total_requests,
        "time_range": {"start": start_time, "end": end_time},
        "avg_response_time_ms": round(avg_response_time, 2),
        "error_rate_percentage": round(error_rate, 2)
    }

def get_top_users(user_requests: dict[str, int], top_n: int) -> list[dict]:
    """Returns the top N users by request count."""
    sorted_users = sorted(user_requests.items(), key=lambda item: item[1], reverse=True)
    
    top_users = []
    for user_id, request_count in sorted_users[:top_n]:
        top_users.append({"user_id": user_id, "request_count": request_count})
        
    return top_users

def calculate_endpoint_stats(endpoint_data: dict) -> list[dict]:
    """Calculates statistics for each endpoint."""
    endpoint_stats_list = []
    for endpoint, data in endpoint_data.items():
        count = data['count']
        if count == 0: continue
        
        avg_time = data['total_time'] / count
        error_rate = (data['errors'] / count) * 100
        
        # Find most common status code
        most_common_status = max(data['statuses'], key=data['statuses'].get) if data['statuses'] else 0

        endpoint_stats_list.append({
            "endpoint": endpoint,
            "request_count": count,
            "avg_response_time_ms": round(avg_time, 2),
            "slowest_request_ms": data['max_time'],
            "fastest_request_ms": data['min_time'] if data['min_time'] != float('inf') else 0,
            "error_count": data['errors'],
            "error_rate_percentage": round(error_rate, 2),
            "most_common_status": most_common_status,
            "total_response_time_ms": data['total_time'],
            "total_memory_cost": data['total_memory_cost'], 
            "is_get_count": data['is_get'] 
        })
        
    return endpoint_stats_list

def detect_performance_issues(endpoint_stats: list[dict]) -> list[dict]:
    """Identifies slow endpoints and high error rate endpoints based on config thresholds."""
    issues = []
    
    for stats in endpoint_stats:
        endpoint = stats["endpoint"]
        avg_time = stats["avg_response_time_ms"]
        err_rate = stats["error_rate_percentage"]
        
        # 1. Slow Endpoint Detection
        severity_slow = None
        threshold_ms = 0
        
        if avg_time > config.THRESHOLD_SLOW_CRITICAL:
            severity_slow = "critical"
            threshold_ms = config.THRESHOLD_SLOW_CRITICAL
        elif avg_time > config.THRESHOLD_SLOW_HIGH:
            severity_slow = "high"
            threshold_ms = config.THRESHOLD_SLOW_HIGH
        elif avg_time > config.THRESHOLD_SLOW_MEDIUM:
            severity_slow = "medium"
            threshold_ms = config.THRESHOLD_SLOW_MEDIUM
            
        if severity_slow:
            issues.append({
                "type": "slow_endpoint",
                "endpoint": endpoint,
                "avg_response_time_ms": round(avg_time, 2),
                "threshold_ms": threshold_ms,
                "severity": severity_slow
            })

        # 2. High Error Rate Detection
        severity_error = None
        threshold_rate = 0.0
        
        if err_rate > config.THRESHOLD_ERROR_CRITICAL:
            severity_error = "critical"
            threshold_rate = config.THRESHOLD_ERROR_CRITICAL
        elif err_rate > config.THRESHOLD_ERROR_HIGH:
            severity_error = "high"
            threshold_rate = config.THRESHOLD_ERROR_HIGH
        elif err_rate > config.THRESHOLD_ERROR_MEDIUM:
            severity_error = "medium"
            threshold_rate = config.THRESHOLD_ERROR_MEDIUM
            
        if severity_error:
            issues.append({
                "type": "high_error_rate",
                "endpoint": endpoint,
                "error_rate_percentage": round(err_rate, 2),
                "threshold_percentage": threshold_rate,
                "severity": severity_error
            })
            
    return issues

# --- Advanced Feature A: Cost Estimation Engine (Fixed for Accuracy) ---

def calculate_cost_analysis(endpoint_data: dict, total_requests: int) -> dict:
    """
    Calculates total and per-endpoint serverless execution costs.
    Uses accurate pre-calculated total memory cost from the main log pass.
    """
    if total_requests == 0:
        return calculate_empty_cost()

    total_request_costs = total_requests * config.COST_PER_REQUEST
    total_execution_costs = 0.0
    total_memory_costs = 0.0
    cost_by_endpoint = []

    for endpoint, data in endpoint_data.items():
        if data['count'] == 0: continue
        
        # 1. Execution Cost: (Total response time in ms) * cost per ms
        endpoint_execution_cost = data['total_time'] * config.COST_PER_MS_EXECUTION
        total_execution_costs += endpoint_execution_cost
        
        # 2. Request Cost: (Count) * cost per request
        endpoint_request_cost = data['count'] * config.COST_PER_REQUEST
        
        # 3. Memory Cost: Sum of individual request memory costs (ACCURATE)
        endpoint_memory_cost = data['total_memory_cost']
        total_memory_costs += endpoint_memory_cost
        
        # Total cost for endpoint
        endpoint_total_cost = endpoint_request_cost + endpoint_execution_cost + endpoint_memory_cost
        total_cost_per_request = endpoint_total_cost / data['count']

        cost_by_endpoint.append({
            "endpoint": endpoint,
            "total_cost": round(endpoint_total_cost, 6), # Increased precision to avoid zero rounding issue
            "cost_per_request": round(total_cost_per_request, 6) 
        })

    total_cost = total_request_costs + total_execution_costs + total_memory_costs
    
    return {
        "total_cost_usd": round(total_cost, 2),
        "cost_breakdown": {
            "request_costs": round(total_request_costs, 6),
            "execution_costs": round(total_execution_costs, 6),
            "memory_costs": round(total_memory_costs, 6)
        },
        "cost_by_endpoint": cost_by_endpoint,
        # Optimization potential is added in function.py orchestration layer if needed, default to 0.0 here
        "optimization_potential_usd": 0.0 
    }

# --- Advanced Feature C: Rate Limiting Analysis (NEW) ---

def analyze_rate_limit_violations(validated_logs: list[dict[str, Any]]) -> dict:
    """
    Analyzes log data to detect per-minute and per-hour violations using sliding windows.
    The input logs MUST be sorted chronologically.
    """
    rules = config.RATE_LIMIT_RULES
    
    # Trackers store the timestamps (datetime objects) of recent requests for each key
    # { 'user_id' or 'endpoint': [dt_request_1, dt_request_2, ...] }
    user_tracker = defaultdict(list)
    endpoint_tracker = defaultdict(list)
    
    user_violations: list[dict] = []
    endpoint_violations: list[dict] = []
    
    # Helper to check and prune the tracker
    def check_and_prune(tracker, key, current_time, time_window_seconds, limit_key, violation_list, entity_type):
        
        # 1. Add current request
        tracker[key].append(current_time)
        
        # 2. Prune old requests outside the time window
        cutoff_time = current_time - timedelta(seconds=time_window_seconds)
        # Keep only timestamps STRICTLY greater than the cutoff
        tracker[key] = [ts for ts in tracker[key] if ts > cutoff_time]
        
        actual_count = len(tracker[key])
        limit = rules[entity_type][limit_key]
        
        # 3. Check violation
        if actual_count > limit:
            violation_type = limit_key.replace('requests_', '')
            
            # Simple check to prevent logging a violation for every single request in the same heavy window.
            # We only log it if the last violation for this key/type was NOT the current request time.
            violation_found = False
            for v in violation_list:
                if (entity_type == 'per_user' and v.get('user_id') == key or 
                    entity_type == 'per_endpoint' and v.get('endpoint') == key) and \
                    v['violation_type'] == violation_type:
                    
                    # Check if the violation has already been logged near this timestamp (within 1 second)
                    logged_dt = v['timestamp_dt']
                    if (current_time - logged_dt).total_seconds() < 1:
                        violation_found = True
                        break
            
            if not violation_found:
                violation_entry = {
                    "violation_type": violation_type.replace('_per', '_'),
                    "limit": limit,
                    "actual": actual_count,
                    "timestamp": current_time.strftime(config.TIMESTAMP_FORMAT),
                    "timestamp_dt": current_time # Store datetime object for internal check
                }
                
                if entity_type == 'per_user':
                    violation_entry["user_id"] = key
                    user_violations.append(violation_entry)
                else:
                    violation_entry["endpoint"] = key
                    endpoint_violations.append(violation_entry)
                
    # Loop over all logs and check both user and endpoint limits
    for log in validated_logs:
        dt = log['timestamp']
        user_id = log['user_id']
        endpoint = log['endpoint']
        
        # Per-Minute Limits (60 seconds)
        check_and_prune(user_tracker, user_id, dt, 60, "requests_per_minute", user_violations, 'per_user')
        check_and_prune(endpoint_tracker, endpoint, dt, 60, "requests_per_minute", endpoint_violations, 'per_endpoint')
        
        # Per-Hour Limits (3600 seconds)
        check_and_prune(user_tracker, user_id, dt, 3600, "requests_per_hour", user_violations, 'per_user')
        check_and_prune(endpoint_tracker, endpoint, dt, 3600, "requests_per_hour", endpoint_violations, 'per_endpoint')

    # Clean up the output list for the final report (remove internal timestamp_dt)
    final_user_violations = [{k: v for k, v in item.items() if k != 'timestamp_dt'} for item in user_violations]
    final_endpoint_violations = [{k: v for k, v in item.items() if k != 'timestamp_dt'} for item in endpoint_violations]
    
    return {
        "user_violations": final_user_violations,
        "endpoint_violations": final_endpoint_violations,
        "total_violations": len(final_user_violations) + len(final_endpoint_violations)
    }

def generate_recommendations(performance_issues: list[dict], rate_limit_violations: dict) -> list[str]:
    """Generates actionable recommendations based on analysis (Updated for Rate Limits)."""
    recommendations = []
    
    # 1. Recommendations from Performance Issues (Prioritized)
    for issue in performance_issues:
        if issue["type"] == "slow_endpoint":
            recommendations.append(
                f"Investigate {issue['endpoint']} performance (avg {issue['avg_response_time_ms']}ms exceeds {issue['threshold_ms']}ms threshold)."
            )
        elif issue["type"] == "high_error_rate":
            recommendations.append(
                f"Alert: {issue['endpoint']} has {issue['error_rate_percentage']}% error rate. Severity: {issue['severity'].upper()}."
            )
            
    # 2. Recommendations from Rate Limit Violations
    if rate_limit_violations["total_violations"] > 0:
        recommendations.append(
            f"ALERT: Detected {rate_limit_violations['total_violations']} rate limit violations. Review top offenders."
        )
        
        # Highlight top 3 unique violating users
        violating_users = {v['user_id'] for v in rate_limit_violations['user_violations']}
        if violating_users:
            top_violators = ', '.join(list(violating_users)[:3])
            recommendations.append(f"Immediate action: Review users [{top_violators}] for potential abuse or misconfiguration.")

    return recommendations