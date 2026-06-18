import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


def load_config():
    if os.path.exists(".env"):
        return {
            "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
            "ntfy_topic": os.getenv("NTFY_TOPIC"),
            "project_id": os.getenv("GCP_PROJECT_ID"),
        }
    else:
        # In production, secrets are fetched via models.storage.get_secret
        from models.storage import get_secret

        return {
            "anthropic_key": get_secret("ANTHROPIC_API_KEY"),
            "ntfy_topic": get_secret("NTFY_TOPIC"),
            "project_id": get_secret("GCP_PROJECT_ID"),
        }


CONFIG = load_config()
NTFY_URL = f"https://ntfy.sh/{CONFIG['ntfy_topic']}" if CONFIG.get("ntfy_topic") else None
anthropic_client = Anthropic(api_key=CONFIG.get("anthropic_key"))

def get_family_context():
    with open("family_context.json", "r") as f:
        return json.load(f)

