-- BigQuery Schema for Document Processing Dashboard
-- Run this script to create the required tables

-- Create dataset (run separately in BigQuery console or via bq command)
-- CREATE SCHEMA IF NOT EXISTS `project_id.document_processing`
-- OPTIONS(location="US");

-- Core documents table
CREATE TABLE IF NOT EXISTS documents (
    document_id STRING NOT NULL,
    filename STRING NOT NULL,
    document_type STRING,  -- sow, contract, email, amendment, msa, other
    structure_type STRING, -- structured, semi_structured, unstructured
    upload_timestamp TIMESTAMP NOT NULL,
    processing_status STRING NOT NULL,  -- pending, processing, completed, failed, review_required
    overall_confidence FLOAT64,
    source_bucket STRING,
    blob_path STRING,
    raw_text_length INT64,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    error_message STRING,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(upload_timestamp)
CLUSTER BY document_type, processing_status;


-- Extracted stakeholders
CREATE TABLE IF NOT EXISTS stakeholders (
    entity_id STRING NOT NULL,
    document_id STRING NOT NULL,
    stakeholder_type STRING NOT NULL,  -- client, vendor, contact, signatory, project_manager
    name STRING NOT NULL,
    role STRING,
    organization STRING,
    email STRING,
    phone STRING,
    confidence FLOAT64 NOT NULL,
    extraction_timestamp TIMESTAMP NOT NULL,
    source_text STRING,  -- Original text span that was extracted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(extraction_timestamp)
CLUSTER BY document_id, stakeholder_type;


-- Extracted deliverables
CREATE TABLE IF NOT EXISTS deliverables (
    entity_id STRING NOT NULL,
    document_id STRING NOT NULL,
    deliverable_name STRING NOT NULL,
    description STRING,
    acceptance_criteria STRING,
    milestone_id STRING,
    dependencies ARRAY<STRING>,
    confidence FLOAT64 NOT NULL,
    extraction_timestamp TIMESTAMP NOT NULL,
    source_text STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(extraction_timestamp)
CLUSTER BY document_id;


-- Extracted deadlines
CREATE TABLE IF NOT EXISTS deadlines (
    entity_id STRING NOT NULL,
    document_id STRING NOT NULL,
    deadline_type STRING NOT NULL,  -- start, end, milestone, payment, review
    deadline_date DATE NOT NULL,
    description STRING,
    associated_deliverable STRING,
    is_firm BOOL DEFAULT TRUE,
    confidence FLOAT64 NOT NULL,
    extraction_timestamp TIMESTAMP NOT NULL,
    source_text STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY deadline_date
CLUSTER BY document_id, deadline_type;


-- Extracted financial entities
CREATE TABLE IF NOT EXISTS financials (
    entity_id STRING NOT NULL,
    document_id STRING NOT NULL,
    financial_type STRING NOT NULL,  -- total_value, payment, penalty, milestone_payment
    amount FLOAT64,
    currency STRING DEFAULT 'USD',
    description STRING,
    payment_terms STRING,
    due_date DATE,
    confidence FLOAT64 NOT NULL,
    extraction_timestamp TIMESTAMP NOT NULL,
    source_text STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(extraction_timestamp)
CLUSTER BY document_id, financial_type;


-- Processing audit log
CREATE TABLE IF NOT EXISTS processing_log (
    log_id STRING NOT NULL,
    document_id STRING,
    event_type STRING NOT NULL,  -- upload, processing_start, extraction_complete, error, review_flagged
    event_timestamp TIMESTAMP NOT NULL,
    user_id STRING,
    service_name STRING,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY document_id, event_type;


-- Manual review queue
CREATE TABLE IF NOT EXISTS review_queue (
    queue_id STRING NOT NULL,
    document_id STRING NOT NULL,
    flagged_entities JSON,  -- List of entity IDs that need review
    reason STRING NOT NULL,  -- low_confidence, ambiguous_extraction, missing_required_fields
    severity STRING DEFAULT 'medium',  -- low, medium, high
    assigned_reviewer STRING,
    review_status STRING DEFAULT 'pending',  -- pending, in_progress, completed, dismissed
    review_notes STRING,
    created_at TIMESTAMP NOT NULL,
    assigned_at TIMESTAMP,
    reviewed_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY review_status, severity;


-- Weekly report snapshots
CREATE TABLE IF NOT EXISTS weekly_reports (
    report_id STRING NOT NULL,
    report_date DATE NOT NULL,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    documents_processed INT64,
    documents_pending INT64,
    avg_confidence FLOAT64,
    documents_flagged_for_review INT64,
    stakeholders_extracted INT64,
    deliverables_extracted INT64,
    deadlines_extracted INT64,
    report_content STRING,  -- Generated summary text
    generated_at TIMESTAMP NOT NULL,
    generated_by STRING DEFAULT 'system'
)
PARTITION BY report_date;
