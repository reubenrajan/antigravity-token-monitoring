# SOP: Prometheus Exporter

## Goal
Host a Prometheus `/metrics` endpoint on port `8000` (by default) that exposes the data gathered by the metrics extraction component.

## Data Sources
Receives a list of dictionaries from the Navigation layer (which orchestrates the Extraction layer):
```python
[
    {
        "account": "user@email.com",
        "modelName": "claude-3-5-sonnet-v2-0",
        "remainingFraction": 0.85,
        "resetTimeMs": 170000000
    }
]
```

## Tool Logic
1. **Initialize Metrics registry:** Use `prometheus_client`.
2. **Define Gauges:**
   - `antigravity_token_quota_remaining_fraction` (Labels: `account`, `model`)
   - `antigravity_token_quota_reset_time_seconds` (Labels: `account`, `model`)
3. **Update Loop:**
   - A background thread or a polling mechanism (e.g. `CustomCollector`) that fetches new data every X seconds (e.g. 60 seconds).
   - Clear existing metrics for gauges that update specific labels if necessary, to avoid stale data for accounts that were removed.
   - Update the metrics with the latest values.
4. **Server:** Start the `start_http_server` from `prometheus_client`.

## Edge Cases to Handle
- If the first fetch fails on startup, the server should still start and return healthy, but with empty metrics. Subsequent polls will populate the data.

## Deployment Target
The final payload is delivered via HTTP GET to `localhost:8000/metrics`. This will be scraped by a local Prometheus instance.
