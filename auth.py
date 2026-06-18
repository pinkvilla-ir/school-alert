"""
Authentication script for Google Calendar API.
Run this once to generate token.json for your account.
"""

# auth.py
# Run this ONCE to authorize your app with Gmail.
# It opens a browser, you click Allow, and saves token.json.

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'  # needed for watch()
]


def authorize():
    creds = None

    # If token.json already exists, load it
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Silently refresh if expired
            creds.refresh(Request())
            print("✅ Token refreshed silently.")
        else:
            # Open browser for one-time authorization
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("✅ Authorization successful.")

        # Save the token for future runs
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
        print("✅ token.json saved.")

    # Verify it actually works by fetching your Gmail profile
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    print(f"\n✅ Connected to Gmail successfully!")
    print(f"   Email address : {profile['emailAddress']}")
    print(f"   Total messages: {profile['messagesTotal']}")
    print(f"\nYou're ready to move to the next step.")

if __name__ == '__main__':
    authorize()
