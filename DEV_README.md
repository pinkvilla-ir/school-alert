# Development README

Quick setup and local test commands for new developers.

Prerequisites
- Python 3.11+ and `pip`
- (Optional) Docker for local container testing

Local setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Environment variables (minimum for basic local tests)
- `ANTHROPIC_API_KEY` — required for real scoring
- `NTFY_TOPIC` or `NTFY_URL` — e.g. `https://ntfy.sh/<topic>`
- `GCP_PROJECT_ID` — used by some flows (optional for synthetic tests)

Run the app locally
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
curl http://127.0.0.1:8080/health
```

One-shot local E2E (uses real Gmail credentials)
```bash
python main.py
```
This requires a valid `token.json` (Gmail OAuth) **or** the `GMAIL_TOKEN` secret in Secret Manager.

Simulate a Gmail webhook
```bash
DATA='{"historyId":"1","emailAddress":"me@example.com"}'
B64=$(echo -n "$DATA" | base64)
curl -X POST -H "Content-Type: application/json" \
  -d "{\"message\":{\"data\":\"$B64\"}}" \
  http://127.0.0.1:8080/webhook
```

Quick synthetic notification (no Gmail)
```bash
# provide NTFY_TOPIC or NTFY_URL env var, e.g.:
export NTFY_TOPIC=sschool-alert-123456-sravz
# or export NTFY_URL=https://ntfy.sh/school-alert-123456-sravz
python scripts/send_test_notification.py --urgency 5
```

Docker (optional)
```bash
docker build -t school-alert .
docker run -p 8080:8080 -e PORT=8080 school-alert
curl http://127.0.0.1:8080/health
```

Cloud Run deploy (no local Docker required)
```bash
gcloud run deploy school-alert \
  --source . \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project-id \
  --timeout=300s
```

Troubleshooting
- If Cloud Run cannot persist Gmail tokens, grant the Cloud Run service account Secret Manager access or pre-create the `GMAIL_TOKEN` secret (see `REAUTH.md`).
- Use `gcloud run services logs read school-alert --region=us-east1` to inspect logs.

Contact
- Ask the original author for OAuth/secret setup details.
