# Next Steps - Deployment Checklist

This document provides a quick checklist for deploying the Intelligent Document Processing and Insights Dashboard.

## ✅ Quick Start Checklist

### 1. GCP Project Setup

- [ ] Authenticate with GCP: `gcloud auth login`
- [ ] Set project ID: `export GCP_PROJECT_ID=your-project-id`
- [ ] Run setup script: `./scripts/setup_gcp.sh` (Linux/Mac) or `.\scripts\setup_gcp.ps1` (Windows)
- [ ] Verify APIs enabled in GCP Console
- [ ] Verify buckets created: `gsutil ls -b`
- [ ] Verify BigQuery dataset created: `bq ls`
- [ ] Create BigQuery tables: Run `bigquery/schema.sql`
- [ ] Create BigQuery views: Run `bigquery/views.sql`

### 2. Environment Configuration

- [ ] Copy `.env.example` to `.env`
- [ ] Update `.env` with your project settings
- [ ] Set `GEMINI_API_KEY` (use GCP Secret Manager in production)
- [ ] Set `GCP_PROJECT_ID`
- [ ] Verify all environment variables are set

### 3. Deploy Services

- [ ] Build Docker image: `docker build -t gcr.io/$PROJECT_ID/doc-processor .`
- [ ] Push image: `docker push gcr.io/$PROJECT_ID/doc-processor`
- [ ] Deploy Cloud Run: `./scripts/deploy.sh` or `.\scripts\deploy.ps1`
- [ ] Deploy Cloud Function: `./scripts/deploy.sh` or `.\scripts\deploy.ps1`
- [ ] Test health endpoint: `curl $SERVICE_URL/health`
- [ ] Verify API docs: `curl $SERVICE_URL/docs`

### 4. Configure Looker

- [ ] Log in to Looker
- [ ] Create BigQuery connection: `Admin > Connections > New Connection`
- [ ] Import LookML files from `looker/` directory
- [ ] Update connection name in `document_processing.model.lkml`
- [ ] Validate LookML: `Development > Validate LookML`
- [ ] Create dashboards for:
  - [ ] Processing Volume
  - [ ] Low Confidence Extractions
  - [ ] Review Queue
  - [ ] Weekly Metrics
- [ ] Commit and deploy LookML

### 5. Run Tests

- [ ] Install test dependencies: `pip install -e ".[dev]"`
- [ ] Run unit tests: `pytest tests/unit/ -v`
- [ ] Run integration tests: `pytest tests/integration/ -v`
- [ ] Check test coverage: `pytest --cov=src --cov-report=html`
- [ ] Review coverage report: `htmlcov/index.html`

### 6. Schedule Reports

- [ ] Get Cloud Run service URL
- [ ] Create Cloud Scheduler job: `./scripts/setup_scheduler.sh`
- [ ] Grant scheduler permissions to invoke Cloud Run
- [ ] Test scheduler manually: `gcloud scheduler jobs run weekly-report-generator --location=us-central1`
- [ ] Verify report generation in BigQuery: `SELECT * FROM weekly_reports ORDER BY generated_at DESC LIMIT 1`

### 7. Verification

- [ ] Upload test document via API
- [ ] Verify document processing completes
- [ ] Check entities extracted in BigQuery
- [ ] Verify low-confidence extractions flagged
- [ ] Check review queue in Looker dashboard
- [ ] Generate test weekly report
- [ ] Verify all services are accessible

## 📋 Detailed Instructions

For detailed step-by-step instructions, see:
- **Deployment Guide**: [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- **API Documentation**: [docs/API.md](API.md)
- **User Guide**: [docs/USER_GUIDE.md](USER_GUIDE.md)

## 🚀 Automated Deployment

You can use the provided scripts for automated deployment:

```bash
# Complete deployment (Linux/Mac)
./scripts/setup_gcp.sh      # Step 1: GCP setup
./scripts/deploy.sh          # Step 2: Deploy services
./scripts/run_tests.sh       # Step 3: Run tests
./scripts/setup_scheduler.sh # Step 4: Schedule reports
```

```powershell
# Complete deployment (Windows PowerShell)
.\scripts\setup_gcp.ps1      # Step 1: GCP setup
.\scripts\deploy.ps1          # Step 2: Deploy services
.\scripts\run_tests.ps1       # Step 3: Run tests
# Step 4: Use setup_scheduler.sh or create manually
```

## ⚠️ Important Notes

1. **Environment Variables**: Store sensitive values (like `GEMINI_API_KEY`) in GCP Secret Manager for production
2. **Service Account**: Ensure service account has all required permissions
3. **BigQuery Schema**: Run `schema.sql` before `views.sql`
4. **Looker Connection**: Test BigQuery connection before importing LookML
5. **Cloud Scheduler**: Verify Cloud Run service is accessible before scheduling

## 🔍 Troubleshooting

Common issues and solutions:

- **Deployment fails**: Check Docker image build, verify environment variables
- **Function not triggering**: Check bucket trigger, verify service account permissions
- **BigQuery errors**: Verify dataset exists, check service account roles
- **Looker connection fails**: Verify BigQuery credentials, check dataset name
- **Reports not generating**: Check Cloud Scheduler job status, verify service URL

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for detailed troubleshooting guide.

## 📞 Support

For additional help:
- Review logs in GCP Console
- Check API documentation at `/docs` endpoint
- Consult user guide: [docs/USER_GUIDE.md](USER_GUIDE.md)
