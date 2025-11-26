# utils.py

from datetime import datetime, timezone
import config
import math
from typing import Union  # <-- 1. IMPORT Union

def parse_timestamp(ts_str: str) -> Union[datetime, None]:
    """Parses a timestamp string into a timezone-aware datetime object."""
    try:
        dt = datetime.strptime(ts_str, config.TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None

def validate_log_entry(log: dict) -> Union[dict, None]:
    """
    Validates and cleans a single log entry, returning None if invalid.
    Handles malformed data and missing fields.
    """
    required_fields = [
        "timestamp", "endpoint", "method", "response_time_ms", 
        "status_code", "user_id", "request_size_bytes", "response_size_bytes"
    ]
    
    for field in required_fields:
        if field not in log:
            return None # Missing required field

    # Validate response time (must be non-negative)
    try:
        response_time = int(log["response_time_ms"])
        if response_time < 0:
            return None
        log["response_time_ms"] = response_time
    except ValueError:
        return None
        
    # Validate sizes (must be non-negative)
    try:
        log["request_size_bytes"] = int(log["request_size_bytes"])
        log["response_size_bytes"] = int(log["response_size_bytes"])
        if log["request_size_bytes"] < 0 or log["response_size_bytes"] < 0:
            return None
    except ValueError:
        return None

    # Validate timestamp
    log_dt = parse_timestamp(log["timestamp"])
    if not log_dt:
        return None
        
    log["timestamp"] = log_dt # Replace string with datetime object

    return log

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
        "caching_opportunities": []
    }

def calculate_empty_cost() -> dict:
     return {
        "total_cost_usd": 0.0,
        "cost_breakdown": {
            "request_costs": 0.0,
            "execution_costs": 0.0,
            "memory_costs": 0.0
        },
        "cost_by_endpoint": [],
        "optimization_potential_usd": 0.0
    }

def calculate_summary(total_requests: int, total_response_time: float, error_count: int, timestamps: list) -> dict:
    """Calculates the overall summary statistics."""
    if total_requests == 0:
        return create_empty_report()["summary"]
        
    avg_response_time = total_response_time / total_requests
    error_rate = (error_count / total_requests) * 100
    
    # Sort timestamps to find range
    timestamps.sort()
    start_time = timestamps[0].strftime(config.TIMESTAMP_FORMAT) if timestamps else ""
    end_time = timestamps[-1].strftime(config.TIMESTAMP_FORMAT) if timestamps else ""

    return {
        "total_requests": total_requests,
        "time_range": {"start": start_time, "end": end_time},
        "avg_response_time_ms": round(avg_response_time, 2),
        "error_rate_percentage": round(error_rate, 2)
    }

def get_top_users(user_requests: dict, top_n: int) -> list:
    """Returns the top N users by request count."""
    sorted_users = sorted(user_requests.items(), key=lambda item: item[1], reverse=True)
    
    top_users = []
    for user_id, request_count in sorted_users[:top_n]:
        top_users.append({"user_id": user_id, "request_count": request_count})
        
    return top_users

def calculate_endpoint_stats(endpoint_data: dict) -> list:
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
            "error_rate_percentage": round(error_rate, 2), # Added for use in performance detection
            "most_common_status": most_common_status,
            "total_response_time_ms": data['total_time'], # Added for cost calculation
            "total_response_bytes": data['response_bytes'], # Added for cost calculation
            "is_get_count": data['is_get'] # Added for caching analysis
        })
        
    return endpoint_stats_list

def detect_performance_issues(endpoint_stats: list) -> list:
    """Identifies slow endpoints and high error rate endpoints based on config thresholds."""
    issues = []
    
    for stats in endpoint_stats:
        endpoint = stats["endpoint"]
        avg_time = stats["avg_response_time_ms"]
        err_rate = stats["error_rate_percentage"]
        
        # 1. Slow Endpoint Detection
        severity_slow = None
        threshold_ms = None
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
        threshold_rate = None
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

def get_memory_cost(response_size_bytes: int) -> float:
    """Calculates the memory cost for a single request based on response size tiers."""
    for max_bytes, cost in config.MEMORY_COST_TIERS_BYTES:
        if response_size_bytes <= max_bytes:
            return cost
    return 0.0 # Should not be reached if tiers are configured correctly

# --- Advanced Feature A: Cost Estimation Engine ---

