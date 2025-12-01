#!/bin/bash

# Google Cloud Run Deployment Script for AGStock

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME="agstock"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "🚀 Deploying AGStock to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

# Push to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars="STORAGE_MODE=gcs,GCS_BUCKET_NAME=agstock-data-${PROJECT_ID}" \
  --project $PROJECT_ID

echo "✅ Deployment complete!"
echo "📍 Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format='value(status.url)'
