# function.py

import json
from collections import defaultdict
import utils

def analyze_api_logs(logs: list) -> dict:
    """
    Processes API call logs in a single efficient pass and generates a comprehensive
    analytics report, including advanced features (Cost and Caching Analysis).
    """
    if not logs:
        return utils.create_empty_report() 

    # 1. Initialize data structures for single-pass analysis
    endpoint_data = defaultdict(lambda: {
        'total_time': 0, 'count': 0, 'errors': 0, 'statuses': defaultdict(int),
        'min_time': float('inf'), 'max_time': float('-inf'), 
        'request_bytes': 0, 'response_bytes': 0, 'is_get': 0,
        'total_response_bytes': 0 # Required for Cost Analysis
    })
    user_requests = defaultdict(int)
    hourly_distribution = defaultdict(int)
    
    # Global summary variables
    total_requests = 0
    total_response_time = 0
    error_count = 0
    timestamps = []

    # 2. Single pass over logs (with robust error handling)
    for log in logs:
        # Validate and clean log
        cleaned_log = utils.validate_log_entry(log)
        if not cleaned_log:
            # print(f"Skipping malformed/invalid log: {log}") # Good for debugging
            continue 

        # Process data
        dt = cleaned_log['timestamp']
        endpoint = cleaned_log['endpoint']
        
        # Update global summary
        total_requests += 1
        total_response_time += cleaned_log['response_time_ms']
        timestamps.append(dt)
        
        # Update hourly distribution
        hour_str = dt.strftime('%H:00')
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
        ed['total_response_bytes'] += cleaned_log['response_size_bytes']
        
        if 400 <= cleaned_log['status_code'] < 600:
            ed['errors'] += 1
            error_count += 1
        
        if cleaned_log['method'] == 'GET':
            ed['is_get'] += 1

    # 3. Post-processing and Report Generation
    
    # Calculate Summary
    summary = utils.calculate_summary(total_requests, total_response_time, error_count, timestamps)
    
    # Calculate Endpoint Stats and Performance Issues
    endpoint_stats = utils.calculate_endpoint_stats(endpoint_data)
    performance_issues = utils.detect_performance_issues(endpoint_stats)

    # Calculate Advanced Features (A & D)
    cost_analysis = utils.calculate_cost_analysis(endpoint_data, total_requests)
    
    # Pass cost data to caching analysis for savings estimation
    caching_opportunities_full = utils.analyze_caching_opportunities(endpoint_stats, cost_analysis)
    
    # Extract total savings for separate output key
    if caching_opportunities_full and "total_potential_savings" in caching_opportunities_full[-1]:
        total_potential_savings = caching_opportunities_full.pop() 
    else:
        total_potential_savings = utils.analyze_caching_opportunities([], utils.calculate_empty_cost())[-1]['total_potential_savings'] # Get empty savings dict

    # Generate Recommendations
    recommendations = utils.generate_recommendations(performance_issues, caching_opportunities_full)

    # Final Report Assembly
    report = {
        "summary": summary,
        "endpoint_stats": endpoint_stats,
        "performance_issues": performance_issues,
        "recommendations": recommendations,
        "hourly_distribution": dict(sorted(hourly_distribution.items())),
        "top_users_by_requests": utils.get_top_users(user_requests, 5),
        "cost_analysis": cost_analysis, # Advanced Feature A
        "caching_opportunities": caching_opportunities_full, # Advanced Feature D
        "total_potential_savings": total_potential_savings # Cleanly separate total savings 
    }
    
    return report

if __name__ == '__main__':
    # Simple example of running the function
    import os
    
    # Load sample data
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sample_path = os.path.join(current_dir, 'tests', 'test_data', 'sample_small.json')
        with open(sample_path, 'r') as f:
            sample_logs = json.load(f)
            
        print("--- Analysis Report ---")
        report = analyze_api_logs(sample_logs)
        print(json.dumps(report, indent=2))
        
    except FileNotFoundError:
        print("Error: Could not find 'tests/test_data/sample_small.json'. Please run tests/test_data first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")