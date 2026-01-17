-- BigQuery Views for Dashboard Consumption
-- These views provide optimized queries for Looker dashboard

-- Document processing summary view
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_document_processing_summary` AS
SELECT
    DATE(upload_timestamp) AS processing_date,
    document_type,
    structure_type,
    processing_status,
    COUNT(*) AS document_count,
    AVG(overall_confidence) AS avg_confidence,
    COUNTIF(overall_confidence < 0.7) AS low_confidence_count,
    COUNTIF(processing_status = 'review_required') AS review_required_count,
    SUM(raw_text_length) AS total_text_length
FROM `{project_id}.{dataset}.documents`
WHERE upload_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY processing_date, document_type, structure_type, processing_status;

-- Low confidence extractions view (for manual review dashboard)
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_low_confidence_extractions` AS
SELECT
    d.document_id,
    d.filename,
    d.document_type,
    d.upload_timestamp,
    d.overall_confidence AS document_confidence,
    'stakeholder' AS entity_type,
    s.entity_id,
    s.name AS entity_name,
    s.confidence AS entity_confidence,
    s.stakeholder_type
FROM `{project_id}.{dataset}.documents` d
INNER JOIN `{project_id}.{dataset}.stakeholders` s ON d.document_id = s.document_id
WHERE s.confidence < 0.7
  AND d.processing_status = 'completed'

UNION ALL

SELECT
    d.document_id,
    d.filename,
    d.document_type,
    d.upload_timestamp,
    d.overall_confidence AS document_confidence,
    'deliverable' AS entity_type,
    del.entity_id,
    del.deliverable_name AS entity_name,
    del.confidence AS entity_confidence,
    NULL AS stakeholder_type
FROM `{project_id}.{dataset}.documents` d
INNER JOIN `{project_id}.{dataset}.deliverables` del ON d.document_id = del.document_id
WHERE del.confidence < 0.7
  AND d.processing_status = 'completed'

UNION ALL

SELECT
    d.document_id,
    d.filename,
    d.document_type,
    d.upload_timestamp,
    d.overall_confidence AS document_confidence,
    'deadline' AS entity_type,
    dl.entity_id,
    CAST(dl.deadline_date AS STRING) AS entity_name,
    dl.confidence AS entity_confidence,
    NULL AS stakeholder_type
FROM `{project_id}.{dataset}.documents` d
INNER JOIN `{project_id}.{dataset}.deadlines` dl ON d.document_id = dl.document_id
WHERE dl.confidence < 0.7
  AND d.processing_status = 'completed'

UNION ALL

SELECT
    d.document_id,
    d.filename,
    d.document_type,
    d.upload_timestamp,
    d.overall_confidence AS document_confidence,
    'financial' AS entity_type,
    f.entity_id,
    f.description AS entity_name,
    f.confidence AS entity_confidence,
    NULL AS stakeholder_type
FROM `{project_id}.{dataset}.documents` d
INNER JOIN `{project_id}.{dataset}.financials` f ON d.document_id = f.document_id
WHERE f.confidence < 0.7
  AND d.processing_status = 'completed';

-- Entity extraction statistics view
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_entity_extraction_stats` AS
SELECT
    DATE(d.upload_timestamp) AS extraction_date,
    d.document_type,
    COUNT(DISTINCT d.document_id) AS documents_processed,
    COUNT(DISTINCT s.entity_id) AS stakeholders_extracted,
    COUNT(DISTINCT del.entity_id) AS deliverables_extracted,
    COUNT(DISTINCT dl.entity_id) AS deadlines_extracted,
    COUNT(DISTINCT f.entity_id) AS financials_extracted,
    AVG(s.confidence) AS avg_stakeholder_confidence,
    AVG(del.confidence) AS avg_deliverable_confidence,
    AVG(dl.confidence) AS avg_deadline_confidence,
    AVG(f.confidence) AS avg_financial_confidence
FROM `{project_id}.{dataset}.documents` d
LEFT JOIN `{project_id}.{dataset}.stakeholders` s ON d.document_id = s.document_id
LEFT JOIN `{project_id}.{dataset}.deliverables` del ON d.document_id = del.document_id
LEFT JOIN `{project_id}.{dataset}.deadlines` dl ON d.document_id = dl.document_id
LEFT JOIN `{project_id}.{dataset}.financials` f ON d.document_id = f.document_id
WHERE d.upload_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
  AND d.processing_status = 'completed'
GROUP BY extraction_date, document_type;

-- Review queue status view
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_review_queue_status` AS
SELECT
    rq.queue_id,
    rq.document_id,
    d.filename,
    d.document_type,
    d.overall_confidence,
    rq.reason,
    rq.severity,
    rq.review_status,
    rq.assigned_reviewer,
    rq.created_at,
    rq.assigned_at,
    rq.reviewed_at,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), rq.created_at, HOUR) AS hours_pending,
    ARRAY_LENGTH(rq.flagged_entities) AS flagged_entities_count
