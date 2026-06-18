import json
from datetime import datetime
from config import anthropic_client, get_family_context
import logging

log = logging.getLogger(__name__)


def score_urgency(email: dict) -> dict:
    FAMILY_CONTEXT = get_family_context()
    prompt = f"""
You are a smart assistant helping a parent manage school-related emails.

FAMILY CONTEXT:
{json.dumps(FAMILY_CONTEXT, indent=2)}

TODAY'S DATE: {datetime.now().strftime("%A, %B %d, %Y %I:%M %p")}

NEW EMAIL:
From    : {email['sender']}
Subject : {email['subject']}
Date    : {email['date']}
Body    :
{email['body']}

TASK:
Analyze this email against the family context and today's date.
Respond ONLY with a valid JSON object — no explanation, no markdown.

{{
  "urgency": <integer 1-5>,
  "summary": "<one sentence, max 20 words>",
  "action_today": <true or false>,
  "reason": "<one sentence explaining your urgency score>"
}}

Be conservative — only score 5 if it genuinely affects today's plans. Even the ones postponed
"""

    try:
        response = anthropic_client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        result = json.loads(raw)
        # Apply simple heuristic overrides for high-impact keywords
        subject_body = (email.get("subject", "") + "\n" + email.get("body", "")).lower()
        cancel_keywords = ["cancel", "cancelled", "canceled", "postpon", "resched", "early dismissal", "school closed", "dismissal"]
        for kw in cancel_keywords:
            if kw in subject_body:
                if result.get("urgency", 0) < 5:
                    old = result.get("urgency", 0)
                    result["urgency"] = 5
                    result["action_today"] = True
                    result["reason"] = (result.get("reason", "") + " [heuristic override: contains '%s']") % kw
                    log.info(
                        f"Heuristic override applied: bumped urgency {old}→5 for keyword '{kw}' in subject/body"
                    )
                break

        log.info(f"Scored email | urgency={result['urgency']} action_today={result['action_today']} | {email['subject'][:60]}")
        return result
    except Exception as e:
        log.exception("Anthropic scoring failed, returning conservative fallback")
        return {"urgency": 3, "summary": "(fallback) review later", "action_today": False, "reason": str(e)}
