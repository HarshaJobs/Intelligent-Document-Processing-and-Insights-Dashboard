# Setup Checklist

Use this checklist to track your deployment progress.

## Prerequisites

- [ ] Google Cloud SDK installed (`gcloud --version`)
- [ ] Docker Desktop installed and running (`docker --version`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Git installed (`git --version`)
- [ ] GCP account created
- [ ] GCP project created with Project ID noted
- [ ] Billing enabled for GCP project

## GCP Authentication

- [ ] Logged in to GCP: `gcloud auth login`
- [ ] Default project set: `gcloud config set project YOUR_PROJECT_ID`
- [ ] Application Default Credentials configured: `gcloud auth application-default login`

## Gemini API

- [ ] Gemini API key obtained from https://makersuite.google.com/app/apikey
- [ ] API key saved securely

## Environment Configuration

- [ ] `.env` file created from `env.example`
- [ ] `GCP_PROJECT_ID` set in `.env`
- [ ] `GEMINI_API_KEY` set in `.env`
- [ ] Environment variables exported or set in PowerShell

## Python Environment

- [ ] Virtual environment created: `python -m venv venv`
- [ ] Virtual environment activated: `.\venv\Scripts\Activate.ps1`
- [ ] Dependencies installed: `pip install -e ".[dev]"`

## GCP Setup (Step 1)

- [ ] Run `.\scripts\setup_gcp.ps1` successfully
- [ ] Required APIs enabled (check in GCP Console)
- [ ] Cloud Storage buckets created
  - [ ] `doc-processing-raw` bucket exists
  - [ ] `doc-processing-processed` bucket exists
- [ ] BigQuery dataset created
- [ ] Service account created: `doc-processor-service`

## BigQuery Tables (Step 2)

- [ ] `bigquery/schema.sql` executed in BigQuery Console
- [ ] Tables created:
  - [ ] `documents`
  - [ ] `stakeholders`
  - [ ] `deliverables`
  - [ ] `deadlines`
  - [ ] `financials`
  - [ ] `processing_log`
  - [ ] `review_queue`
  - [ ] `weekly_reports`
- [ ] `bigquery/views.sql` executed
- [ ] Views created and validated

## Service Deployment (Step 3)

- [ ] Docker image built successfully
- [ ] Docker image pushed to Container Registry
- [ ] Cloud Run service deployed: `doc-processor`
- [ ] Cloud Run service URL obtained
- [ ] Cloud Function deployed: `document-trigger`
- [ ] Health endpoint tested: `curl $SERVICE_URL/health`

## Testing (Step 4)

- [ ] Unit tests run successfully: `pytest tests/unit/ -v`
- [ ] Integration tests run (if applicable)
- [ ] Coverage report generated
- [ ] Test document upload successful
- [ ] Processing pipeline verified

## Cloud Scheduler (Step 5)

- [ ] Cloud Scheduler job created: `weekly-report-generator`
- [ ] Schedule configured: Every Monday at 9 AM UTC
- [ ] Cloud Run service permission granted for scheduler
- [ ] Manual test run successful: `gcloud scheduler jobs run weekly-report-generator`

## Looker Configuration (Step 6 - Optional)

- [ ] Looker account access
- [ ] BigQuery connection created in Looker
- [ ] LookML files imported:
  - [ ] `document_processing.model.lkml`
  - [ ] `documents.view.lkml`
  - [ ] `low_confidence_extractions.view.lkml`
  - [ ] `review_queue.view.lkml`
- [ ] LookML validated
- [ ] Dashboards created:
  - [ ] Processing Volume
  - [ ] Low Confidence Extractions
  - [ ] Review Queue
  - [ ] Weekly Metrics

## Verification

- [ ] Test document uploaded via API
- [ ] Document processed successfully
- [ ] Entities extracted and stored in BigQuery
- [ ] Low-confidence extractions flagged correctly
- [ ] Review queue populated (if applicable)
- [ ] Weekly report generated successfully
- [ ] All services accessible and functional

## Documentation

- [ ] Read [DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [ ] Read [USER_GUIDE.md](docs/USER_GUIDE.md)
- [ ] Read [API.md](docs/API.md)
- [ ] Team members briefed on system

## Next Steps

- [ ] Monitor system logs
- [ ] Set up billing alerts
- [ ] Configure additional dashboards
- [ ] Document operational procedures
- [ ] Plan for scaling

---

**Notes:**
- Check off items as you complete them
- Refer to detailed documentation for each step
- Don't hesitate to revisit previous steps if needed
