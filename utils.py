import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("alerts.log")],
)

log = logging.getLogger(__name__)


def log_to_file(email: dict, score: dict):
    record = {
        "timestamp": datetime.now().isoformat(),
        "sender": email["sender"],
        "subject": email["subject"],
        "urgency": score["urgency"],
        "summary": score["summary"],
        "action_today": score["action_today"],
        "reason": score["reason"],
    }
    try:
        with open("email_log.json", "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        log.exception("Failed to write email log")