FROM `{project_id}.{dataset}.review_queue` rq
INNER JOIN `{project_id}.{dataset}.documents` d ON rq.document_id = d.document_id
WHERE rq.review_status IN ('pending', 'in_progress')
ORDER BY rq.created_at DESC;

-- Weekly processing metrics view
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_weekly_processing_metrics` AS
SELECT
    DATE_TRUNC(DATE(upload_timestamp), WEEK(MONDAY)) AS week_start,
    DATE_ADD(DATE_TRUNC(DATE(upload_timestamp), WEEK(MONDAY)), INTERVAL 6 DAY) AS week_end,
    COUNT(DISTINCT document_id) AS total_documents,
    COUNTIF(processing_status = 'completed') AS completed_documents,
    COUNTIF(processing_status = 'failed') AS failed_documents,
    COUNTIF(processing_status = 'review_required') AS review_required_documents,
    COUNTIF(processing_status IN ('pending', 'processing')) AS pending_documents,
    AVG(overall_confidence) AS avg_confidence,
    COUNTIF(overall_confidence < 0.7) AS low_confidence_documents,
    SUM(raw_text_length) AS total_text_processed
FROM `{project_id}.{dataset}.documents`
WHERE upload_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
GROUP BY week_start, week_end
ORDER BY week_start DESC;

-- Stakeholder analysis view
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_stakeholder_analysis` AS
SELECT
    s.stakeholder_type,
    s.organization,
    s.role,
    COUNT(DISTINCT s.document_id) AS document_count,
    COUNT(DISTINCT s.entity_id) AS occurrence_count,
    AVG(s.confidence) AS avg_confidence,
    MIN(s.extraction_timestamp) AS first_seen,
    MAX(s.extraction_timestamp) AS last_seen
FROM `{project_id}.{dataset}.stakeholders` s
INNER JOIN `{project_id}.{dataset}.documents` d ON s.document_id = d.document_id
WHERE d.processing_status = 'completed'
GROUP BY s.stakeholder_type, s.organization, s.role
ORDER BY occurrence_count DESC;

-- Deadline tracking view
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_deadline_tracking` AS
SELECT
    dl.deadline_date,
    dl.deadline_type,
    dl.is_firm,
    COUNT(DISTINCT dl.document_id) AS document_count,
    COUNT(DISTINCT dl.entity_id) AS deadline_count,
    AVG(dl.confidence) AS avg_confidence,
    d.document_type,
    dl.description
FROM `{project_id}.{dataset}.deadlines` dl
INNER JOIN `{project_id}.{dataset}.documents` d ON dl.document_id = d.document_id
WHERE d.processing_status = 'completed'
  AND dl.deadline_date >= CURRENT_DATE()
GROUP BY dl.deadline_date, dl.deadline_type, dl.is_firm, d.document_type, dl.description
ORDER BY dl.deadline_date ASC;

-- Financial summary view
CREATE OR REPLACE VIEW `{project_id}.{dataset}.v_financial_summary` AS
SELECT
    f.financial_type,
    f.currency,
    COUNT(DISTINCT f.document_id) AS document_count,
    COUNT(DISTINCT f.entity_id) AS entity_count,
    SUM(f.amount) AS total_amount,
    AVG(f.amount) AS avg_amount,
    AVG(f.confidence) AS avg_confidence,
    MIN(f.due_date) AS earliest_due_date,
    MAX(f.due_date) AS latest_due_date
FROM `{project_id}.{dataset}.financials` f
INNER JOIN `{project_id}.{dataset}.documents` d ON f.document_id = d.document_id
WHERE d.processing_status = 'completed'
  AND f.amount IS NOT NULL
GROUP BY f.financial_type, f.currency
ORDER BY total_amount DESC;
