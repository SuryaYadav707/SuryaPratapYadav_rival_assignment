# System Design — Log Analysis Engine

This document describes the architecture, algorithms, and design decisions behind the Log Analysis Engine implemented for the Rival assignment.

---

# 1. Architecture Overview

The system follows a modular, pipeline-based architecture:

1. **Input Loading**
2. **Validation**
3. **Single-Pass Aggregation**
4. **Post-Processing**
5. **Advanced Computations (Cost + Rate Limiting)**
6. **Recommendation Engine**
7. **Report Assembly**

Each stage is separated into functions for clarity, scalability, and testability.

logs.json → validate → aggregate → compute stats → detect issues → generate recommendations → final report


---

# 2. Core Design Principles

### ✔ Single-pass processing  
All important metrics are collected in one traversal of the logs (O(N)), ensuring high performance even for large datasets.

### ✔ Fault tolerance  
Malformed logs are caught by `validate_log_entry()` and counted as invalid rather than breaking execution.

### ✔ Configurable  
Thresholds (latency, rate limits, cost model) are kept in `config.py`.

### ✔ Extensible  
New metrics or analysis modules can be added without impacting the core pipeline.

---

# 3. Data Structures

| Structure | Purpose |
|----------|----------|
| `endpoint_stats_map` | Collects per-endpoint counts, response times, and status distributions |
| `performance_issues` | List of slow requests with severity categories |
| `hourly_distribution` | Tracks traffic volume for each hour (00–23) |
| `user_request_count` | Tracks request count per user |
| `validated_logs` | Stores valid logs for rate-limiting analysis |
| `rate_limit_violations` | Stores final sliding-window rate limit results |

All structures are optimized for O(1) average insert/update.

---

# 4. Single-Pass Aggregation

During the main loop, each log contributes to:

- total request count  
- endpoint-level response times  
- status code aggregation  
- latency-based issue detection  
- hourly traffic  
- user activity tracking  
- validation counts  

This guarantees minimal runtime and maximum efficiency.

---

# 5. Post-Processing Logic

After the single pass:

### ✔ Percentile Computation  
Median and p95 are computed using sorting per-endpoint:
O(K log K) per endpoint



### ✔ Endpoint Success Rate  
Calculated as:
success / total_requests



### ✔ Sorting  
Top users and hourly distribution are sorted chronologically or by volume depending on the metric.

---

# 6. Advanced Option A — Cost Analysis

Cost estimation is implemented based on:
total_cost = total_requests * COST_PER_REQUEST


This is intentionally simple, business-relevant, and low-overhead.

---

# 7. Advanced Option C — Rate Limiting Analysis

A sliding window rate-limiting detector is implemented:

### Algorithm Steps:
1. Sort validated logs by timestamp  
2. Maintain a deque for each user  
3. For each timestamp:
   - Push current time  
   - Pop entries older than 60 seconds  
4. If deque length > threshold → violation logged  

### Complexity:
O(N log N) # because sorting timestamps is required



### Why Option C was chosen:
- Reflects real production systems  
- Demonstrates understanding of distributed rate limits  
- Provides actionable insights  

---

# 8. Performance Issue Detection

Latency categories:

| Category | Threshold |
|----------|-----------|
| Medium | > 500 ms |
| High | > 1000 ms |
| Critical | > 2000 ms |

These mirror realistic API SLO boundaries.

---

# 9. Recommendation Engine

Recommendations are generated using:

- high-latency endpoints  
- critical performance issues  
- users violating rate limits  
- endpoints with high error rates  

Design goal: Provide **SRE-grade actionable insights**, not just metrics.

---

# 10. Complexity Analysis

| Component | Time | Space |
|----------|------|--------|
| Validation | O(N) | O(1) |
| Single-pass aggregation | **O(N)** | O(E + U) |
| Percentile processing | O(K log K) | O(K) |
| Rate limiting (sliding window) | **O(N log N)** | O(N) |
| Final assembly | O(E) | O(E) |

Overall worst-case:
O(N log N)


---

# 11. Edge Cases Considered

- Missing required fields  
- Invalid timestamps  
- Negative response times  
- Empty dataset  
- All logs invalid  
- Multiple requests in the same millisecond  
- Multiple users hitting same endpoint  
- High request bursts  
- Logs out of chronological order  

---

# 12. Testing Strategy

### Included test cases:
- Functional tests covering typical datasets  
- Edge cases (malformed logs, missing fields)  
- Large dataset performance tests  
- Validation tests  
- Rate limiting behaviour tests  

Tests ensure correctness, stability, and performance.

---

# 13. Design Rationale

The final architecture was chosen because it:

- scales well  
- is easy to understand and extend  
- uses clean, isolated modules  
- mirrors real-world logging analytics pipelines  
- aligns with production engineering best practices  

---
