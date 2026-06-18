# Manual Gmail re-authorization (local)

This document shows the quick steps to re-authorize Gmail access from your laptop, save the resulting `token.json`, and upload it to Secret Manager so Cloud Run uses the updated credentials.

Prereqs
- `credentials.json` (OAuth client secrets) present in the repo root
- `gcloud` configured to the project and you have Secret Manager permissions
- Python environment with `google-auth-oauthlib` installed

1) Install helper (if needed)

```bash
python3 -m pip install --upgrade google-auth-oauthlib
```

2) Run the interactive OAuth flow (opens browser)

```bash
PYTHONPATH=. python3 - <<'PY'
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
  "https://www.googleapis.com/auth/gmail.readonly",
  "https://www.googleapis.com/auth/gmail.modify"
]

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0, authorization_prompt_params={"access_type":"offline","prompt":"consent"})
with open('token.json', 'w') as f:
    f.write(creds.to_json())
print('Wrote token.json')
PY
```

Notes:
- `access_type=offline` + `prompt=consent` forces Google to return a refresh token.
- If Google does not return a refresh token, visit https://myaccount.google.com/permissions, remove the app, then re-run the flow.

3) Verify locally

```bash
PYTHONPATH=. python3 - <<'PY'
from main import get_gmail_service
svc = get_gmail_service()
print(svc.users().getProfile(userId='me').execute())
PY
```

4) Upload `token.json` to Secret Manager (Cloud Run reads `versions/latest`)

```bash
PROJECT=project-732b0e97-59c1-40ee-9d0
gcloud secrets create GMAIL_TOKEN --replication-policy="automatic" --project=${PROJECT} || true
gcloud secrets versions add GMAIL_TOKEN --data-file=token.json --project=${PROJECT}
```

5) Permissions & verification
- Ensure the Cloud Run service account has `roles/secretmanager.secretAccessor`.
- Your service reads `projects/.../secrets/GMAIL_TOKEN/versions/latest` so no redeploy is required after uploading a new version.

Troubleshooting
- If you get `invalid_grant` again: the refresh token was revoked — remove the app from Google permissions and re-run the flow.
- If the flow fails to return a refresh token, ensure you use `prompt=consent` and `access_type=offline`.
- Protect `credentials.json` and `token.json` — treat them as secrets.

If you want, I can scaffold secure `/oauth/start` and `/oauth/callback` endpoints so reauthorization can be performed from the running Cloud Run app (recommended for easier ops).


## Deploying to Cloud Run

After you update secrets or code, deploy the service so Cloud Run runs the latest image. Two common options:

- Deploy from source (Cloud Build builds image automatically):

gcloud run deploy school-alert \
  --source . \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=school-alert

- Build an image and deploy the image explicitly (useful when you want an Artifact Registry image):

```bash
PROJECT=project-732b0e97-59c1-40ee-9d0
REGION=us-east1
REPO=school-alert-repo
LOCATION=us-central1

# Build & push
gcloud builds submit --tag ${LOCATION}-docker.pkg.dev/${PROJECT}/${REPO}/school-alert:latest .

# Deploy the pushed image
gcloud run deploy school-alert \
  --source . \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=project-732b0e97-59c1-40ee-9d0
```

Verification & notes:

- Check service status and recent logs:

```bash
gcloud run services describe school-alert --region=${REGION} --project=${PROJECT} --format='yaml(status,latestReadyRevisionName,traffic)'
gcloud run services logs read school-alert --region=${REGION} --limit=100 --project=${PROJECT}
```

- Ensure the Cloud Run service account has `roles/secretmanager.secretAccessor` so it can read `GMAIL_TOKEN`.
- Uploading a new `GMAIL_TOKEN` secret version *does not* require a redeploy — the service reads `versions/latest` at runtime. However, if you changed code (e.g., added `/oauth` endpoints), you must redeploy.

### Checking logs

Stream recent logs for the Cloud Run service (live tail):

```bash
gcloud beta run services logs tail school-alert --region=us-east1 --project=project-732b0e97-59c1-40ee-9d0
```

Read recent log entries (non-streaming):

```bash
gcloud run services logs read school-alert --region=us-east1 --limit=200 --project=project-732b0e97-59c1-40ee-9d0
```

Or use Cloud Logging filters directly (streaming):

```bash
gcloud logging tail --project=project-732b0e97-59c1-40ee-9d0 "resource.type=cloud_run_revision AND resource.labels.service_name=school-alert"
```

Tip: if you see `invalid_grant` errors in logs, follow the reauth steps above to refresh the Gmail token.

