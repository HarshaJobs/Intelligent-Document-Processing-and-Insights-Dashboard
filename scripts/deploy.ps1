# Deployment Script for Cloud Run and Cloud Functions (PowerShell for Windows)

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_NAME = if ($env:CLOUD_RUN_SERVICE) { $env:CLOUD_RUN_SERVICE } else { "doc-processor" }
$FUNCTION_NAME = if ($env:CLOUD_FUNCTION_NAME) { $env:CLOUD_FUNCTION_NAME } else { "document-trigger" }
$RAW_BUCKET = if ($env:GCS_RAW_BUCKET) { $env:GCS_RAW_BUCKET } else { "doc-processing-raw" }

if ([string]::IsNullOrEmpty($PROJECT_ID)) {
    Write-Host "Error: GCP_PROJECT_ID environment variable is not set" -ForegroundColor Red
    exit 1
}

Write-Host "Deploying to GCP Project: $PROJECT_ID" -ForegroundColor Green
Write-Host "Region: $REGION"
Write-Host ""

# Set the project
gcloud config set project $PROJECT_ID

# Build and deploy Cloud Run service
Write-Host "Building Docker image..." -ForegroundColor Yellow
$IMAGE_NAME = "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
docker build -t $IMAGE_NAME .

Write-Host "Pushing Docker image to Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME

Write-Host "Deploying Cloud Run service: $SERVICE_NAME" -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCS_RAW_BUCKET=${RAW_BUCKET},BIGQUERY_DATASET=document_processing"

# Get Cloud Run service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
Write-Host "Cloud Run service deployed at: $SERVICE_URL" -ForegroundColor Green

# Deploy Cloud Function
Write-Host ""
Write-Host "Deploying Cloud Function: $FUNCTION_NAME" -ForegroundColor Yellow
Push-Location cloud_functions\document_trigger

gcloud functions deploy $FUNCTION_NAME `
    --gen2 `
    --runtime python311 `
    --region $REGION `
    --trigger-bucket $RAW_BUCKET `
    --entry-point document_uploaded `
    --memory 512MB `
    --timeout 60s `
    --max-instances 10 `
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},PROCESSING_SERVICE_URL=${SERVICE_URL},BIGQUERY_DATASET=document_processing" `
    --service-account "doc-processor-service@${PROJECT_ID}.iam.gserviceaccount.com"

Pop-Location

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Cloud Run Service: $SERVICE_URL"
Write-Host "Cloud Function: $FUNCTION_NAME"
Write-Host ""
Write-Host "Test the deployment:"
Write-Host "  curl $SERVICE_URL/health"
Write-Host ""
