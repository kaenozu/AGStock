#!/bin/bash

# Setup Cloud Scheduler to trigger daily market scans

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME="agstock"
SCHEDULER_JOB_NAME="daily-market-scan"

echo "⏰ Setting up Cloud Scheduler..."

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format='value(status.url)')

# Create Cloud Scheduler job (runs at 9:00 AM JST = 00:00 UTC)
gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
  --location=$REGION \
  --schedule="0 0 * * 1-5" \
  --uri="${SERVICE_URL}/api/scan" \
  --http-method=POST \
  --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --time-zone="Asia/Tokyo" \
  --description="Daily market scan (weekdays at 9 AM JST)"

echo "✅ Cloud Scheduler configured!"
echo "Job: $SCHEDULER_JOB_NAME"
echo "Schedule: Weekdays at 9:00 AM JST"
