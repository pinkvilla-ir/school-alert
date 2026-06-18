# school-alert
School-alert is a Python FastAPI app that monitors Gmail, scores message urgency using Anthropic (with keyword heuristics), and sends notifications via ntfy.sh. It persists history IDs, sent-message records, and cooldowns; includes retries, backoff, deduplication, numeric priority headers, Docker/Cloud Run deployment, and env-base
