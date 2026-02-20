import os
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080"
SCOPES = "openid email profile https://www.googleapis.com/auth/cloud-platform"

auth_code = None

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query_components = parse_qs(urlparse(self.path).query)
        if "code" in query_components:
            auth_code = query_components["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication successful!</h1><p>You can close this window now.</p></body></html>")
        elif "error" in query_components:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication failed!</h1><p>Please check the console.</p></body></html>")
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        pass

def run_local_server():
    server_address = ('', 8080)
    try:
        httpd = HTTPServer(server_address, AuthHandler)
        print("\nWaiting for authorization...")
        while not auth_code:
            httpd.handle_request()
    except OSError as e:
        print(f"Error starting local server: {e}")
        print("Make sure port 8080 is available.")
        return False
    return True

def authenticate_and_save():
    global auth_code
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("Google OAuth credentials missing in .env")

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={SCOPES}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    print("\n" + "="*50)
    print("Action Required: Google Authentication")
    print("="*50)
    print("\nPlease log in to your Google Account to authorize Token Metrics:")
    print(auth_url)
    
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    if not run_local_server():
        return False

    print("Authorization code received. Exchanging for tokens...")

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
    )

    if resp.status_code != 200:
        print(f"Failed to exchange token: {resp.text}")
        return False

    tokens = resp.json()
    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")

    if not refresh_token:
        print("Warning: No refresh token returned.")
        return False

    user_resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    email = "unknown"
    if user_resp.status_code == 200:
        email = user_resp.json().get("email", "unknown")

    config_path = Path.cwd() / "antigravity-accounts.json"
    
    data = {"accounts": []}
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
        except Exception:
            pass

    updated = False
    for acc in data["accounts"]:
        if acc.get("email") == email:
            acc["refresh_token"] = refresh_token
            updated = True
            break
            
    if not updated:
        data["accounts"].append({
            "email": email,
            "refresh_token": refresh_token
        })

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Successfully authenticated and saved refresh token for {email} to {config_path}")
    return True

if __name__ == "__main__":
    authenticate_and_save()
