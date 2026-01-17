# GCP Project Setup Script (PowerShell for Windows)
# This script enables required APIs, creates buckets, and sets up BigQuery dataset

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$DATASET_NAME = if ($env:BIGQUERY_DATASET) { $env:BIGQUERY_DATASET } else { "document_processing" }
$RAW_BUCKET = if ($env:GCS_RAW_BUCKET) { $env:GCS_RAW_BUCKET } else { "doc-processing-raw" }
$PROCESSED_BUCKET = if ($env:GCS_PROCESSED_BUCKET) { $env:GCS_PROCESSED_BUCKET } else { "doc-processing-processed" }

if ([string]::IsNullOrEmpty($PROJECT_ID)) {
    Write-Host "Error: GCP_PROJECT_ID environment variable is not set" -ForegroundColor Red
    Write-Host "Usage: `$env:GCP_PROJECT_ID='your-project-id'; .\scripts\setup_gcp.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Setting up GCP Project: $PROJECT_ID" -ForegroundColor Green
Write-Host "Region: $REGION"
Write-Host "Dataset: $DATASET_NAME"
Write-Host "Raw Bucket: $RAW_BUCKET"
Write-Host "Processed Bucket: $PROCESSED_BUCKET"
Write-Host ""

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "Enabling required GCP APIs..." -ForegroundColor Yellow
$apis = @(
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "logging.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Enabling $api..."
    gcloud services enable $api
}

Write-Host "APIs enabled successfully" -ForegroundColor Green
Write-Host ""

# Create Cloud Storage buckets
Write-Host "Creating Cloud Storage buckets..." -ForegroundColor Yellow

# Check and create raw bucket
$rawExists = gsutil ls -b "gs://$RAW_BUCKET" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Bucket gs://$RAW_BUCKET already exists" -ForegroundColor Yellow
} else {
    Write-Host "Creating bucket: gs://$RAW_BUCKET" -ForegroundColor Yellow
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION "gs://$RAW_BUCKET"
    Write-Host "Bucket gs://$RAW_BUCKET created" -ForegroundColor Green
}

# Check and create processed bucket
$processedExists = gsutil ls -b "gs://$PROCESSED_BUCKET" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Bucket gs://$PROCESSED_BUCKET already exists" -ForegroundColor Yellow
} else {
    Write-Host "Creating bucket: gs://$PROCESSED_BUCKET" -ForegroundColor Yellow
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION "gs://$PROCESSED_BUCKET"
    Write-Host "Bucket gs://$PROCESSED_BUCKET created" -ForegroundColor Green
}

Write-Host "Buckets configured successfully" -ForegroundColor Green
Write-Host ""

# Create BigQuery dataset
Write-Host "Creating BigQuery dataset: $DATASET_NAME" -ForegroundColor Yellow
bq mk --dataset --location=US --description="Document Processing and Insights Dashboard dataset" "${PROJECT_ID}:${DATASET_NAME}" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Dataset may already exist" -ForegroundColor Yellow
}
Write-Host "Dataset created successfully" -ForegroundColor Green
Write-Host ""

# Note: Schema and views creation should be done manually or via bq command
Write-Host "Next: Create BigQuery tables using bigquery/schema.sql" -ForegroundColor Yellow
Write-Host "      Create BigQuery views using bigquery/views.sql" -ForegroundColor Yellow
Write-Host ""

# Create service account
$SERVICE_ACCOUNT_NAME = "doc-processor-service"
$SERVICE_ACCOUNT_EMAIL = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "Creating service account: $SERVICE_ACCOUNT_NAME" -ForegroundColor Yellow
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
    --display-name="Document Processor Service Account" `
    --description="Service account for document processing functions" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Service account may already exist" -ForegroundColor Yellow
}

# Grant necessary permissions
Write-Host "Granting permissions to service account..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="roles/bigquery.dataEditor"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="roles/bigquery.jobUser"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="roles/logging.logWriter"

Write-Host "Service account configured successfully" -ForegroundColor Green
Write-Host ""

Write-Host "=========================================" -ForegroundColor Green
Write-Host "GCP Project Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:"
Write-Host "  Project ID: $PROJECT_ID"
Write-Host "  Region: $REGION"
Write-Host "  BigQuery Dataset: $DATASET_NAME"
Write-Host "  Raw Bucket: gs://$RAW_BUCKET"
Write-Host "  Processed Bucket: gs://$PROCESSED_BUCKET"
Write-Host "  Service Account: $SERVICE_ACCOUNT_EMAIL"
Write-Host ""
