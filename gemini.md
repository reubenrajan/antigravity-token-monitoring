# Project Map: Token Metrics

## 1. Discovery
**North Star:** Build a web application to monitor AI model token usage across multiple Google Cloud accounts with real-time updates and analytics.
**Integrations:** Google Cloud, Antigravity opencode-antigravity-auth, Prometheus, Grafana. *(Keys: Google OAuth Client ID/Secret in `.env`)*
**Source of Truth:** Local file created by opencode-antigravity-auth: `~/.config/opencode/antigravity-accounts.json`
**Delivery Payload:** Prometheus `/metrics` endpoint and a Grafana Dashboard JSON.
**Behavioral Rules:** Use B.L.A.S.T protocol, 3-layer architecture, deterministic logic, self-healing principles. No API proxy development required.

## 2. Data Schema

### Input Payload (antigravity-accounts.json)
```json
{
  "accounts": [
    {
      "email": "user@example.com",
      "refresh_token": "oauth_refresh_token_string",
      "projectId": "optional-project-id"
    }
  ]
}
```

### Processing Logic (Quota Extraction)
1. Refresh the token via `https://oauth2.googleapis.com/token` using `.env` credentials (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`).
2. Call `https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels` via POST with the access token.
3. Parse `modelData.quotaInfo.remainingFraction` and `resetTime`.

### Output Payload (Prometheus Metrics)
```text
# HELP antigravity_token_quota_remaining_fraction Remaining token quota fraction (0.0 to 1.0)
# TYPE antigravity_token_quota_remaining_fraction gauge
antigravity_token_quota_remaining_fraction{account="user@example.com", model="claude-3-5-sonnet"} 0.85

# HELP antigravity_token_quota_reset_time_seconds Epoch time when the token quota resets
# TYPE antigravity_token_quota_reset_time_seconds gauge
antigravity_token_quota_reset_time_seconds{account="user@example.com", model="claude-3-5-sonnet"} 1718294400
```

## 3. Maintenance Log
**Deployment & Usage:**
1. Populate `.env` with the Google OAuth Credentials.
2. Ensure you have the python environment setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (or manually install `requests` `prometheus_client` `python-dotenv`).
3. If you have the Antigravity extension installed, the script will automatically read `~/.config/opencode/antigravity-accounts.json`.
4. If the file is not found, the `exporter.py` will prompt a live OAuth flow in the terminal to authenticate and save a local `antigravity-accounts.json`.
5. Run the exporter: `python tools/exporter.py` (Hosts on `localhost:8000`).
6. Import `dashboards/dashboard.json` into Grafana and ensure your Prometheus data source is connected to `localhost:8000`.

**Self-Healing Notes:**
- If rate-limited (429), the underlying fetch calls must implement backoff strategies as outlined in SOPs.
- `unauthorized_client` errors mean the `.env` OAuth keys do not match the keys used to generate the tokens in `antigravity-accounts.json`.
