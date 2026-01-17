#!/bin/bash
# GCP Project Setup Script
# This script enables required APIs, creates buckets, and sets up BigQuery dataset

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BIGQUERY_DATASET:-document_processing}"
RAW_BUCKET="${GCS_RAW_BUCKET:-doc-processing-raw}"
PROCESSED_BUCKET="${GCS_PROCESSED_BUCKET:-doc-processing-processed}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable is not set"
    echo "Usage: export GCP_PROJECT_ID=your-project-id && ./scripts/setup_gcp.sh"
    exit 1
fi

echo "Setting up GCP Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Dataset: $DATASET_NAME"
echo "Raw Bucket: $RAW_BUCKET"
echo "Processed Bucket: $PROCESSED_BUCKET"
echo ""

# Set the project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    storage.googleapis.com \
    cloudfunctions.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    logging.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

echo "APIs enabled successfully"
echo ""

# Create Cloud Storage buckets
echo "Creating Cloud Storage buckets..."

# Check if raw bucket exists
if gsutil ls -b "gs://$RAW_BUCKET" &>/dev/null; then
    echo "Bucket gs://$RAW_BUCKET already exists"
else
    echo "Creating bucket: gs://$RAW_BUCKET"
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://$RAW_BUCKET"
    echo "Bucket gs://$RAW_BUCKET created"
fi

# Check if processed bucket exists
if gsutil ls -b "gs://$PROCESSED_BUCKET" &>/dev/null; then
    echo "Bucket gs://$PROCESSED_BUCKET already exists"
else
    echo "Creating bucket: gs://$PROCESSED_BUCKET"
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://$PROCESSED_BUCKET"
    echo "Bucket gs://$PROCESSED_BUCKET created"
fi

# Set bucket lifecycle policies (optional - move old files to archive)
cat > /tmp/bucket-lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/bucket-lifecycle.json "gs://$RAW_BUCKET"
gsutil lifecycle set /tmp/bucket-lifecycle.json "gs://$PROCESSED_BUCKET"
rm /tmp/bucket-lifecycle.json

echo "Buckets configured successfully"
echo ""

# Create BigQuery dataset
echo "Creating BigQuery dataset: $DATASET_NAME"
bq mk --dataset \
    --location=US \
    --description="Document Processing and Insights Dashboard dataset" \
    "${PROJECT_ID}:${DATASET_NAME}" || echo "Dataset may already exist"
echo "Dataset created successfully"
echo ""

# Create BigQuery tables from schema
echo "Creating BigQuery tables from schema..."
SCHEMA_FILE="bigquery/schema.sql"

if [ -f "$SCHEMA_FILE" ]; then
    # Replace placeholders in schema file
    sed "s/{project_id}/${PROJECT_ID}/g; s/{dataset}/${DATASET_NAME}/g" "$SCHEMA_FILE" > /tmp/schema_processed.sql
    
    # Execute schema SQL
    echo "Executing schema.sql..."
    bq query --use_legacy_sql=false --format=prettyjson < /tmp/schema_processed.sql || echo "Tables may already exist or SQL needs manual execution"
    rm /tmp/schema_processed.sql
    echo "Tables created successfully"
else
    echo "Warning: Schema file not found at $SCHEMA_FILE"
    echo "Please create tables manually using bigquery/schema.sql"
fi

echo ""

# Create BigQuery views
echo "Creating BigQuery views..."
VIEWS_FILE="bigquery/views.sql"

if [ -f "$VIEWS_FILE" ]; then
    # Replace placeholders in views file
    sed "s/{project_id}/${PROJECT_ID}/g; s/{dataset}/${DATASET_NAME}/g" "$VIEWS_FILE" > /tmp/views_processed.sql
    
    # Execute views SQL
    echo "Executing views.sql..."
    bq query --use_legacy_sql=false --format=prettyjson < /tmp/views_processed.sql || echo "Views may already exist or SQL needs manual execution"
    rm /tmp/views_processed.sql
    echo "Views created successfully"
else
    echo "Warning: Views file not found at $VIEWS_FILE"
    echo "Please create views manually using bigquery/views.sql"
fi

echo ""

# Create service account for Cloud Functions (if needed)
SERVICE_ACCOUNT_NAME="doc-processor-service"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Creating service account: $SERVICE_ACCOUNT_NAME"
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name="Document Processor Service Account" \
    --description="Service account for document processing functions" \
    2>/dev/null || echo "Service account may already exist"

# Grant necessary permissions
echo "Granting permissions to service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.objectAdmin" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/bigquery.dataEditor" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/bigquery.jobUser" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/logging.logWriter" \
    --condition=None

echo "Service account configured successfully"
echo ""

echo "========================================="
echo "GCP Project Setup Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  BigQuery Dataset: $DATASET_NAME"
echo "  Raw Bucket: gs://$RAW_BUCKET"
echo "  Processed Bucket: gs://$PROCESSED_BUCKET"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "Next steps:"
echo "  1. Set up environment variables in .env file"
echo "  2. Run deployment scripts: ./scripts/deploy.sh"
echo "  3. Configure Looker connection to BigQuery"
echo ""
