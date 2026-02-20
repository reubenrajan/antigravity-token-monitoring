# Project: Token Metrics - AI Token Usage Dashboard on Grafana
## Goal: Build a web application to monitor AI model token usage across multiple Google Cloud accounts with real-time updates and analytics.

## Key features:
- Multi-Account Monitoring - Track multiple Google Cloud accounts simultaneously
- Real-Time Quotas - View Claude and Gemini model quota percentages with live updates
- Reset Timers - Countdown to quota reset for each account and model
- Subscription Tier Detection - Automatic FREE/PRO/ULTRA tier detection
- Usage Analytics - Token usage, request stats, burn rate calculations
- Timeline Visualization - Hourly usage graphs and quota history
- Language Server Integration - Connect to Antigravity VS Code extension
- API Proxy - Claude/OpenAI compatible API with automatic account rotation
- Custom Prometheus Exporter
- Custom Grafana Dashboard with the graphs referenced from Prometheus Queries

## Tech Stack:
- Grafana
- Prometheus
- Python

## Prerequisites
- Google Cloud Account with OAuth credentials configured
- Antigravity accounts - OAuth tokens from opencode-antigravity-auth

## Dashboard Components
- Total Accounts: Lists all the Google Accounts with OAuth credentials configured
- Token Utilization: Shows the token utilization for each account and model
- Reset Timers: Countdown to quota reset for each account and model
- Subscription Tier Detection: Automatic FREE/PRO/ULTRA tier detection
- Usage Analytics: Token usage, request stats, burn rate calculations
- Timeline Visualization: Hourly usage graphs and quota history

## References
Note: Don't copy/imitate the code directly from the referenced repository, rather use it as a reference to understand logic, always employ coding best practices when implementing.
https://github.com/OmerFarukOruc/antigravity-dashboard

## Future Support (not to be developed now):
- ChatGPT Integration
- Perplexity Integration