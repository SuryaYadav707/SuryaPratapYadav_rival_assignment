# function.py

import json
from collections import defaultdict
from typing import Final, Any, Dict, List
import utils
import os
from datetime import datetime

def analyze_api_logs(logs: List[Dict[str, Any]]) -> dict:
    """
    Processes API call logs in a single efficient pass and generates a comprehensive
    analytics report, including advanced features (Cost Estimation and Rate Limiting Analysis).
    """
    if not logs:
        # Returns empty report including the default rate_limit_violations structure
        return utils.create_empty_report() 

    # 1. Initialize data structures
    EndpointData = defaultdict[str, Dict[str, Any]]
    
    endpoint_data: EndpointData = defaultdict(lambda: {
        'total_time': 0, 'count': 0, 'errors': 0, 'statuses': defaultdict(int),
        'min_time': float('inf'), 'max_time': float('-inf'), 
        'total_memory_cost': 0.0, # ACCUMULATES INDIVIDUAL MEMORY COSTS
        'is_get': 0
    })
    user_requests = defaultdict(int)
    hourly_distribution = defaultdict(int)
    
    # Global summary variables
    total_requests: int = 0
    total_response_time: float = 0.0
    error_count: int = 0
    timestamps: List[datetime] = []
    
    # Store validated logs for the time-sensitive rate limiting analysis
    validated_logs: List[Dict[str, Any]] = [] 

    # 2. Single pass for aggregation and validation
    for log in logs:
        cleaned_log = utils.validate_log_entry(log)
        if not cleaned_log:
            continue 

        # Store the cleaned log for time-based analysis later
        validated_logs.append(cleaned_log)
        
        # Process data
        dt = cleaned_log['timestamp']
        endpoint = cleaned_log['endpoint']
        
        # Update global summary
        total_requests += 1
        total_response_time += cleaned_log['response_time_ms']
        timestamps.append(dt)
        
        # Update hourly distribution
        hour_str: str = dt.strftime('%H:00')
        hourly_distribution[hour_str] += 1
        
        # Update user stats
        user_requests[cleaned_log['user_id']] += 1

        # Update endpoint stats
        ed = endpoint_data[endpoint]
        ed['total_time'] += cleaned_log['response_time_ms']
        ed['count'] += 1
        ed['min_time'] = min(ed['min_time'], cleaned_log['response_time_ms'])
        ed['max_time'] = max(ed['max_time'], cleaned_log['response_time_ms'])
        ed['statuses'][cleaned_log['status_code']] += 1
        
        # ACCURATE MEMORY COST ACCUMULATION
        memory_cost = utils.get_memory_cost(cleaned_log['response_size_bytes'])
        ed['total_memory_cost'] += memory_cost
        
        if 400 <= cleaned_log['status_code'] < 600:
            ed['errors'] += 1
            error_count += 1
        
        if cleaned_log['method'] == 'GET':
            ed['is_get'] += 1
            
    # CRITICAL: Sort validated logs by time before rate limit analysis (ensures sliding window integrity)
    validated_logs.sort(key=lambda x: x['timestamp'])

    # 3. Post-processing and Report Generation
    
    summary = utils.calculate_summary(total_requests, total_response_time, error_count, timestamps)
    endpoint_stats = utils.calculate_endpoint_stats(endpoint_data)
    performance_issues = utils.detect_performance_issues(endpoint_stats)

    # Advanced Features
    cost_analysis = utils.calculate_cost_analysis(endpoint_data, total_requests)
    
    # Rate Limiting Analysis
    rate_limit_violations = utils.analyze_rate_limit_violations(validated_logs)

    # Optimization Potential is 0.0 since Caching Analysis (Option D) was replaced.
    cost_analysis["optimization_potential_usd"] = 0.0

    # Generate Recommendations (Uses Rate Limit violations now)
    recommendations = utils.generate_recommendations(performance_issues, rate_limit_violations)

    # Final Report Assembly
    report = {
        "summary": summary,
        "endpoint_stats": endpoint_stats,
        "performance_issues": performance_issues,
        "recommendations": recommendations,
        "hourly_distribution": dict(sorted(hourly_distribution.items())),
        "top_users_by_requests": utils.get_top_users(user_requests, 5),
        "cost_analysis": cost_analysis,
        "rate_limit_violations": rate_limit_violations # NEW OUTPUT BLOCK
    }
    
    return report

if __name__ == '__main__':
    # Simple example of running the function
    
    # Determine the path to the sample data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.join(script_dir, 'tests', 'test_data', 'sample_medium.json')

    if not os.path.exists(sample_path):
        print(f"Error: Could not find sample data at {sample_path}")
        print("Please ensure the directory structure is correct and 'sample_small.json' exists.")
    else:
        try:
            with open(sample_path, 'r') as f:
                sample_logs = json.load(f)
                
            print("--- Analysis Report ---")
            report = analyze_api_logs(sample_logs)
            print(json.dumps(report, indent=2))
            
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from {sample_path}. Check file format.")
        except Exception as e:
            print(f"An unexpected error occurred during analysis: {e}")