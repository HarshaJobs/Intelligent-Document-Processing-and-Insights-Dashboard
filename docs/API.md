# API Documentation

## Intelligent Document Processing API

RESTful API for processing SOWs, contracts, and other business documents using Gemini AI for entity extraction.

### Base URL

```
https://your-cloud-run-service.run.app
```

### Authentication

Currently, the API does not require authentication for development. In production, implement authentication using:
- Google Cloud IAM
- OAuth 2.0
- API Keys

### Endpoints

#### Health Check

```
GET /health
```

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-01T10:00:00Z"
}
```

#### Upload Document

```
POST /api/v1/documents/upload
```

Upload a document for processing.

**Parameters:**
- `file` (multipart/form-data): Document file (PDF, DOCX, or TXT)
- `document_type` (query, optional): Document type hint (sow, contract, email, amendment, msa, other)

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "sow-example.pdf",
  "status": "pending",
  "message": "Document queued for processing. ID: 550e8400-e29b-41d4-a716-446655440000"
}
```

#### Get Document Status

```
GET /api/v1/documents/{document_id}/status
```

Get processing status for a document.

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "document_type": "sow",
  "confidence": 0.85,
  "processed_at": "2024-03-01T10:05:00Z",
  "entities_extracted": 12
}
```

#### Get Extracted Entities

```
GET /api/v1/documents/{document_id}/entities
```

Get all extracted entities for a processed document.

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "sow",
  "structure_type": "structured",
  "overall_confidence": 0.85,
  "stakeholders": [
    {
      "entity_id": "stakeholder-001",
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "stakeholder_type": "project_manager",
      "name": "John Smith",
      "role": "Project Manager",
      "organization": "Tech Solutions Inc.",
      "email": "john.smith@techsolutions.com",
      "phone": null,
      "confidence": 0.9,
      "extraction_timestamp": "2024-03-01T10:05:00Z"
    }
  ],
  "deliverables": [...],
  "deadlines": [...],
  "financials": [...],
  "extraction_timestamp": "2024-03-01T10:05:00Z",
  "processing_time_ms": 3500,
  "needs_review": false,
  "review_reasons": []
}
```

#### List Documents

```
GET /api/v1/documents/
```

List documents with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by processing status
- `document_type` (optional): Filter by document type
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 50): Results per page

**Response:**
```json
{
  "documents": [...],
  "total_count": 150,
  "page": 1,
  "page_size": 50
}
```

#### Get Review Queue

```
GET /api/v1/documents/review-queue
```

Get documents that require manual review.

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 50): Results per page

**Response:**
```json
{
  "documents": [...],
  "total_count": 10,
  "page": 1,
  "page_size": 50
}
```

#### Process Document

```
POST /api/v1/documents/process
```

Process a document from Cloud Storage (called by Cloud Function).

**Request Body:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "bucket": "doc-processing-raw",
  "blob_path": "2024/03/01/document-id.pdf",
  "content_type": "application/pdf"
}
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "overall_confidence": 0.85,
  "entities_extracted": 12,
  "needs_review": false
}
```

#### Reprocess Document

```
POST /api/v1/documents/{document_id}/reprocess
```

Trigger reprocessing of a document.

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "reprocessing_queued",
  "message": "Document has been queued for reprocessing"
}
```

### Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Status Codes:**
- `400`: Bad Request - Invalid input parameters
- `404`: Not Found - Document or resource not found
- `500`: Internal Server Error - Processing failure

### Rate Limiting

No rate limiting is currently implemented. Consider adding rate limiting for production:
- Per-IP limits
- Per-API-key limits
- Per-user limits

### Example Usage

#### Upload and Process a Document

```bash
# Upload document
curl -X POST "https://api.example.com/api/v1/documents/upload" \
  -F "file=@sow-example.pdf" \
  -F "document_type=sow"

# Check status
curl "https://api.example.com/api/v1/documents/{document_id}/status"

# Get extracted entities
curl "https://api.example.com/api/v1/documents/{document_id}/entities"
```

#### Get Review Queue

```bash
curl "https://api.example.com/api/v1/documents/review-queue?page=1&page_size=50"
```
