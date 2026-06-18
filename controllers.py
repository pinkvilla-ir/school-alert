from fastapi import FastAPI, Request, HTTPException
from datetime import datetime
import base64
import json
import logging

from services.gmail_service import fetch_latest_email, get_gmail_service
from services.anthropic_service import score_urgency
from services.notification_service import send_notification
from models.storage import get_last_history_id, set_last_history_id
from utils import log_to_file

log = logging.getLogger(__name__)

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "app": "school-alert"}


@app.post("/webhook")
async def gmail_webhook(request: Request):
    try:
        body = await request.json()
        pubsub_message = body.get("message", {})
        if not pubsub_message:
            raise HTTPException(status_code=400, detail="No message in request")

        data_b64 = pubsub_message.get("data", "")
        data_json = base64.b64decode(data_b64).decode("utf-8")
        data = json.loads(data_json)

        history_id = str(data.get("historyId"))
        email_addr = data.get("emailAddress")

        log.info(f"Webhook received | historyId={history_id} | {email_addr}")

        prev_history_id = get_last_history_id(email_addr)
        email = fetch_latest_email(start_history_id=prev_history_id)
        if not email:
            try:
                set_last_history_id(email_addr, history_id)
            except Exception:
                pass
            return {"status": "ok", "action": "no new email found"}

        score = score_urgency(email)
        log_to_file(email, score)

        try:
            set_last_history_id(email_addr, history_id)
        except Exception as e:
            log.error(f"Failed to update last history id store: {e}")

        if score["urgency"] >= 4:
            send_notification(email, score)
            return {"status": "ok", "action": "notification_sent", "urgency": score["urgency"]}
        else:
            log.info(f"Low urgency ({score['urgency']}) — no notification sent")
            return {"status": "ok", "action": "logged_only", "urgency": score["urgency"]}

    except json.JSONDecodeError as e:
        log.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        log.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/renew-watch")
async def renew_watch():
    try:
        service = get_gmail_service()
        project_id = None
        # project id can be provided via env or config; keep simple here
        topic = f"projects/{project_id}/topics/gmail-push"
        result = service.users().watch(userId="me", body={"topicName": topic}).execute()
        log.info(f"Gmail watch renewed | expiration={result.get('expiration')}")
        return {"status": "ok", "expiration": result.get("expiration")}
    except Exception as e:
        log.error(f"Failed to renew watch: {e}")
        raise HTTPException(status_code=500, detail=str(e))