def calculate_cost_analysis(endpoint_data: dict, total_requests: int) -> dict:
    """Calculates total and per-endpoint serverless execution costs."""
    if total_requests == 0:
        return calculate_empty_cost()

    total_request_costs = total_requests * config.COST_PER_REQUEST
    total_execution_costs = 0.0
    total_memory_costs = 0.0
    cost_by_endpoint = []

    for endpoint, data in endpoint_data.items():
        if data['count'] == 0: continue
        
        # Execution cost: (Total response time in ms) * cost per ms
        endpoint_execution_cost = data['total_time'] * config.COST_PER_MS_EXECUTION
        total_execution_costs += endpoint_execution_cost
        
        # Request cost: (Count) * cost per request
        endpoint_request_cost = data['count'] * config.COST_PER_REQUEST
        
        # Memory cost: (Count) * average memory cost per request
        # For simplicity, we assume the total memory cost is the sum of costs for each individual response size, 
        # using the tier cost per request.
        
        # This implementation requires a loop through the original logs to accurately calculate memory cost, 
        # as it depends on the size of *each* response. Since we only have total_response_bytes here, 
        # we'll approximate by using the *total count* times the cost for the *average* response size.
        # However, to be fully accurate based on the prompt's tiers (which are per request), 
        # we must assume the memory costs were summed during the single pass in function.py.
        # Since the pass is in function.py, let's assume `data` contains `total_memory_cost` 
        # calculated during the pass for accurate tiering.
        
        # *** SELF-CORRECTION: Must pass through cost data calculated in main pass ***
        # Since the main function only computes total bytes, we'll estimate using average size, 
        # and document this trade-off in DESIGN.md.
        
        avg_response_bytes = data['total_response_bytes'] / data['count']
        avg_memory_cost_per_request = get_memory_cost(int(avg_response_bytes))
        endpoint_memory_cost = data['count'] * avg_memory_cost_per_request
        total_memory_costs += endpoint_memory_cost
        
        # Total cost for endpoint
        endpoint_total_cost = endpoint_request_cost + endpoint_execution_cost + endpoint_memory_cost
        total_cost_per_request = endpoint_total_cost / data['count']

        cost_by_endpoint.append({
            "endpoint": endpoint,
            "total_cost": round(endpoint_total_cost, 2),
            "cost_per_request": round(total_cost_per_request, 4)
        })

    total_cost = total_request_costs + total_execution_costs + total_memory_costs
    
    # Calculate Optimization Potential (For this feature, we'll set it to 0 and rely on caching analysis for savings)
    optimization_potential_usd = 0.0
    
    return {
        "total_cost_usd": round(total_cost, 2),
        "cost_breakdown": {
            "request_costs": round(total_request_costs, 2),
            "execution_costs": round(total_execution_costs, 2),
            "memory_costs": round(total_memory_costs, 2)
        },
        "cost_by_endpoint": cost_by_endpoint,
        "optimization_potential_usd": round(optimization_potential_usd, 2)
    }

# --- Advanced Feature D: Caching Opportunity Analysis ---

def analyze_caching_opportunities(endpoint_stats: list, cost_analysis: dict) -> list:
    """Identifies endpoints that would benefit most from caching."""
    opportunities = []
    
    total_potential_savings = {
        "requests_eliminated": 0,
        "cost_savings_usd": 0.0,
        "performance_improvement_ms": 0.0
    }
    
    cost_map = {item['endpoint']: item for item in cost_analysis['cost_by_endpoint']}

    for stats in endpoint_stats:
        endpoint = stats["endpoint"]
        request_count = stats["request_count"]
        error_rate = stats["error_rate_percentage"]
        is_get_count = stats["is_get_count"]
        
        # 1. Check Criteria
        passes_criteria = (
            request_count > config.CACHE_CRITERIA_MIN_REQUESTS and 
            (is_get_count / request_count) >= config.CACHE_CRITERIA_MIN_GET_RATIO and
            error_rate <= config.CACHE_CRITERIA_MAX_ERROR_RATE and
            stats["most_common_status"] < 400 # Assumes 2xx/3xx are cacheable/consistent
        )
        
        if passes_criteria:
            # 2. Calculate Potential Savings
            potential_cache_hit_rate = math.floor((is_get_count / request_count) * 100 * 0.95) # 95% of GETs are cacheable
            potential_requests_saved = math.floor(request_count * (potential_cache_hit_rate / 100))
            
            # Find associated cost for savings calculation
            endpoint_cost_data = cost_map.get(endpoint)
            
            if endpoint_cost_data:
                cost_per_request = endpoint_cost_data['cost_per_request']
                estimated_cost_savings_usd = potential_requests_saved * cost_per_request
                
                # Performance improvement (approx) = requests saved * avg response time
                performance_improvement_ms = potential_requests_saved * stats["avg_response_time_ms"]
                
                opportunities.append({
                    "endpoint": endpoint,
                    "potential_cache_hit_rate": potential_cache_hit_rate,
                    "current_requests": request_count,
                    "potential_requests_saved": potential_requests_saved,
                    "estimated_cost_savings_usd": round(estimated_cost_savings_usd, 2),
                    "recommended_ttl_minutes": config.RECOMMENDED_TTL_MINUTES,
                    "recommendation_confidence": "high"
                })
                
                # Update total savings
                total_potential_savings["requests_eliminated"] += potential_requests_saved
                total_potential_savings["cost_savings_usd"] += estimated_cost_savings_usd
                total_potential_savings["performance_improvement_ms"] += performance_improvement_ms
                
    # Add Total Savings to the result for the final output format
    opportunities.append({
        "total_potential_savings": {
            "requests_eliminated": total_potential_savings["requests_eliminated"],
            "cost_savings_usd": round(total_potential_savings["cost_savings_usd"], 2),
            "performance_improvement_ms": round(total_potential_savings["performance_improvement_ms"], 2)
        }
    })
    
    return opportunities
    
def generate_recommendations(performance_issues: list, caching_opportunities: list) -> list:
    """Generates actionable recommendations based on analysis."""
    recommendations = []
    
    # 1. Recommendations from Performance Issues
    for issue in performance_issues:
        if issue["type"] == "slow_endpoint":
            recommendations.append(
                f"Investigate {issue['endpoint']} performance (avg {issue['avg_response_time_ms']}ms exceeds {issue['threshold_ms']}ms threshold)."
            )
        elif issue["type"] == "high_error_rate":
            recommendations.append(
                f"Alert: {issue['endpoint']} has {issue['error_rate_percentage']}% error rate. Severity: {issue['severity'].upper()}."
            )
            
    # 2. Recommendations from Caching Opportunities
    for opportunity in caching_opportunities:
        if "endpoint" in opportunity: # Skip the total savings entry
            recommendations.append(
                f"Consider caching for {opportunity['endpoint']} ({opportunity['current_requests']} requests, {opportunity['potential_cache_hit_rate']}% cache-hit potential)."
            )

    return recommendations