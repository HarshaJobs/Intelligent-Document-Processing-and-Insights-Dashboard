#!/bin/bash
# Cloud Scheduler Setup for Weekly Reports

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SCHEDULER_JOB_NAME="${SCHEDULER_JOB_NAME:-weekly-report-generator}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-doc-processor}"
SERVICE_URL="${PROCESSING_SERVICE_URL:-}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable is not set"
    exit 1
fi

echo "Setting up Cloud Scheduler for weekly reports"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set the project
gcloud config set project "$PROJECT_ID"

# Get Cloud Run service URL if not provided
if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")
    if [ -z "$SERVICE_URL" ]; then
        echo "Error: Could not determine Cloud Run service URL"
        echo "Please set PROCESSING_SERVICE_URL environment variable"
        exit 1
    fi
fi

# Create Cloud Scheduler job
echo "Creating Cloud Scheduler job: $SCHEDULER_JOB_NAME"
echo "Schedule: Every Monday at 9:00 AM UTC (0 9 * * 1)"
echo "Target: $SERVICE_URL/api/v1/reports/generate"

gcloud scheduler jobs create http "$SCHEDULER_JOB_NAME" \
    --location="$REGION" \
    --schedule="0 9 * * 1" \
    --uri="$SERVICE_URL/api/v1/reports/generate" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{"week_start": null, "week_end": null}' \
    --time-zone="UTC" \
    --description="Generate weekly report for document processing" \
    --max-retry-attempts=3 \
    --max-retry-duration=3600s \
    --min-backoff-duration=10s \
    --max-backoff-duration=300s \
    --attempt-deadline=600s \
    2>/dev/null || {
    echo "Job may already exist. Updating..."
    gcloud scheduler jobs update http "$SCHEDULER_JOB_NAME" \
        --location="$REGION" \
        --uri="$SERVICE_URL/api/v1/reports/generate" \
        --http-method=POST \
        --headers="Content-Type=application/json" \
        --message-body='{"week_start": null, "week_end": null}'
}

echo ""
echo "========================================="
echo "Cloud Scheduler Setup Complete!"
echo "========================================="
echo ""
echo "Job Name: $SCHEDULER_JOB_NAME"
echo "Schedule: Every Monday at 9:00 AM UTC"
echo "Target: $SERVICE_URL/api/v1/reports/generate"
echo ""
echo "To test manually:"
echo "  gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION"
echo ""
