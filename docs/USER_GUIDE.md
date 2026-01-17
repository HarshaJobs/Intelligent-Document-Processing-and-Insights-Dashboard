# User Guide

## Intelligent Document Processing and Insights Dashboard

This guide provides instructions for using the document processing system, dashboard, and review workflows.

### Table of Contents

1. [Overview](#overview)
2. [Uploading Documents](#uploading-documents)
3. [Viewing Processing Status](#viewing-processing-status)
4. [Reviewing Low-Confidence Extractions](#reviewing-low-confidence-extractions)
5. [Using the Looker Dashboard](#using-the-looker-dashboard)
6. [Weekly Reports](#weekly-reports)

---

## Overview

The Intelligent Document Processing system extracts structured entities (stakeholders, deliverables, deadlines, financials) from business documents like SOWs and contracts using Google's Gemini AI.

**Key Features:**
- Automatic entity extraction from documents
- Confidence scoring for quality assessment
- Manual review workflow for low-confidence extractions
- Dashboard visualization of processing metrics
- Automated weekly reports

---

## Uploading Documents

### Supported Formats

- **PDF** (.pdf)
- **Word Documents** (.docx)
- **Text Files** (.txt)

### Upload Methods

#### 1. API Upload

Use the REST API to upload documents:

```bash
curl -X POST "https://api.example.com/api/v1/documents/upload" \
  -F "file=@document.pdf" \
  -F "document_type=sow"
```

#### 2. Cloud Storage Upload

Upload directly to Google Cloud Storage bucket:

```bash
gsutil cp document.pdf gs://doc-processing-raw/
```

The Cloud Function will automatically trigger processing.

---

## Viewing Processing Status

### Check Status via API

```bash
curl "https://api.example.com/api/v1/documents/{document_id}/status"
```

**Response includes:**
- Processing status (pending, processing, completed, failed, review_required)
- Overall confidence score
- Number of entities extracted
- Processing timestamps

### Processing Statuses

- **pending**: Document uploaded, waiting to be processed
- **processing**: Currently being analyzed by Gemini AI
- **completed**: Successfully processed and entities extracted
- **failed**: Processing failed due to error
- **review_required**: Processed but requires manual review due to low confidence

---

## Reviewing Low-Confidence Extractions

Documents with low confidence scores (< 0.7) are automatically flagged for review.

### Access Review Queue

#### Via API

```bash
curl "https://api.example.com/api/v1/documents/review-queue"
```

#### Via Looker Dashboard

Navigate to the **Review Queue** explore in Looker.

### Review Workflow

1. **View Flagged Documents**: Review queue shows documents needing attention
2. **Check Entity Confidence**: Review individual entity confidence scores
3. **Manually Correct**: Update incorrect extractions if needed
4. **Approve/Reject**: Mark items as reviewed or dismissed
5. **Reprocess**: Trigger reprocessing after corrections

---

## Using the Looker Dashboard

### Accessing the Dashboard

1. Open Looker at your organization's Looker URL
2. Navigate to **Document Processing** folder
3. Select a dashboard or explore

### Available Explores

#### 1. Processing Volume

- View documents processed over time
- Filter by document type, status, date range
- Metrics: total documents, average confidence, success rate

#### 2. Low Confidence Extractions

- List all entities with confidence < 0.7
- Filter by entity type, document type
- Sort by confidence score or date

#### 3. Review Queue

- View pending review items
- Filter by severity, status, reviewer
- Track time pending in queue

#### 4. Entity Extraction Statistics

- Extraction counts by entity type
- Confidence trends over time
- Success rates by document type

#### 5. Weekly Metrics

- Weekly aggregated metrics
- Processing volume trends
- Quality metrics over time

#### 6. Stakeholder Analysis

- Most common stakeholders
- Organizations and roles
- Cross-document analysis

#### 7. Deadline Tracking

- Upcoming deadlines extracted from documents
- Filter by deadline type, date range
- Track firm vs. flexible deadlines

#### 8. Financial Summary

- Financial terms extracted
- Total amounts by currency
- Payment terms summary

### Creating Custom Dashboards

1. Open an explore (e.g., "Processing Volume")
2. Select dimensions (e.g., document_type, upload_date)
3. Add measures (e.g., count, avg_confidence)
4. Apply filters as needed
5. Save as dashboard tile

---

## Weekly Reports

### Automated Reports

Weekly reports are automatically generated every Monday for the previous week.

**Report includes:**
- Executive summary
- Processing volume highlights
- Quality metrics and confidence trends
- Items requiring attention
- Recommendations for next week

### Accessing Reports

#### Via BigQuery

Query the `weekly_reports` table:

```sql
SELECT 
  report_date,
  week_start,
  week_end,
  documents_processed,
  avg_confidence,
  report_content
FROM `project.dataset.weekly_reports`
ORDER BY report_date DESC
LIMIT 10;
```

#### Via Looker

Create a dashboard tile from the `weekly_reports` view.

### Manual Report Generation

Generate a report for a specific week via API:

```bash
curl -X POST "https://api.example.com/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "week_start": "2024-03-01",
    "week_end": "2024-03-07"
  }'
```

---

## Tips and Best Practices

### Improving Extraction Quality

1. **Use Structured Documents**: Structured documents (with clear sections) extract better
2. **Provide Document Type Hints**: Specify document type when uploading for better accuracy
3. **Review Low Confidence Items**: Regularly review flagged items to improve training data

### Dashboard Best Practices

1. **Set Appropriate Date Ranges**: Use date filters to focus on relevant time periods
2. **Monitor Confidence Trends**: Watch for declining confidence scores over time
3. **Track Review Queue**: Ensure review queue doesn't grow too large

### Troubleshooting

#### Low Confidence Scores

- Check if document is structured properly
- Verify document type is correct
- Review similar documents for patterns

#### Processing Failures

- Check document format is supported
- Verify file is not corrupted
- Review error messages in processing logs

#### Missing Entities

- Some entities may not be present in all documents
- Check document content manually
- Consider reprocessing with different settings

---

## Support

For issues or questions:

1. Check API documentation: `/docs`
2. Review error messages in Looker logs
3. Contact your system administrator

---

## Appendix

### Document Type Classifications

- **sow**: Statement of Work
- **contract**: Contract or agreement
- **email**: Email correspondence
- **amendment**: Amendment or addendum
- **msa**: Master Service Agreement
- **other**: Other document types

### Entity Types

- **stakeholders**: People or organizations involved
- **deliverables**: Products, services, or outcomes
- **deadlines**: Important dates and milestones
- **financials**: Financial terms and amounts

### Confidence Thresholds

- **High Confidence**: >= 0.7 (automatically approved)
- **Low Confidence**: < 0.7 (flagged for review)
- **Review Required**: < 0.5 (mandatory manual review)
