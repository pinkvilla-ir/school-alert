
import os
import time
import random
import httpx
import logging
from datetime import datetime
from config import NTFY_URL, CONFIG
from models.storage import (
    get_last_sent_for_topic,
    set_last_sent_for_topic,
    has_message_been_sent,
    mark_message_sent,
)

log = logging.getLogger(__name__)


def send_notification(email: dict, score: dict):
    urgency = score["urgency"]
    summary = score["summary"]
    action = score["action_today"]
    subject = email["subject"]
    sender = email["sender"]

    if urgency == 5:
        title = "🚨 Urgent school alert"
        priority = "urgent"
    elif urgency == 4:
        title = "⚠️ Action needed this week"
        priority = "high"
    else:
        title = "📚 School update"
        priority = "default"

    message = f"{summary}\n\nFrom: {sender}\nSubject: {subject}\nAction today: {'Yes ⚡' if action else 'No'}"

    def _sanitize_header(s: str) -> str:
        if not isinstance(s, str):
            s = str(s)
        return s.encode("ascii", "ignore").decode("ascii")
    # ntfy expects numeric priority 1-5 in the Priority header
    priority_map = {"urgent": "5", "high": "4", "default": "3"}
    headers = {"Priority": priority_map.get(priority, "3")}
    full_message = f"{title}\n\n{message}"

    if not NTFY_URL:
        log.error("NTFY_URL is not configured — skipping notification")
        return

    topic = CONFIG.get("ntfy_topic") if isinstance(CONFIG, dict) else None
    # Configurable cooldowns: default short cooldown for normal sends and a
    # longer minimum cooldown applied when ntfy rate-limits us.
    COOLDOWN_SECONDS = int(os.getenv("NTFY_COOLDOWN", "60"))
    MIN_COOLDOWN_ON_429 = int(os.getenv("NTFY_MIN_COOLDOWN", "300"))
    if topic:
        # store cooldown as expiry timestamp (epoch). If stored value is in the
        # future, skip sending until that time.
        last_expiry = get_last_sent_for_topic(topic)
        if last_expiry and time.time() < float(last_expiry):
            expiry_dt = datetime.fromtimestamp(float(last_expiry)).isoformat()
            log.info(f"Skipping notification — cooldown active for topic {topic} until {expiry_dt}")
            return

    # Prevent duplicate sends for the same email: use Gmail message id when
    # available, otherwise fallback to subject|sender|date signature.
    msg_id = email.get("id")
    if not msg_id:
        msg_id = f"sig:{email.get('subject','')[:200]}|{email.get('sender','')[:200]}|{email.get('date','')[:100]}"

    try:
        if has_message_been_sent(msg_id):
            log.info(f"Skipping notification — already sent for message {msg_id}")
            return
    except Exception:
        # If the store check fails, continue and try to send (fail-open)
        log.exception("Failed to check sent-message store; proceeding to send")

    max_retries = 5
    base_backoff = 1.0
    log.info(f"Sending notification to nfty url - {NTFY_URL}")
    for attempt in range(1, max_retries + 1):
        try:
            response = httpx.post(NTFY_URL, content=full_message.encode("utf-8"), headers=headers, timeout=10.0)
            if response.status_code == 200:
                log.info(f"Notification sent | priority={priority} | {summary}")
                if topic:
                    try:
                        # set expiry to now + cooldown seconds
                        expiry = time.time() + COOLDOWN_SECONDS
                        set_last_sent_for_topic(topic, expiry)
                    except Exception:
                        log.exception("Failed to update cooldown store")
                # record that we've sent this message so we don't send it again
                try:
                    mark_message_sent(msg_id)
                except Exception:
                    log.exception("Failed to mark message as sent")
                return
            if response.status_code == 429:
                # Respect Retry-After header if present, otherwise compute backoff.
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after)
                else:
                    wait = int(base_backoff * (2 ** (attempt - 1)) + random.uniform(0, 1))

                log.warning(f"ntfy rate limited (429). attempt={attempt} wait={wait}s headers={dict(response.headers)}")
                # Persist a cooldown expiry so we don't hammer ntfy while it's limiting us.
                # Use a longer minimum cooldown when a 429 occurs.
                if topic:
                    try:
                        expiry = time.time() + max(wait, COOLDOWN_SECONDS, MIN_COOLDOWN_ON_429)
                        set_last_sent_for_topic(topic, expiry)
                        log.info(f"Set cooldown for topic {topic} until {datetime.fromtimestamp(expiry).isoformat()}")
                    except Exception:
                        log.exception("Failed to update cooldown store on 429")
                # Do not aggressively retry immediately; return and allow the cooldown to prevent further sends
                return
            # Log non-200 responses for debugging
            if response.status_code >= 400:
                log.error(f"ntfy response {response.status_code}: {response.text} headers={dict(response.headers)}")
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error sending notification: {e}")
            break
        except Exception as e:
            wait = min(10, base_backoff * attempt)
            log.warning(f"ntfy send attempt {attempt} failed: {type(e).__name__}: {e}. retrying in {wait}s")
            time.sleep(wait)
            continue

    log.error(f"Gave up sending notification after {max_retries} attempts")
