import os
import json
from typing import Optional
from google.cloud import secretmanager
import logging
import time

log = logging.getLogger(__name__)

HISTORY_STORE = "history_ids.json"
COOLDOWN_STORE = "ntfy_cooldowns.json"
SENT_STORE = "sent_messages.json"


def _load_store(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_store(path: str, store: dict):
    try:
        with open(path, "w") as f:
            json.dump(store, f)
    except Exception as e:
        log.error(f"Failed to persist store {path}: {type(e).__name__}: {e}")


def get_last_history_id(email_addr: str) -> Optional[str]:
    store = _load_store(HISTORY_STORE)
    return store.get(email_addr)


def set_last_history_id(email_addr: str, history_id: str) -> None:
    store = _load_store(HISTORY_STORE)
    store[email_addr] = history_id
    _save_store(HISTORY_STORE, store)


def get_last_sent_for_topic(topic: str) -> Optional[float]:
    store = _load_store(COOLDOWN_STORE)
    ts = store.get(topic)
    return float(ts) if ts is not None else None


def set_last_sent_for_topic(topic: str, ts: float) -> None:
    store = _load_store(COOLDOWN_STORE)
    store[topic] = ts
    _save_store(COOLDOWN_STORE, store)


def has_message_been_sent(msg_key: str) -> bool:
    """Return True if we've already sent a notification for this message key."""
    store = _load_store(SENT_STORE)
    return msg_key in store


def mark_message_sent(msg_key: str) -> None:
    """Record that we've sent a notification for this message key."""
    store = _load_store(SENT_STORE)
    store[msg_key] = int(time.time())
    _save_store(SENT_STORE, store)


def get_secret(secret_id: str) -> str:
    """Fetch a secret from GCP Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT_ID", "school-alert")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")
