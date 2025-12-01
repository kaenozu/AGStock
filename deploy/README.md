# AGStock Cloud Deployment Guide

## Prerequisites
1. **Google Cloud Platform Account**
2. **gcloud CLI** installed and configured
3. **Docker** installed locally

## Setup Steps

### 1. Configure GCP Project
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# Login and set project
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
```

### 2. Enable Required APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable storage-api.googleapis.com
```

### 3. Create GCS Bucket for State Storage
```bash
gsutil mb -l $GCP_REGION gs://agstock-data-${GCP_PROJECT_ID}
```

### 4. Configure Docker for GCR
```bash
gcloud auth configure-docker
```

### 5. Deploy to Cloud Run
```bash
cd deploy
chmod +x cloud_run_deploy.sh
./cloud_run_deploy.sh
```

### 6. Setup Scheduler (Optional)
```bash
chmod +x scheduler_setup.sh
./scheduler_setup.sh
```

## Local Testing with Docker

### Build and run locally:
```bash
docker-compose up --build
```

Access the app at: http://localhost:8080

### Test with GCS locally:
```bash
# Set environment variables
export STORAGE_MODE=gcs
export GCS_BUCKET_NAME=agstock-data-${GCP_PROJECT_ID}
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

docker-compose up
```

## Environment Variables
- `STORAGE_MODE`: `local` or `gcs`
- `GCS_BUCKET_NAME`: Google Cloud Storage bucket name
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON key (local only)

## Cost Optimization
Cloud Run pricing:
- **Free tier**: 2 million requests/month
- **Pay-per-use**: Only charged when the container is running
- Recommended: Set min instances to 0 for maximum cost savings

## Monitoring
View logs:
```bash
gcloud run services logs tail agstock --region=$GCP_REGION
```

## Troubleshooting
- **Container fails to start**: Check logs via GCP Console
- **Storage errors**: Verify GCS bucket permissions
- **Scheduler not triggering**: Check service account permissions
