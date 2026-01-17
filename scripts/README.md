# Deployment Scripts

Scripts for deploying the Intelligent Document Processing and Insights Dashboard to GCP.

## Scripts Overview

| Script | Description | Platform |
|--------|-------------|----------|
| `setup_gcp.sh` / `setup_gcp.ps1` | Set up GCP project (APIs, buckets, BigQuery) | Linux/Mac / Windows |
| `deploy.sh` / `deploy.ps1` | Deploy Cloud Run and Cloud Functions | Linux/Mac / Windows |
| `run_tests.sh` / `run_tests.ps1` | Execute unit and integration tests | Linux/Mac / Windows |
| `setup_scheduler.sh` | Set up Cloud Scheduler for weekly reports | Linux/Mac |

## Quick Start

### 1. Set Environment Variables

```bash
export GCP_PROJECT_ID=your-project-id
export GEMINI_API_KEY=your-gemini-api-key
```

Or on Windows (PowerShell):
```powershell
$env:GCP_PROJECT_ID="your-project-id"
$env:GEMINI_API_KEY="your-gemini-api-key"
```

### 2. Run Setup Script

**Linux/Mac:**
```bash
chmod +x scripts/setup_gcp.sh
./scripts/setup_gcp.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup_gcp.ps1
```

### 3. Deploy Services

**Linux/Mac:**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy.ps1
```

### 4. Run Tests

**Linux/Mac:**
```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\run_tests.ps1
```

### 5. Set Up Scheduler

```bash
chmod +x scripts/setup_scheduler.sh
./scripts/setup_scheduler.sh
```

## Prerequisites

- Google Cloud SDK installed and authenticated
- Docker installed (for Cloud Run deployment)
- Python 3.11+ with dependencies installed
- Required environment variables set

## Detailed Instructions

See [DEPLOYMENT.md](../docs/DEPLOYMENT.md) for comprehensive deployment guide.
