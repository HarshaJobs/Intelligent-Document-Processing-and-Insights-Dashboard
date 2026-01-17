# Deployment Guide

Complete guide for deploying the Intelligent Document Processing and Insights Dashboard.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GCP Project Setup](#gcp-project-setup)
3. [Deploy Services](#deploy-services)
4. [Configure Looker](#configure-looker)
5. [Run Tests](#run-tests)
6. [Schedule Reports](#schedule-reports)
7. [Verification](#verification)

---

## Prerequisites

### Required Tools

- **Google Cloud SDK** (`gcloud`) - [Install Guide](https://cloud.google.com/sdk/docs/install)
- **Docker** - [Install Guide](https://docs.docker.com/get-docker/)
- **Python 3.11+** - [Install Guide](https://www.python.org/downloads/)
- **Git** - [Install Guide](https://git-scm.com/downloads)

### GCP Account Requirements

- Active GCP project with billing enabled
- Owner or Editor role on the project
- Access to the following services:
  - Cloud Run
  - Cloud Functions
  - Cloud Storage
  - BigQuery
  - Cloud Scheduler
  - Cloud Build
  - Artifact Registry

### Environment Variables

Create a `.env` file in the project root:

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash-exp

# Cloud Storage
GCS_RAW_BUCKET=doc-processing-raw
GCS_PROCESSED_BUCKET=doc-processing-processed

# BigQuery
BIGQUERY_DATASET=document_processing
BIGQUERY_LOCATION=US

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production

# Confidence Thresholds
LOW_CONFIDENCE_THRESHOLD=0.7
REVIEW_REQUIRED_THRESHOLD=0.5
```

---

## GCP Project Setup

### Step 1: Authenticate with GCP

```bash
gcloud auth login
gcloud auth application-default login
```

### Step 2: Set Project ID

```bash
export GCP_PROJECT_ID=your-project-id
gcloud config set project $GCP_PROJECT_ID
```

### Step 3: Run Setup Script

#### For Linux/Mac:

```bash
chmod +x scripts/setup_gcp.sh
export GCP_PROJECT_ID=your-project-id
./scripts/setup_gcp.sh
```

#### For Windows (PowerShell):

```powershell
$env:GCP_PROJECT_ID="your-project-id"
.\scripts\setup_gcp.ps1
```

### Step 4: Verify Setup

Check that the following were created:

- ✅ APIs enabled
- ✅ Cloud Storage buckets created
- ✅ BigQuery dataset created
- ✅ Service account created with permissions

```bash
# Verify buckets
gsutil ls -b

# Verify BigQuery dataset
bq ls

# Verify service account
gcloud iam service-accounts list
```

### Step 5: Create BigQuery Tables

Run the schema file in BigQuery console or via CLI:

```bash
# Replace placeholders in schema file
sed "s/{project_id}/${GCP_PROJECT_ID}/g; s/{dataset}/document_processing/g" bigquery/schema.sql | bq query --use_legacy_sql=false

# Create views
sed "s/{project_id}/${GCP_PROJECT_ID}/g; s/{dataset}/document_processing/g" bigquery/views.sql | bq query --use_legacy_sql=false
```

---

## Deploy Services

### Step 1: Build Docker Image

```bash
# Set project ID
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1

# Build and push image
IMAGE_NAME="gcr.io/${GCP_PROJECT_ID}/doc-processor"
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME
```

### Step 2: Deploy Cloud Run Service

```bash
gcloud run deploy doc-processor \
    --image gcr.io/${GCP_PROJECT_ID}/doc-processor \
    --platform managed \
    --region ${GCP_REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "GCP_PROJECT_ID=${GCP_PROJECT_ID},GCS_RAW_BUCKET=doc-processing-raw,GCS_PROCESSED_BUCKET=doc-processing-processed,BIGQUERY_DATASET=document_processing"
```

**Note**: Add `GEMINI_API_KEY` as a secret:

```bash
# Create secret
gcloud secrets create gemini-api-key --data-file=- <<< "your-api-key"

# Grant access
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:doc-processor-service@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Deploy with secret
gcloud run deploy doc-processor \
    --image gcr.io/${GCP_PROJECT_ID}/doc-processor \
    --update-secrets GEMINI_API_KEY=gemini-api-key:latest
```

### Step 3: Deploy Cloud Function

```bash
cd cloud_functions/document_trigger

# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe doc-processor --region ${GCP_REGION} --format 'value(status.url)')

# Deploy function
gcloud functions deploy document-trigger \
    --gen2 \
    --runtime python311 \
    --region ${GCP_REGION} \
    --trigger-bucket doc-processing-raw \
    --entry-point document_uploaded \
    --memory 512MB \
    --timeout 60s \
    --max-instances 10 \
    --set-env-vars "GCP_PROJECT_ID=${GCP_PROJECT_ID},PROCESSING_SERVICE_URL=${SERVICE_URL},BIGQUERY_DATASET=document_processing" \
    --service-account "doc-processor-service@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

cd ../..
```

### Step 4: Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe doc-processor --region ${GCP_REGION} --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test API documentation
curl $SERVICE_URL/docs
```

---

## Configure Looker

### Step 1: Set Up BigQuery Connection

1. Log in to Looker
2. Navigate to **Admin** > **Connections**
3. Click **New Connection**
4. Select **BigQuery**
5. Configure connection:
   - **Name**: `document_processing_bigquery`
   - **Project Name**: `your-project-id`
   - **Dataset**: `document_processing`
   - **Service Account JSON**: Upload service account key
   - **Application Default Credentials**: Enable if using ADC

### Step 2: Import LookML Files

1. Navigate to **Development** > **Projects**
2. Create a new project or use existing
3. Import LookML files from `looker/` directory:
   - `document_processing.model.lkml`
   - `documents.view.lkml`
   - `low_confidence_extractions.view.lkml`
   - `review_queue.view.lkml`

### Step 3: Update Connection References

Edit `document_processing.model.lkml`:

```lookml
connection: "document_processing_bigquery"
```

### Step 4: Create Dashboards

1. Create dashboard for **Processing Volume**
2. Create dashboard for **Low Confidence Extractions**
3. Create dashboard for **Review Queue**
4. Create dashboard for **Weekly Metrics**

### Step 5: Publish and Deploy

1. Validate LookML: **Development** > **Validate LookML**
2. Commit changes: **Development** > **Commit Changes**
3. Deploy to production: **Development** > **Deploy**

---

## Run Tests

### Unit Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/unit/ -v --cov=src --cov-report=term-missing
```

### Integration Tests

```bash
# Set test environment variables
export GCP_PROJECT_ID=test-project
export GEMINI_API_KEY=test-key

# Run integration tests
pytest tests/integration/ -v
```

### Full Test Suite

```bash
# For Linux/Mac
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh

# For Windows (PowerShell)
.\scripts\run_tests.ps1
```

---

## Schedule Reports

### Step 1: Set Up Cloud Scheduler

```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe doc-processor --region ${GCP_REGION} --format 'value(status.url)')

# Create scheduler job
gcloud scheduler jobs create http weekly-report-generator \
    --location ${GCP_REGION} \
    --schedule "0 9 * * 1" \
    --uri "${SERVICE_URL}/api/v1/reports/generate" \
    --http-method POST \
    --headers "Content-Type=application/json" \
    --message-body '{"week_start": null, "week_end": null}' \
    --time-zone UTC \
    --description "Generate weekly report for document processing"
```

### Step 2: Test Scheduler Job

```bash
# Test manually
gcloud scheduler jobs run weekly-report-generator --location ${GCP_REGION}
```

### Step 3: Grant Scheduler Permissions

```bash
# Grant Cloud Scheduler service account permission to invoke Cloud Run
PROJECT_NUMBER=$(gcloud projects describe ${GCP_PROJECT_ID} --format 'value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud run services add-iam-policy-binding doc-processor \
    --region ${GCP_REGION} \
    --member "serviceAccount:${SERVICE_ACCOUNT}" \
    --role "roles/run.invoker"
```

---

## Verification

### 1. Test Document Upload

```bash
# Upload test document
curl -X POST "${SERVICE_URL}/api/v1/documents/upload" \
    -F "file=@test-document.pdf" \
    -F "document_type=sow"
```

### 2. Check Processing Status

```bash
# Get document ID from upload response, then:
curl "${SERVICE_URL}/api/v1/documents/{document_id}/status"
```

### 3. Verify BigQuery Data

```bash
# Query documents table
bq query --use_legacy_sql=false \
    "SELECT * FROM \`${GCP_PROJECT_ID}.document_processing.documents\` LIMIT 10"
```

### 4. Test Weekly Report Generation

```bash
# Trigger report generation
curl -X POST "${SERVICE_URL}/api/v1/reports/generate" \
    -H "Content-Type: application/json" \
    -d '{"week_start": null, "week_end": null}'
```

### 5. Check Looker Dashboards

1. Navigate to Looker dashboards
2. Verify data is loading correctly
3. Test filters and visualizations

---

## Troubleshooting

### Common Issues

#### Cloud Run Deployment Fails

- Check Docker image is built correctly
- Verify environment variables are set
- Check service account permissions

#### Cloud Function Not Triggering

- Verify bucket trigger is configured correctly
- Check function logs: `gcloud functions logs read document-trigger --region ${GCP_REGION}`
- Verify service account has storage permissions

#### BigQuery Access Denied

- Verify service account has BigQuery roles
- Check dataset and table names are correct
- Verify dataset location matches query location

#### Looker Connection Fails

- Verify BigQuery connection credentials
- Check service account has BigQuery permissions
- Verify dataset name in LookML files

#### Weekly Reports Not Generating

- Check Cloud Scheduler job is enabled
- Verify Cloud Run service is accessible
- Check scheduler service account has invoke permissions

---

## Monitoring and Maintenance

### Cloud Run Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=doc-processor" --limit 50
```

### Cloud Function Logs

```bash
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=document-trigger" --limit 50
```

### BigQuery Query Performance

Monitor query performance in BigQuery console:
- Slow queries
- High-cost queries
- Failed queries

### Cost Monitoring

Set up billing alerts in GCP Console:
1. Navigate to **Billing** > **Budgets & alerts**
2. Create budget for project
3. Set alerts for cost thresholds

---

## Next Steps

After successful deployment:

1. **Monitor System**: Set up alerts for errors and performance
2. **Optimize Performance**: Review BigQuery queries and indexes
3. **Scale Resources**: Adjust Cloud Run and Cloud Function scaling
4. **Update Dashboards**: Refine Looker dashboards based on usage
5. **Document Workflows**: Document operational procedures

---

## Support

For issues or questions:
- Check logs in Cloud Console
- Review API documentation: `/docs` endpoint
- Consult user guide: `docs/USER_GUIDE.md`
