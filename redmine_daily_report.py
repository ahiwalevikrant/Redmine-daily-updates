import os
import sys
import json
import requests

REDMINE_URL = os.getenv("REDMINE_URL", "").rstrip("/")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

if not REDMINE_URL:
    print("ERROR: REDMINE_URL is missing")
    sys.exit(1)

if not REDMINE_API_KEY:
    print("ERROR: REDMINE_API_KEY is missing")
    sys.exit(1)

if not TEAMS_WEBHOOK_URL:
    print("ERROR: TEAMS_WEBHOOK_URL is missing")
    sys.exit(1)

headers = {
    "X-Redmine-API-Key": REDMINE_API_KEY,
    "Content-Type": "application/json"
}

params = {
    "assigned_to_id": "me",
    "status_id": "open",
    "limit": 50,
    "sort": "priority:desc"
}

try:
    api_url = f"{REDMINE_URL}/issues.json"

    print(f"Calling Redmine API: {api_url}")

    response = requests.get(
        api_url,
        headers=headers,
        params=params,
        timeout=30
    )

    print(f"Redmine Status Code: {response.status_code}")

    response.raise_for_status()

    data = response.json()
    issues = data.get("issues", [])

    print(f"Found {len(issues)} open tickets")

    if not issues:
        card_content = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Large",
                    "weight": "Bolder",
                    "color": "Good",
                    "text": "✅ No Open Tickets"
                },
                {
                    "type": "TextBlock",
                    "text": "No open tickets assigned."
                }
            ]
        }
    else:
        items = []

        for issue in issues[:10]:
            ticket_id = issue.get("id", "")
            subject = issue.get("subject", "")
            status = issue.get("status", {}).get("name", "")
            priority = issue.get("priority", {}).get("name", "")

            items.append({
                "type": "TextBlock",
                "wrap": True,
                "text": f"#{ticket_id} - {subject}"
            })

            items.append({
                "type": "TextBlock",
                "spacing": "Small",
                "isSubtle": True,
                "text": f"Status: {status} | Priority: {priority}"
            })

        card_content = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Large",
                    "weight": "Bolder",
                    "text": f"📋 Open Redmine Tickets ({len(issues)})"
                },
                {
                    "type": "Container",
                    "items": items
                }
            ]
        }

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_content
            }
        ]
    }

    print("Sending message to Teams...")

    teams_response = requests.post(
        TEAMS_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )

    print(f"Teams Status Code: {teams_response.status_code}")

    if teams_response.status_code not in [200, 202]:
        print("Teams Response:")
        print(teams_response.text)
        sys.exit(1)

    print("Report sent successfully")

except requests.exceptions.RequestException as ex:
    print(f"Request Error: {str(ex)}")
    sys.exit(1)

except Exception as ex:
    print(f"Unexpected Error: {str(ex)}")
    sys.exit(1)
