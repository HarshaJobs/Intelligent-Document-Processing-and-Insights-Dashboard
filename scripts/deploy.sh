#!/bin/bash
# Deployment Script for Cloud Run and Cloud Functions

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-doc-processor}"
FUNCTION_NAME="${CLOUD_FUNCTION_NAME:-document-trigger}"
RAW_BUCKET="${GCS_RAW_BUCKET:-doc-processing-raw}"
PROCESSING_SERVICE_URL="${PROCESSING_SERVICE_URL:-}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable is not set"
    exit 1
fi

echo "Deploying to GCP Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set the project
gcloud config set project "$PROJECT_ID"

# Build and deploy Cloud Run service
echo "Building Docker image..."
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
docker build -t "$IMAGE_NAME" .

echo "Pushing Docker image to Container Registry..."
docker push "$IMAGE_NAME"

echo "Deploying Cloud Run service: $SERVICE_NAME"
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCS_RAW_BUCKET=${RAW_BUCKET},BIGQUERY_DATASET=document_processing"

# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)')
echo "Cloud Run service deployed at: $SERVICE_URL"

# Deploy Cloud Function
echo ""
echo "Deploying Cloud Function: $FUNCTION_NAME"
cd cloud_functions/document_trigger

gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --trigger-bucket "$RAW_BUCKET" \
    --entry-point document_uploaded \
    --memory 512MB \
    --timeout 60s \
    --max-instances 10 \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},PROCESSING_SERVICE_URL=${SERVICE_URL:-},BIGQUERY_DATASET=document_processing" \
    --service-account "doc-processor-service@${PROJECT_ID}.iam.gserviceaccount.com"

cd ../..

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Cloud Run Service: $SERVICE_URL"
echo "Cloud Function: $FUNCTION_NAME"
echo ""
echo "Test the deployment:"
echo "  curl $SERVICE_URL/health"
echo ""
