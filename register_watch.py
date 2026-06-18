# register_watch.py
# Run this once to tell Gmail to start pushing 
# notifications to your Pub/Sub topic.

import os
from dotenv import load_dotenv
from main import get_gmail_service

load_dotenv()

service = get_gmail_service()

result = service.users().watch(
    userId="me",
    body={
        "topicName": "projects/project-732b0e97-59c1-40ee-9d0/topics/gmail-push"
    }
).execute()

print(f"✅ Watch registered!")
print(f"   Expiration : {result['expiration']}")
print(f"   HistoryId  : {result['historyId']}")
print(f"\nGmail will now push notifications to your Pub/Sub topic.")
print(f"Remember: this expires in 7 days — Cloud Scheduler will renew it automatically.")