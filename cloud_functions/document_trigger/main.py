"""
Cloud Function for document upload trigger.

Triggered when a document is uploaded to Cloud Storage.
Initiates the processing pipeline.
"""

import json
import logging
import os
from datetime import datetime

import functions_framework
from google.cloud import storage
from cloudevents.http import CloudEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
PROCESSING_SERVICE_URL = os.environ.get(
    "PROCESSING_SERVICE_URL", "http://localhost:8080"
)
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", "document_processing")


def validate_file_type(filename: str) -> bool:
    """Check if file type is supported."""
    supported_extensions = [".pdf", ".docx", ".txt"]
    return any(filename.lower().endswith(ext) for ext in supported_extensions)


def extract_document_id_from_path(blob_path: str) -> str:
    """
    Extract document ID from blob path.
    
    Expected format: YYYY/MM/DD/document_id.ext
    """
    import os
    basename = os.path.basename(blob_path)
    name, _ = os.path.splitext(basename)
    return name


@functions_framework.cloud_event
def document_uploaded(cloud_event: CloudEvent) -> None:
    """
    Cloud Function triggered by Cloud Storage upload.
    
    Args:
        cloud_event: CloudEvent containing the trigger data
    """
    data = cloud_event.data
    
    bucket_name = data.get("bucket")
    blob_name = data.get("name")
    content_type = data.get("contentType", "")
    size = data.get("size", 0)
    
    logger.info(f"Processing upload: gs://{bucket_name}/{blob_name}")
    
    # Validate file type
    if not validate_file_type(blob_name):
        logger.warning(f"Unsupported file type: {blob_name}")
        return
    
    # Extract document ID
    document_id = extract_document_id_from_path(blob_name)
    
    # Log the event
    log_entry = {
        "event_type": "document.uploaded",
        "document_id": document_id,
        "bucket": bucket_name,
        "blob_path": blob_name,
        "content_type": content_type,
        "size": int(size),
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.info(f"Upload event: {json.dumps(log_entry)}")
    
    # Trigger processing (via HTTP call to Cloud Run service)
    try:
        import httpx
        
        response = httpx.post(
            f"{PROCESSING_SERVICE_URL}/api/v1/documents/process",
            json={
                "document_id": document_id,
                "bucket": bucket_name,
                "blob_path": blob_name,
                "content_type": content_type,
            },
            timeout=30.0,
        )
        
        if response.status_code == 200:
            logger.info(f"Processing triggered for document {document_id}")
        else:
            logger.error(
                f"Failed to trigger processing: {response.status_code} - {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Error triggering processing: {e}")
        # Don't raise - let the function complete to avoid retries
        # The status tracker will mark this as pending for retry


@functions_framework.http
def health_check(request):
    """Health check endpoint for the Cloud Function."""
    return {"status": "healthy", "service": "document-trigger"}
