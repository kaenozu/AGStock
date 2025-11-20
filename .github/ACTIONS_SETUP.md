# GitHub Actions Setup Guide

## Overview
The `daily_scan.yml` workflow automatically runs the trading system every weekday at 17:00 JST (after market close).

## Setup Instructions

### 1. Configure Secrets
Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

#### Slack Notification (Optional)
- `SLACK_WEBHOOK_URL`: Your Slack webhook URL
  - Get it from: https://api.slack.com/messaging/webhooks

#### Email Notification (Optional)
- `EMAIL_ENABLED`: Set to `true` to enable email notifications
- `EMAIL_FROM`: Your email address (e.g., `your-email@gmail.com`)
- `EMAIL_PASSWORD`: Your email app password
  - For Gmail: https://support.google.com/accounts/answer/185833
- `EMAIL_TO`: Recipient email address

### 2. Enable Workflow
The workflow is automatically enabled once you push it to the repository.

### 3. Manual Trigger
You can manually trigger the workflow:
1. Go to Actions tab
2. Select "Daily Market Scan"
3. Click "Run workflow"

### 4. View Results
- Workflow logs: Actions tab → Daily Market Scan
- Saved reports: `reports/` folder (auto-committed)
- Errors: Automatically creates an Issue

## Workflow Schedule
- **Cron**: `0 8 * * 1-5` (08:00 UTC = 17:00 JST)
- **Days**: Monday-Friday (weekdays only)

## Customization
Edit `.github/workflows/daily_scan.yml` to:
- Change schedule time
- Modify notification settings
- Add additional steps
