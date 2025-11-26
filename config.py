# Standard timestamp format for parsing and output
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_TIMEZONE = 'UTC'

# --- Part 1: Performance Issue Detection Thresholds (in ms) ---
THRESHOLD_SLOW_MEDIUM = 500
THRESHOLD_SLOW_HIGH = 1000
THRESHOLD_SLOW_CRITICAL = 2000

# --- Part 1: Error Rate Detection Thresholds (in percentage) ---
THRESHOLD_ERROR_MEDIUM = 5.0  # > 5%
THRESHOLD_ERROR_HIGH = 10.0  # > 10%
THRESHOLD_ERROR_CRITICAL = 15.0  # > 15%

# --- Part 2A: Cost Estimation Engine Rates (in USD) ---
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

# --- Part 2D: Caching Opportunity Analysis Criteria ---
CACHE_CRITERIA_MIN_REQUESTS = 100
CACHE_CRITERIA_MIN_GET_RATIO = 0.80 # 80% GET requests
CACHE_CRITERIA_MAX_ERROR_RATE = 2.0  # < 2% error rate
RECOMMENDED_TTL_MINUTES = 15