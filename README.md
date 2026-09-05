# Daily Redmine Updates for Microsoft Teams

This repository contains a lightweight Python automation that sends a daily summary of your open Redmine issues to a Microsoft Teams incoming webhook.

It runs automatically through GitHub Actions every weekday at **7:00 AM IST** (01:30 UTC) and can also be started manually from the Actions tab.

## What it does

The script:

1. Calls Redmine's `issues.json` API using the configured API key.
2. Requests issues assigned to the authenticated Redmine user, with an open status.
3. Sorts the results by priority, highest first, and fetches up to 50 issues.
4. Builds a Microsoft Teams Adaptive Card.
5. Posts a card containing the first 10 issues, or a "No Open Tickets" card when none are found.

Each listed issue shows its ID, subject, status, and priority. The card heading reflects the total number of matching issues, even when only the first 10 are displayed.

## Repository layout

| Path | Purpose |
| --- | --- |
| `redmine_daily_report.py` | Retrieves Redmine issues and posts the Teams Adaptive Card. |
| `.github/workflows/redmine-report.yml` | GitHub Actions workflow that installs Python dependencies, validates secrets, and runs the script. |

## Prerequisites

- Access to a Redmine instance with API access enabled.
- A Redmine API key for the user whose assigned issues should be reported.
- A Microsoft Teams incoming-webhook URL that accepts Adaptive Cards.
- Python 3.11 or later for local execution (the workflow uses Python 3.11).

## Configure GitHub Actions

In the GitHub repository, open **Settings → Secrets and variables → Actions** and add these repository secrets:

| Secret | Description | Example |
| --- | --- | --- |
| `REDMINE_URL` | Base URL of the Redmine installation. A trailing slash is accepted. | `https://redmine.example.com` |
| `REDMINE_API_KEY` | API key for the Redmine user whose work should be reported. | `your-redmine-api-key` |
| `TEAMS_WEBHOOK_URL` | Incoming webhook URL for the target Teams channel. | `https://…` |

The workflow checks that all three secrets exist before running the report. Keep them in GitHub Secrets; do not commit them to the repository or paste them into source files.

### Schedule and manual runs

The workflow is configured with:

```yaml
- cron: '30 1 * * 1-5'
```

That means Monday–Friday at 01:30 UTC, which is 07:00 IST. GitHub Actions schedules can be delayed during periods of high load, so use the **Run workflow** button under the Actions tab if you need an immediate report.

## Run locally

Create and activate a virtual environment if desired, install the only dependency, then provide the same three values as environment variables.

```powershell
python -m pip install requests

$env:REDMINE_URL = "https://redmine.example.com"
$env:REDMINE_API_KEY = "your-redmine-api-key"
$env:TEAMS_WEBHOOK_URL = "https://your-teams-webhook-url"

python .\redmine_daily_report.py
```

On macOS or Linux:

```bash
python -m pip install requests
export REDMINE_URL="https://redmine.example.com"
export REDMINE_API_KEY="your-redmine-api-key"
export TEAMS_WEBHOOK_URL="https://your-teams-webhook-url"
python redmine_daily_report.py
```

## Redmine query details

The request is sent to:

```text
<REDMINE_URL>/issues.json
```

with the `X-Redmine-API-Key` header and these query parameters:

| Parameter | Value | Meaning |
| --- | --- | --- |
| `assigned_to_id` | `me` | Issues assigned to the API-key owner. |
| `status_id` | `open` | Open issues only. |
| `limit` | `50` | Fetch at most 50 matching issues. |
| `sort` | `priority:desc` | Highest-priority issues first. |

The script applies a 30-second timeout to both Redmine and Teams requests.

## Troubleshooting

| Symptom | Likely cause and resolution |
| --- | --- |
| `REDMINE_URL is missing` (or another missing-variable error) | Add the variable locally or the matching GitHub Actions secret. |
| Redmine returns 401 or 403 | Check the API key, API access setting, and the account's Redmine permissions. |
| No issues appear | Confirm that the API-key owner has open issues assigned to them; the query deliberately uses `assigned_to_id=me`. |
| Teams returns a non-200/202 response | Verify the incoming webhook URL and that the Teams connector/workflow is still active and permitted to receive Adaptive Cards. |
| Scheduled workflow does not start exactly at 7:00 AM IST | GitHub Actions cron jobs are best-effort; run the workflow manually for a time-sensitive delivery. |

Workflow logs show the Redmine and Teams HTTP status codes, plus the number of issues found. They do not print the configured secrets.

## Customization

To change the report behavior, edit `params` in `redmine_daily_report.py`:

- Adjust `status_id` to include different issue states.
- Change `assigned_to_id` to report for another Redmine user or group.
- Increase or decrease the Redmine fetch `limit`.
- Change `issues[:10]` to control how many issues appear in the Teams card.
- Update the cron expression in `.github/workflows/redmine-report.yml` to change the schedule.

After changing the workflow or script, commit and push the update, then use **Run workflow** once to verify the end-to-end delivery.

## Security notes

- Treat `REDMINE_API_KEY` and `TEAMS_WEBHOOK_URL` as credentials.
- Use repository or organization secrets instead of plain-text workflow values.
- Rotate a credential immediately if it appears in a commit, log, screenshot, or message.
- Limit the Redmine account and Teams webhook to the minimum access needed for this report.

