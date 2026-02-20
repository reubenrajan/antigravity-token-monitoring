# SOP: Live Authentication Fallback

## Goal
Provide a fallback mechanism to authenticate the user and retrieve a valid refresh token when no `antigravity-accounts.json` file is found, ensuring the exporter can run seamlessly.

## Integration
Google OAuth 2.0 (Local Web Server flow or Device Authorization flow). Since this is a local CLI/Server tool, a local web server flow (spinning up a temporary HTTP server on localhost to catch the redirect callback) is standard.

## Tool Logic
1. **Configuration:** 
   - `client_id` and `client_secret` loaded from `.env`.
   - Scopes required: (Research required to find exact scopes used by Antigravity extension, likely includes `https://www.googleapis.com/auth/cloud-platform` and/or user email).
2. **Authorization Request:**
   - Generate a random `state` parameter and an code verifier/challenge (PKCE) if required by the client type.
   - Print a URL for the user to visit in their browser: `https://accounts.google.com/o/oauth2/v2/auth?...`
   - Start a temporary local web server (e.g., on port 8080) to listen for the redirect.
3. **Callback Handling:**
   - User authenticates and grants permission.
   - Google redirects the browser to `http://localhost:8080/?code=...&state=...`.
   - The local web server captures the `code` and shuts down.
4. **Token Exchange:**
   - Exchange the authorization `code` for an `access_token` and `refresh_token` at `https://oauth2.googleapis.com/token`.
5. **Save State:**
   - Fetch the user's email using the access token (e.g., `/oauth2/v2/userinfo`).
   - Create or update `antigravity-accounts.json` in the active project directory with the new `email` and `refresh_token`.

## Edge Cases
- Port 8080 is already in use (try adjacent ports like 8081, 8082).
- User cancels the authorization flow.
- Token exchange fails due to client misconfiguration.
