# Intelligent Document Processing and Insights Dashboard

An AI-powered document processing system that extracts key entities from SOWs, contracts, and business documents using Google's Gemini API, stores results in BigQuery, and visualizes insights through Looker dashboards.

## Features

- **Document Ingestion**: Upload PDF, DOCX, or TXT files via API or Cloud Storage
- **AI-Powered Extraction**: Extract stakeholders, deliverables, deadlines using Gemini API
- **Confidence Scoring**: Flag low-confidence extractions for manual review
- **Audit Logging**: Complete audit trail via Cloud Logging
- **BigQuery Storage**: Structured storage for analytics and reporting
- **Looker Dashboards**: Visualize processing volume and extraction insights
- **Automated Reports**: Weekly GenAI-powered summary reports

## Architecture

```
Cloud Storage (Raw) → Cloud Function → Cloud Run (FastAPI)
                                            ↓
                                      Gemini API
                                            ↓
                                      BigQuery → Looker Studio
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud SDK
- GCP Project with enabled APIs:
  - Generative Language API (Gemini)
  - Cloud Storage
  - BigQuery
  - Cloud Functions
  - Cloud Run
  - Cloud Logging

### Local Development

1. **Clone and setup environment:**
   ```bash
   cd "Intelligent Document Processing and Insights Dashboard"
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -e ".[dev]"
   ```

2. **Configure environment:**
   ```bash
   copy .env.example .env
   # Edit .env with your GCP settings
   ```

3. **Run locally:**
   ```bash
   uvicorn src.api.main:app --reload --port 8080
   ```

4. **Run with Docker:**
   ```bash
   docker-compose up
   ```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/documents/upload` | POST | Upload a document |
| `/api/v1/documents/{id}/status` | GET | Get processing status |
| `/api/v1/documents/{id}/entities` | GET | Get extracted entities |
| `/api/v1/documents/` | GET | List documents |
| `/api/v1/documents/review-queue` | GET | Get documents needing review |

### Project Structure

```
├── src/
│   ├── api/              # FastAPI application
│   │   ├── main.py       # Entry point
│   │   ├── routes/       # API routes
│   │   └── models/       # Pydantic models
│   ├── ingestion/        # Document ingestion
│   │   ├── storage_handler.py
│   │   ├── audit_logger.py
│   │   ├── metadata_extractor.py
│   │   └── status_tracker.py
│   ├── extraction/       # Gemini extraction (Phase 3)
│   ├── storage/          # BigQuery operations (Phase 5)
│   └── reports/          # Weekly reports (Phase 7)
├── cloud_functions/      # Cloud Function triggers
├── bigquery/             # Schema definitions
├── tests/                # Unit and integration tests
├── Dockerfile
└── docker-compose.yml
```

## Deployment

### Deploy to Cloud Run

```bash
# Build and push container
gcloud builds submit --tag gcr.io/$PROJECT_ID/doc-processor

# Deploy
gcloud run deploy doc-processor \
  --image gcr.io/$PROJECT_ID/doc-processor \
  --platform managed \
  --region us-central1 \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID"
```

### Deploy Cloud Function

```bash
cd cloud_functions/document_trigger
gcloud functions deploy document-trigger \
  --gen2 \
  --runtime python311 \
  --trigger-event google.cloud.storage.object.v1.finalized \
  --trigger-resource $RAW_BUCKET
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | GCP Project ID | Required |
| `GEMINI_API_KEY` | Gemini API Key | Required |
| `GCS_RAW_BUCKET` | Raw documents bucket | doc-processing-raw |
| `GCS_PROCESSED_BUCKET` | Processed results bucket | doc-processing-processed |
| `BIGQUERY_DATASET` | BigQuery dataset name | document_processing |
| `LOW_CONFIDENCE_THRESHOLD` | Threshold for flagging | 0.7 |

## License

MIT
