#!/usr/bin/env python3
"""First-time OAuth setup for headless environments (PythonAnywhere)."""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
]

cred_dir = Path(__file__).resolve().parent.parent / "credentials"
cred_file = cred_dir / "credentials.json"
token_file = cred_dir / "token.json"
cred_dir.mkdir(parents=True, exist_ok=True)

if not cred_file.exists():
    print(f"credentials.json not found at {cred_file}")
    print("1. Go to https://console.cloud.google.com/apis/credentials")
    print("2. Create OAuth 2.0 Client ID → Desktop app")
    print("3. Download JSON → save as:", cred_file)
    exit(1)

flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), SCOPES)

if hasattr(flow, 'run_console'):
    creds = flow.run_console()
else:
    auth_url, _ = flow.authorization_url(prompt='consent')
    print("Open this URL in your browser:")
    print(auth_url)
    code = input("Enter the authorization code: ")
    flow.fetch_token(code=code)
    creds = flow.credentials

with open(token_file, "w") as f:
    f.write(creds.to_json())
print(f"token.json saved to {token_file}")
