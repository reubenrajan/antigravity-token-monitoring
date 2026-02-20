# SOP: Metrics Extraction

## Goal
Extract real-time remaining quota fraction and reset time for Gemini and Claude models across multiple Google Cloud accounts using OAuth tokens from the Antigravity extension.

## Input Schema
The application reads from `~/.config/opencode/antigravity-accounts.json`:
```json
{
  "accounts": [
    {
      "email": "user@example.com",
      "refresh_token": "string"
    }
  ]
}
```
And requires `.env` variables:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## Extraction Logic (Deterministic Steps)
1. **Load Accounts:** Read the JSON file (`~/.config/opencode/antigravity-accounts.json` or local `antigravity-accounts.json`) and parse the `accounts` array.
2. **Live Authentication Fallback:** If the file doesn't exist or is empty, trigger a local OAuth Device Flow or Local Web Server flow to fetch a new refresh token contextually, and save it to the local `antigravity-accounts.json`.
3. **Refresh Pass:** For each account, hit `https://oauth2.googleapis.com/token`.
   - Method: POST
   - Body (URL encoded): `client_id`, `client_secret`, `refresh_token`, `grant_type=refresh_token`
   - Handle 400 (Invalid Grant) by logging "Token Expired" and skipping the account (or re-triggering auth).
4. **Quota Fetch Pass:** For each valid access token, hit `https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels`.
   - Method: POST
   - Headers: 
     - `Authorization: Bearer <access_token>`
     - `User-Agent: antigravity/1.11.5 windows/amd64`
     - `X-Goog-Api-Client: google-cloud-sdk vscode_cloudshelleditor/0.1`
     - `Client-Metadata: {"ideType":"IDE_UNSPECIFIED","platform":"PLATFORM_UNSPECIFIED","pluginType":"GEMINI"}`
   - Handle 429/500 errors gracefully with at least one retry logic (backoff).
5. **Data Transformation:** Parse the response body (`models` dictionary).
   - Extract `quotaInfo.remainingFraction` and `quotaInfo.resetTime` for all models.

## Edge Cases to Handle
- **Network timeouts:** Wrap requests in a try-except block with a timeout. Return empty metrics if extraction fails entirely.
- **Missing tokens:** If `refresh_token` is missing from an account, skip it.

## Output Schema
Returns a list of dictionaries to the navigation layer:
```python
[
    {
        "account": "user@email.com",
        "modelName": "claude-3-5-sonnet-v2-0",
        "remainingFraction": 0.85, # Float
        "resetTimeMs": 170000000 # Epoch MS Integer
    }
]
```
