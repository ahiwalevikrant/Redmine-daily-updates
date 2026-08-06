import os
import sys
import json
import requests

# === CONFIGURATION (from environment variables) ===
REDMINE_URL = os.environ.get("REDMINE_URL", "https://redmine.speridian.com/redmine/projects/engineering")
API_KEY = os.environ.get("REDMINE_API_KEY")
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")

if not API_KEY or not TEAMS_WEBHOOK_URL:
    print("❌ Missing required environment variables: REDMINE_API_KEY and/or TEAMS_WEBHOOK_URL")
    sys.exit(1)

# === STEP 1: Fetch tickets assigned to you ===
headers = {"X-Redmine-API-Key": API_KEY}
params = {
    "assigned_to_id": "me",
    "status_id": "open",
    "limit": 50,
    "sort": "priority:desc"
}

try:
    response = requests.get(f"{REDMINE_URL}/issues.json", headers=headers, params=params, timeout=30)
    response.raise_for_status()
    issues = response.json().get("issues", [])
    print(f"✅ Found {len(issues)} tickets assigned to you")

    # === STEP 2: Build Adaptive Card ===
    if not issues:
        # No tickets - simple card
        adaptive_card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "✅ No Open Tickets!",
                    "size": "Large",
                    "weight": "Bolder",
                    "color": "Good"
                },
                {
                    "type": "TextBlock",
                    "text": "No tickets are currently assigned to you. Enjoy your day! 🎉",
                    "isSubtle": True
                }
            ]
        }
    else:
        # Build ticket list for Adaptive Card
        ticket_items = []
        for issue in issues[:10]:  # Limit to 10 tickets
            ticket_id = issue.get("id", "N/A")
            subject = issue.get("subject", "No subject")
            priority = issue.get("priority", {}).get("name", "N/A")
            status = issue.get("status", {}).get("name", "N/A")

            # Color based on priority
            color = "Attention" if priority in ["High", "Urgent"] else "Default"

            ticket_items.append({
                "type": "TextBlock",
                "text": f"**#{ticket_id}** - {subject}",
                "wrap": True
            })
            ticket_items.append({
                "type": "TextBlock",
                "text": f"Priority: {priority} | Status: {status}",
                "isSubtle": True,
                "spacing": "Small",
                "separator": True
            })

        adaptive_card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📋 Your Open Redmine Tickets",
                    "size": "Large",
                    "weight": "Bolder"
                },
                {
                    "type": "TextBlock",
                    "text": f"You have {len(issues)} open ticket(s) assigned to you",
                    "isSubtle": True,
                    "spacing": "Small"
                },
                {
                    "type": "Container",
                    "items": ticket_items,
                    "spacing": "Medium"
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View All Tickets in Redmine",
                    "url": f"{REDMINE_URL}/issues?assigned_to_id=me"
                }
            ]
        }

    # === STEP 3: Send to Teams ===
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": adaptive_card
            }
        ]
    }

    print("📤 Sending Adaptive Card to Teams...")
    response_teams = requests.post(
        TEAMS_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )

    print(f"📊 Teams Response Status: {response_teams.status_code}")

    if response_teams.status_code == 202:
        print("✅ Message accepted! Check your Teams channel.")
    else:
        print(f"❌ Error: {response_teams.status_code}")
        print(f"Response: {response_teams.text}")
        sys.exit(1)

except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
