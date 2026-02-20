import os
import time
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from prometheus_client import start_http_server, Gauge
from authenticator import authenticate_and_save

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("metrics_exporter")

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Metrics definitions
remaining_fraction_metric = Gauge(
    "antigravity_token_quota_remaining_fraction", 
    "Remaining token quota fraction (0.0 to 1.0)",
    ["account", "model"]
)

reset_time_metric = Gauge(
    "antigravity_token_quota_reset_time_seconds", 
    "Epoch time when the token quota resets",
    ["account", "model"]
)

available_model_metric = Gauge(
    "antigravity_model_available", 
    "Indicates if a model is available to the account (1 for yes)",
    ["account", "model", "display_name"]
)

def get_accounts():
    """Load accounts from local or default config. Trigger live auth if not found."""
    # First check project directory
    local_path = Path.cwd() / "antigravity-accounts.json"
    default_path = Path.home() / ".config" / "opencode" / "antigravity-accounts.json"
    
    config_path = local_path if local_path.exists() else default_path
    
    if not config_path.exists():
        logger.warning(f"No accounts file found. Triggering live authentication.")
        if authenticate_and_save():
            config_path = local_path
        else:
            logger.error("Authentication failed or cancelled.")
            return []

    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            return data.get("accounts", [])
    except Exception as e:
        logger.error(f"Failed to read accounts file: {e}")
        return []

def refresh_token(refresh_token_string):
    """Refresh the OAuth token."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token_string,
            "grant_type": "refresh_token"
        },
        timeout=10
    )
    if resp.status_code != 200:
        logger.error(f"Token refresh failed: {resp.status_code}")
        return None
    return resp.json().get("access_token")

def fetch_quotas(access_token, email):
    """Fetch the quota info for the given access token."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "antigravity/1.11.5 windows/amd64",
        "X-Goog-Api-Client": "google-cloud-sdk vscode_cloudshelleditor/0.1",
        "Client-Metadata": '{"ideType":"IDE_UNSPECIFIED","platform":"PLATFORM_UNSPECIFIED","pluginType":"GEMINI"}',
    }
    
    try:
        resp = requests.post(
            "https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels",
            headers=headers,
            json={},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json().get("models", {})
        else:
            logger.error(f"Failed to fetch models for {email}: {resp.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching models for {email}: {e}")
        return {}

def update_metrics():
    """Main loop to update metrics across all accounts."""
    accounts = get_accounts()
    if not accounts:
        logger.warning("No accounts available to check.")
        return

    # To avoid stale data if accounts are removed or models disappear, 
    # we could clear the registry, but for simplicity we'll just overwrite existing labels.
    # A robust solution might use a CustomCollector, but Gauge is fine for this use case.

    for acc in accounts:
        email = acc.get("email", "unknown")
        token = acc.get("refresh_token")
        
        if not token:
            logger.warning(f"No refresh token for account {email}")
            continue
            
        logger.info(f"Fetching quotas for {email}...")
        access_token = refresh_token(token)
        if not access_token:
            continue
            
        models = fetch_quotas(access_token, email)
        
        for model_name, info in models.items():
            display_name = info.get("displayName", model_name)
            
            # Export availability status and exact displayName
            available_model_metric.labels(
                account=email, 
                model=model_name, 
                display_name=display_name
            ).set(1)
            
            quota = info.get("quotaInfo", {})
            rem_frac = quota.get("remainingFraction")
            reset_time_str = quota.get("resetTime")
            
            if rem_frac is not None:
                remaining_fraction_metric.labels(account=email, model=model_name).set(rem_frac)
                
            if reset_time_str:
                # Convert string like '2025-02-18T10:00:00Z' to epoch timestamp if needed
                # However we don't have python 3.11 fromisoformat perfectly matching Z sometimes.
                # Since Prometheus is happy with epoch, let's just make sure it sets cleanly.
                try:
                    from datetime import datetime
                    clean_str = reset_time_str.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(clean_str)
                    reset_time_metric.labels(account=email, model=model_name).set(dt.timestamp())
                except Exception as e:
                    logger.debug(f"Could not parse time {reset_time_str}: {e}")

if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("Missing Google OAuth credentials in .env")
        exit(1)
        
    logger.info("Starting Prometheus metrics server on port 8000...")
    start_http_server(8000)
    
    # Run the collector loop
    while True:
        try:
            update_metrics()
        except Exception as e:
            logger.error(f"Unexpected error in update loop: {e}")
            
        logger.info("Sleeping for 60 seconds...")
        time.sleep(60)
