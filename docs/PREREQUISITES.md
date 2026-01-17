# Prerequisites Setup Guide

Before deploying the Intelligent Document Processing Dashboard, you need to set up the required tools and services.

## Required Tools

### 1. Google Cloud SDK (gcloud)

**Windows:**
1. Download Google Cloud SDK installer from: https://cloud.google.com/sdk/docs/install-sdk#windows
2. Run the installer and follow the setup wizard
3. Open a new PowerShell/Command Prompt window
4. Verify installation:
   ```powershell
   gcloud --version
   ```

**Alternative Installation (using PowerShell):**
```powershell
# Download and install via PowerShell
Invoke-WebRequest -Uri "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe" -OutFile "$env:TEMP\GoogleCloudSDKInstaller.exe"
Start-Process -FilePath "$env:TEMP\GoogleCloudSDKInstaller.exe" -Wait
```

**Linux/Mac:**
```bash
# Download and install
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### 2. Docker Desktop

**Windows:**
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Start Docker Desktop
4. Verify installation:
   ```powershell
   docker --version
   ```

### 3. Python 3.11+

**Windows:**
1. Download Python from: https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```powershell
   python --version
   ```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3-pip

# Mac (using Homebrew)
brew install python@3.11
```

### 4. Git (if not already installed)

**Windows:**
- Download from: https://git-scm.com/download/win
- Install using default options

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt install git

# Mac
brew install git
```

## GCP Account Setup

### 1. Create GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `intelligent-doc-processing`
4. Note the Project ID (e.g., `intelligent-doc-processing-123456`)
5. Click "Create"

### 2. Enable Billing

1. Go to [Billing](https://console.cloud.google.com/billing)
2. Link your GCP project to a billing account
3. Enable billing for the project

### 3. Authenticate with gcloud

```powershell
# Login to GCP
gcloud auth login

# Set default project
gcloud config set project YOUR_PROJECT_ID

# Enable Application Default Credentials
gcloud auth application-default login
```

## Required GCP APIs

Enable the following APIs in GCP Console:

1. **AI Platform API** (`aiplatform.googleapis.com`)
2. **BigQuery API** (`bigquery.googleapis.com`)
3. **Cloud Storage API** (`storage.googleapis.com`)
4. **Cloud Functions API** (`cloudfunctions.googleapis.com`)
5. **Cloud Run API** (`run.googleapis.com`)
6. **Cloud Scheduler API** (`cloudscheduler.googleapis.com`)
7. **Cloud Logging API** (`logging.googleapis.com`)
8. **Cloud Build API** (`cloudbuild.googleapis.com`)
9. **Artifact Registry API** (`artifactregistry.googleapis.com`)

**Enable via gcloud (after installation):**
```powershell
$PROJECT_ID = "your-project-id"
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID
gcloud services enable storage.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudfunctions.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID
gcloud services enable logging.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID
```

## Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the API key and save it securely
4. Add to your `.env` file: `GEMINI_API_KEY=your-api-key`

## Python Environment Setup

### 1. Create Virtual Environment

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```powershell
# Install project dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Environment Variables Setup

1. Copy the example environment file:
   ```powershell
   Copy-Item env.example .env
   ```

2. Edit `.env` file with your configuration:
   ```powershell
   # Edit .env file with your values
   notepad .env
   ```

3. Required variables:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GEMINI_API_KEY`: Your Gemini API key
   - `GCS_RAW_BUCKET`: Name for raw documents bucket
   - `GCS_PROCESSED_BUCKET`: Name for processed documents bucket

## Verification Checklist

Before proceeding with deployment, verify:

- [ ] Google Cloud SDK installed and authenticated
- [ ] Docker Desktop installed and running
- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] GCP project created
- [ ] Billing enabled for GCP project
- [ ] Required APIs enabled
- [ ] Gemini API key obtained
- [ ] Python virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file configured

## Next Steps

Once all prerequisites are met:

1. **Set Environment Variables:**
   ```powershell
   $env:GCP_PROJECT_ID = "your-project-id"
   $env:GEMINI_API_KEY = "your-api-key"
   ```

2. **Run GCP Setup:**
   ```powershell
   .\scripts\setup_gcp.ps1
   ```

3. **Deploy Services:**
   ```powershell
   .\scripts\deploy.ps1
   ```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.
