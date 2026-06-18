"""Application entrypoint.

This file only exposes the FastAPI `app` from `controllers` for Cloud Run.
It also provides a small local end-to-end test when executed as a script.
"""

from controllers import app


if __name__ == "__main__":
    # Local convenience test: fetch, score, and optionally notify.
    # Import inside main to avoid import-time side effects in Cloud Run.
    from services.gmail_service import fetch_latest_email
    from services.anthropic_service import score_urgency
    from services.notification_service import send_notification

    print("Running local end-to-end test: fetch -> score -> notify")
    email = fetch_latest_email(None)
    if not email:
        print("No new/unread email found to test.")
    else:
        print(email.get("subject"), email.get("sender"), email.get("date"))
        score = score_urgency(email)
        print("Score:", score)
        if score.get("urgency", 0) >= 4:
            send_notification(email, score)
            print("Notification sent")
        else:
            print("No notification needed for urgency", score.get("urgency"))