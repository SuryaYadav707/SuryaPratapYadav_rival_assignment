from typing import Final
# Standard timestamp format for parsing and output
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_TIMEZONE = 'UTC'

# Part 1: Performance Issue Detection Thresholds (in ms) ---
THRESHOLD_SLOW_MEDIUM = 500
THRESHOLD_SLOW_HIGH = 1000
THRESHOLD_SLOW_CRITICAL = 2000

# Part 1: Error Rate Detection Thresholds (in percentage) ---
THRESHOLD_ERROR_MEDIUM = 5.0 
THRESHOLD_ERROR_HIGH = 10.0  
THRESHOLD_ERROR_CRITICAL = 15.0  

# Part 2A: Cost Estimation Engine Rates (in USD) ---
COST_PER_REQUEST = 0.0001
COST_PER_MS_EXECUTION = 0.000002

# Memory tiers are based on Response Size Bytes
MEMORY_COST_TIERS_BYTES = [
    (1024, 0.00001),  # 0-1KB (1024 bytes)
    (10240, 0.00005), # 1KB-10KB (10240 bytes)
    (float('inf'), 0.0001) # 10KB+
]
# Multiplier to convert bytes to KB for readability/comparison
BYTES_TO_KB_MULTIPLIER = 1 / 1024 

# Part 2C: Rate Limiting Analysis Configuration (NEW) ---
RATE_LIMIT_RULES: Final[dict] = {
    "per_user": {
      "requests_per_minute": 100,
      "requests_per_hour": 1000
    },
    "per_endpoint": {
      "requests_per_minute": 500,
      "requests_per_hour": 5000
    }
}
