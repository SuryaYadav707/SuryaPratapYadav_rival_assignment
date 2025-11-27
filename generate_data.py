import json
import random
from datetime import datetime, timedelta, timezone

def generate_mock_logs(num_logs: int, output_filename: str):
    """
    Generates a list of mock API logs designed to test all features: 
    core stats, errors, slow responses, and rate limit violations.
    """
    
    # --- Configuration ---
    ENDPOINTS = ["/api/users", "/api/products", "/api/orders", "/api/search", "/api/auth"]
    METHODS = ["GET", "POST", "PUT", "DELETE"]
    USER_IDS = [f"user_{i:03d}" for i in range(10)]
    STATUS_CODES_SUCCESS = [200, 201, 202, 204]
    STATUS_CODES_ERROR = [400, 401, 404, 500, 503]
    
    # Define a high-traffic user and endpoint to reliably trigger rate limits
    HIGH_TRAFFIC_USER = "user_999"
    HIGH_TRAFFIC_ENDPOINT = "/api/critical"
    
    # Base timestamp
    start_time = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    logs = []
    current_time = start_time
    
    # --- Generate Logs ---
    for i in range(num_logs):
        log = {}
        
        # Increment time slightly more for the first 400 logs
        if i < 400:
            current_time += timedelta(milliseconds=random.randint(100, 500))
            
            # Use random user/endpoint
            log["user_id"] = random.choice(USER_IDS)
            log["endpoint"] = random.choice(ENDPOINTS)
            log["method"] = random.choice(METHODS)
            
            # Randomize metrics
            is_error = random.random() < 0.1 # 10% error rate
            log["status_code"] = random.choice(STATUS_CODES_ERROR) if is_error else random.choice(STATUS_CODES_SUCCESS)
            log["response_time_ms"] = random.randint(100, 1500)
            
            # Generate different memory tiers for cost testing
            if i % 10 == 0: # Large response (10KB+)
                log["response_size_bytes"] = random.randint(10241, 50000)
            elif i % 5 == 0: # Medium response (1KB-10KB)
                log["response_size_bytes"] = random.randint(1025, 10240)
            else: # Small response (0-1KB)
                log["response_size_bytes"] = random.randint(100, 1024)
            
            log["request_size_bytes"] = random.randint(100, 1000)
            
        # --- Inject Rate Limit Violation Traffic (Logs 400 to 500) ---
        else:
            # Injecting 100 requests in a 30-second window to guarantee per-minute violation
            current_time = start_time + timedelta(minutes=random.choice([2, 3])) # Jump to a new time window
            current_time += timedelta(seconds=random.uniform(0.0, 30.0))
            
            # Alternate between user and endpoint violation
            if i % 2 == 0:
                log["user_id"] = HIGH_TRAFFIC_USER
                log["endpoint"] = random.choice(ENDPOINTS) # Any endpoint
            else:
                log["user_id"] = random.choice(USER_IDS) # Any user
                log["endpoint"] = HIGH_TRAFFIC_ENDPOINT
                
            log["method"] = "GET"
            log["status_code"] = 200
            log["response_time_ms"] = random.randint(50, 200)
            log["response_size_bytes"] = random.randint(100, 500)
            log["request_size_bytes"] = 100
        
        # Ensure timestamp is the last generated time
        log["timestamp"] = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        logs.append(log)

    # Write logs to file
    with open(output_filename, 'w') as f:
        json.dump(logs, f, indent=2)

    print(f"\n✅ Successfully generated {num_logs} mock logs in {output_filename}")
    print("   Run your analysis function with this file to test all features.")


if __name__ == '__main__':
    # Define the output file path
    # You might want to adjust this path to put it in your 'tests/test_data' directory
    output_file = "mock_logs_10000.json"
    generate_mock_logs(10000, output_file)