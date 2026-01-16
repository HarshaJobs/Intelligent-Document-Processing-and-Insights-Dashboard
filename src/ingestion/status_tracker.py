"""
Processing status tracker for documents.

Manages document processing status in BigQuery.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from src.api.models.document import DocumentType, DocumentStructure, ProcessingStatus
from src.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ProcessingStatusTracker:
    """
    Tracks document processing status in BigQuery.
    
    Provides methods to create, update, and query processing status.
    """

    def __init__(self):
        """Initialize the status tracker."""
        self._client: Optional[bigquery.Client] = None

    @property
    def client(self) -> bigquery.Client:
        """Get or create BigQuery client."""
        if self._client is None:
            self._client = bigquery.Client(
                project=settings.gcp_project_id,
                location=settings.bigquery_location,
            )
        return self._client

    @property
    def documents_table(self) -> str:
        """Full path to documents table."""
        return f"{settings.gcp_project_id}.{settings.bigquery_dataset}.documents"

    @property
    def processing_log_table(self) -> str:
        """Full path to processing log table."""
        return f"{settings.gcp_project_id}.{settings.bigquery_dataset}.processing_log"

    @property
    def review_queue_table(self) -> str:
        """Full path to review queue table."""
        return f"{settings.gcp_project_id}.{settings.bigquery_dataset}.review_queue"

    def create_document_record(
        self,
        document_id: str,
        filename: str,
        source_bucket: str,
        blob_path: str,
        document_type: Optional[DocumentType] = None,
        structure_type: Optional[DocumentStructure] = None,
        raw_text_length: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Create a new document record in BigQuery.
        
        Args:
            document_id: Unique document identifier
            filename: Original filename
            source_bucket: Cloud Storage bucket name
            blob_path: Path in the bucket
            document_type: Optional detected document type
            structure_type: Optional detected structure type
            raw_text_length: Length of extracted text
            metadata: Additional metadata
            
        Returns:
            True if created successfully
        """
        row = {
            "document_id": document_id,
            "filename": filename,
            "document_type": document_type.value if document_type else None,
            "structure_type": structure_type.value if structure_type else None,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "processing_status": ProcessingStatus.PENDING.value,
            "overall_confidence": None,
            "source_bucket": source_bucket,
            "blob_path": blob_path,
            "raw_text_length": raw_text_length,
            "processing_started_at": None,
            "processing_completed_at": None,
            "error_message": None,
            "metadata": metadata,
        }
        
        try:
            errors = self.client.insert_rows_json(self.documents_table, [row])
            if errors:
                logger.error(f"Failed to insert document record: {errors}")
                return False
            
            logger.info(f"Created document record for {document_id}")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error creating document record: {e}")
            raise

    def update_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        confidence: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update document processing status.
        
        Args:
            document_id: Document identifier
            status: New processing status
            confidence: Optional overall confidence score
            error_message: Optional error message
            
        Returns:
            True if updated successfully
        """
        update_fields = [f"processing_status = '{status.value}'"]
        
        if status == ProcessingStatus.PROCESSING:
            update_fields.append(f"processing_started_at = CURRENT_TIMESTAMP()")
        elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            update_fields.append(f"processing_completed_at = CURRENT_TIMESTAMP()")
        
        if confidence is not None:
            update_fields.append(f"overall_confidence = {confidence}")
        
        if error_message:
            # Escape single quotes in error message
            safe_error = error_message.replace("'", "''")
            update_fields.append(f"error_message = '{safe_error}'")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP()")
        
        query = f"""
            UPDATE `{self.documents_table}`
            SET {', '.join(update_fields)}
            WHERE document_id = '{document_id}'
        """
        
        try:
            job = self.client.query(query)
            job.result()
            
            logger.info(f"Updated status for {document_id} to {status.value}")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"Failed to update status for {document_id}: {e}")
            raise

    def log_processing_event(
        self,
        document_id: str,
        event_type: str,
        details: Optional[dict] = None,
        user_id: Optional[str] = None,
        service_name: str = "document-processor",
    ) -> bool:
        """
        Log a processing event to BigQuery.
        
        Args:
            document_id: Document identifier
            event_type: Type of event
            details: Event details
            user_id: Optional user identifier
            service_name: Name of the service
            
        Returns:
            True if logged successfully
        """
        row = {
            "log_id": str(uuid.uuid4()),
            "document_id": document_id,
            "event_type": event_type,
            "event_timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "service_name": service_name,
            "details": details,
        }
        
        try:
            errors = self.client.insert_rows_json(self.processing_log_table, [row])
            if errors:
                logger.error(f"Failed to insert processing log: {errors}")
                return False
            
            return True
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error logging event: {e}")
            raise

    def flag_for_review(
        self,
        document_id: str,
        reason: str,
        flagged_entities: Optional[list] = None,
        severity: str = "medium",
    ) -> bool:
        """
        Flag a document for manual review.
        
        Args:
            document_id: Document identifier
            reason: Reason for flagging
            flagged_entities: List of entity IDs that need review
            severity: Severity level (low, medium, high)
            
        Returns:
            True if flagged successfully
        """
        row = {
            "queue_id": str(uuid.uuid4()),
            "document_id": document_id,
            "flagged_entities": flagged_entities,
            "reason": reason,
            "severity": severity,
            "assigned_reviewer": None,
            "review_status": "pending",
            "review_notes": None,
            "created_at": datetime.utcnow().isoformat(),
            "assigned_at": None,
            "reviewed_at": None,
        }
        
        try:
            errors = self.client.insert_rows_json(self.review_queue_table, [row])
            if errors:
                logger.error(f"Failed to add to review queue: {errors}")
                return False
            
            # Also update document status
            self.update_status(document_id, ProcessingStatus.REVIEW_REQUIRED)
            
            logger.info(f"Flagged document {document_id} for review: {reason}")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error flagging document: {e}")
            raise

    def get_document_status(self, document_id: str) -> Optional[dict]:
        """
        Get current status of a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document status dictionary or None if not found
        """
        query = f"""
            SELECT 
                document_id,
                filename,
                document_type,
                structure_type,
                processing_status,
                overall_confidence,
                upload_timestamp,
                processing_started_at,
                processing_completed_at,
                error_message
            FROM `{self.documents_table}`
            WHERE document_id = '{document_id}'
        """
        
        try:
            job = self.client.query(query)
            results = list(job.result())
            
            if results:
                row = results[0]
                return dict(row)
            
            return None
            
        except GoogleCloudError as e:
            logger.error(f"Failed to get status for {document_id}: {e}")
            raise

    def get_pending_documents(self, limit: int = 100) -> list[dict]:
        """
        Get documents pending processing.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of pending document records
        """
        query = f"""
            SELECT 
                document_id,
                filename,
                source_bucket,
                blob_path,
                upload_timestamp
            FROM `{self.documents_table}`
            WHERE processing_status = 'pending'
            ORDER BY upload_timestamp ASC
            LIMIT {limit}
        """
        
        try:
            job = self.client.query(query)
            return [dict(row) for row in job.result()]
            
        except GoogleCloudError as e:
            logger.error(f"Failed to get pending documents: {e}")
            raise


def get_status_tracker() -> ProcessingStatusTracker:
    """Get a status tracker instance."""
    return ProcessingStatusTracker()
