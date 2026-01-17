# Quick Start Guide

Get the Intelligent Document Processing Dashboard up and running quickly.

## Prerequisites Check

First, ensure you have all prerequisites installed. See [PREREQUISITES.md](PREREQUISITES.md) for detailed setup instructions.

```powershell
# Check installations
gcloud --version
docker --version
python --version
git --version
```

## Step 1: Install Prerequisites

If prerequisites are not installed:

1. **Install Google Cloud SDK:**
   - Download from: https://cloud.google.com/sdk/docs/install-sdk#windows
   - Or use PowerShell installer (see PREREQUISITES.md)

2. **Install Docker Desktop:**
   - Download from: https://www.docker.com/products/docker-desktop

3. **Install Python 3.11+:**
   - Download from: https://www.python.org/downloads/

## Step 2: Set Up GCP Project

1. **Create GCP Project:**
   - Go to https://console.cloud.google.com/
   - Create a new project
   - Note the Project ID

2. **Enable Billing:**
   - Link billing account to your project

3. **Authenticate:**
   ```powershell
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth application-default login
   ```

## Step 3: Configure Environment

1. **Create .env file:**
   ```powershell
   Copy-Item env.example .env
   ```

2. **Edit .env with your values:**
   - Set `GCP_PROJECT_ID=your-project-id`
   - Set `GEMINI_API_KEY=your-gemini-api-key`
   - Update bucket names if needed

3. **Set environment variables:**
   ```powershell
   $env:GCP_PROJECT_ID = "your-project-id"
   $env:GEMINI_API_KEY = "your-api-key"
   ```

## Step 4: Set Up Python Environment

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"
```

## Step 5: Run GCP Setup

```powershell
# Run setup script
.\scripts\setup_gcp.ps1
```

This will:
- Enable required APIs
- Create Cloud Storage buckets
- Create BigQuery dataset
- Create service account
- Set up permissions

## Step 6: Create BigQuery Tables

1. **Go to BigQuery Console:**
   - Navigate to: https://console.cloud.google.com/bigquery

2. **Run schema.sql:**
   - Open `bigquery/schema.sql`
   - Replace `{project_id}` and `{dataset}` placeholders
   - Execute in BigQuery console

3. **Run views.sql:**
   - Open `bigquery/views.sql`
   - Replace placeholders
   - Execute in BigQuery console

## Step 7: Deploy Services

```powershell
# Deploy Cloud Run and Cloud Functions
.\scripts\deploy.ps1
```

This will:
- Build Docker image
- Push to Container Registry
- Deploy Cloud Run service
- Deploy Cloud Function

## Step 8: Test Deployment

```powershell
# Get service URL
$SERVICE_URL = gcloud run services describe doc-processor --region us-central1 --format 'value(status.url)'

# Test health endpoint
curl $SERVICE_URL/health

# Test API docs
Start-Process $SERVICE_URL/docs
```

## Step 9: Run Tests

```powershell
# Run test suite
.\scripts\run_tests.ps1
```

## Step 10: Set Up Cloud Scheduler

```powershell
# Get service URL
$SERVICE_URL = gcloud run services describe doc-processor --region us-central1 --format 'value(status.url)'
$env:PROCESSING_SERVICE_URL = $SERVICE_URL

# Create scheduler job (use bash script or create manually)
# See docs/DEPLOYMENT.md for manual setup
```

## Step 11: Configure Looker (Optional)

1. **Create BigQuery Connection:**
   - Log in to Looker
   - Go to Admin > Connections
   - Create BigQuery connection

2. **Import LookML Files:**
   - Upload files from `looker/` directory
   - Update connection name in `document_processing.model.lkml`

3. **Create Dashboards:**
   - Create dashboards for processing volume, review queue, etc.

## Troubleshooting

### gcloud not found
- Install Google Cloud SDK (see PREREQUISITES.md)
- Restart PowerShell after installation

### Docker not running
- Start Docker Desktop
- Wait for it to fully start

### Permission errors
- Verify you're authenticated: `gcloud auth list`
- Check project permissions in GCP Console

### API errors
- Verify APIs are enabled: Check in GCP Console > APIs & Services
- Re-run setup script if needed

## Next Steps

- **Detailed Deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **User Guide:** See [USER_GUIDE.md](USER_GUIDE.md)
- **API Documentation:** See [API.md](API.md)

## Getting Help

- Check logs in GCP Console
- Review error messages in deployment output
- Consult documentation in `docs/` directory
