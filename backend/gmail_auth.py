from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
import os, threading

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = "token.json"
CRED_PATH = "credentials.json"


def run_oauth_with_timeout(timeout_sec=60):
    """
    Runs OAuth login flow but stops waiting after timeout_sec seconds.
    Returns creds or None.
    """
    creds_container = {"creds": None}

    def oauth_flow():
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CRED_PATH, SCOPES)
            creds_container["creds"] = flow.run_local_server(port=8080)
        except Exception:
            creds_container["creds"] = None

    thread = threading.Thread(target=oauth_flow)
    thread.daemon = True
    thread.start()
    thread.join(timeout_sec)

    if thread.is_alive():
        print("⏳ OAuth timeout — user did not authenticate.")
        return None

    return creds_container["creds"]


def get_gmail_service():
    """Authenticate with Gmail. If OAuth login is required but user does not authenticate within timeout → return None."""

    creds = None

    # Load token if available
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception:
            print("⚠ token.json corrupt — deleting.")
            os.remove(TOKEN_PATH)
            creds = None

    # Case 1: No token at all → must do OAuth
    if not creds:
        print("No token found — running OAuth...")
        creds = run_oauth_with_timeout()
        if not creds:
            print("OAuth login not completed — fallback required.")
            return None

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    # Case 2: Token exists but expired
    if not creds.valid:
        if creds.refresh_token:
            try:
                print("Refreshing token...")
                creds.refresh(Request())
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())
            except RefreshError:
                print("Refresh token invalid — OAuth required")
                creds = run_oauth_with_timeout()
                if not creds:
                    print("OAuth login not completed — fallback required.")
                    return None
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())
        else:
            print("⚠ No refresh token — OAuth required")
            creds = run_oauth_with_timeout()
            if not creds:
                print("OAuth login not completed — fallback required.")
                return None
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

    print("Gmail API authenticated successfully.")
    return build("gmail", "v1", credentials=creds)