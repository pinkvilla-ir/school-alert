#!/usr/bin/env python3
"""Send a synthetic ntfy notification for local testing.

This script is standalone and does not import the app code, so it's
safe to use when Gmail creds or other environment variables are not set.
"""
import os
import sys
import argparse
import json
import time

try:
    import httpx
except Exception:
    print("Please install httpx (`pip install httpx`) to run this script.")
    sys.exit(1)


def build_message(urgency: int) -> (str, dict):
    summary = "Test: synthetic school alert"
    subject = "Test notification"
    sender = "dev@example.com"
    action = urgency >= 4

    title = "📚 School update"
    priority = "default"
    if urgency == 5:
        title = "🚨 Urgent school alert"
        priority = "urgent"
    elif urgency == 4:
        title = "⚠️ Action needed this week"
        priority = "high"

    body = (
        f"{summary}\n\nFrom: {sender}\nSubject: {subject}\nAction today: {'Yes' if action else 'No'}"
    )

    headers = {"Priority": priority}
    return title + "\n\n" + body, headers


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--urgency", type=int, default=5, help="urgency 1-5")
    args = p.parse_args()

    ntfy_url = os.getenv("NTFY_URL")
    ntfy_topic = os.getenv("NTFY_TOPIC")
    if not ntfy_url and ntfy_topic:
        ntfy_url = f"https://ntfy.sh/{ntfy_topic}"

    message, headers = build_message(args.urgency)

    if not ntfy_url:
        print("NTFY_URL or NTFY_TOPIC not set. Example curl you can run:")
        sample = (
            f"curl -X POST -H 'Title: Test' -H 'Priority: {headers['Priority']}' "
            f"--data-binary $'" + message.replace("'", "'\"'\"'") + "' "
            "https://ntfy.sh/your-topic"
        )
        print(sample)
        return

    print(f"Sending test notification to {ntfy_url} (priority={headers['Priority']})")
    try:
        r = httpx.post(ntfy_url, content=message.encode("utf-8"), headers=headers, timeout=10.0)
        print("status:", r.status_code)
        try:
            print(r.text)
        except Exception:
            pass
    except Exception as e:
        print("Request failed:", type(e).__name__, e)


if __name__ == "__main__":
    main()
