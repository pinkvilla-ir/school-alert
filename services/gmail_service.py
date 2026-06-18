import os
import base64
import json
import logging
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

from models.storage import get_secret

log = logging.getLogger(__name__)


def get_gmail_service():
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        token_json = get_secret("GMAIL_TOKEN")
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    if getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
        try:
            creds.refresh(GoogleRequest())
            log.info("Gmail token refreshed.")
        except Exception:
            log.exception("Failed to refresh Gmail token")

        try:
            if os.path.exists("token.json"):
                with open("token.json", "w") as f:
                    f.write(creds.to_json())
                log.info("Saved refreshed Gmail credentials to token.json")
            else:
                # attempt to persist to Secret Manager via models.storage
                # keep simple here; storage.get_secret is read-only
                log.info("Running without writing refreshed token to Secret Manager")
        except Exception:
            log.exception("Failed to persist refreshed credentials")

    return build("gmail", "v1", credentials=creds)


def extract_body(payload: dict) -> str:
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        result = extract_body(part)
        if result:
            return result

    return "(no body found)"


def fetch_latest_email(start_history_id: str | None = None):
    service = get_gmail_service()

    try:
        messages = []

        if start_history_id:
            try:
                history = (
                    service.users()
                    .history()
                    .list(userId="me", startHistoryId=start_history_id, historyTypes=["messageAdded"])
                    .execute()
                )
                for record in history.get("history", []):
                    for msg in record.get("messagesAdded", []):
                        messages.append(msg["message"]["id"])
            except Exception:
                messages = []

        if not messages:
            log.info("No new messages via history API — falling back to unread query")
            resp = service.users().messages().list(userId="me", q="is:unread", maxResults=10).execute()
            for m in resp.get("messages", []):
                messages.append(m["id"])

        if not messages:
            log.info("No new messages found (history and unread query returned none)")
            return None

        msg_id = messages[-1]
        if len(messages) > 1:
            latest_id = msg_id
            latest_ts = -1
            for mid in messages:
                try:
                    m_meta = service.users().messages().get(userId="me", id=mid, format="metadata").execute()
                    ts = int(m_meta.get("internalDate", 0))
                    if ts > latest_ts:
                        latest_ts = ts
                        latest_id = mid
                except Exception:
                    continue
            msg_id = latest_id

        message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in message["payload"].get("headers", [])}
        subject = headers.get("subject", "(no subject)")
        sender = headers.get("from", "(unknown sender)")
        date = headers.get("date", "")
        body = extract_body(message["payload"])

        return {"id": msg_id, "subject": subject, "sender": sender, "date": date, "body": body[:3000]}

    except Exception:
        log.exception("Error fetching email")
        return None
