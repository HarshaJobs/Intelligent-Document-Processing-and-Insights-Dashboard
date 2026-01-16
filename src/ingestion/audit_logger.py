"""
Audit logging for document processing pipeline.

Provides structured logging to Cloud Logging for compliance
and operational visibility.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from google.cloud import logging as cloud_logging

from src.config import get_settings

settings = get_settings()


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Document lifecycle events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DOWNLOADED = "document.downloaded"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_MOVED = "document.moved"
    
    # Processing events
    PROCESSING_STARTED = "processing.started"
    PROCESSING_COMPLETED = "processing.completed"
    PROCESSING_FAILED = "processing.failed"
    PROCESSING_RETRIED = "processing.retried"
    
    # Extraction events
    EXTRACTION_COMPLETED = "extraction.completed"
    EXTRACTION_LOW_CONFIDENCE = "extraction.low_confidence"
    
    # Review events
    REVIEW_FLAGGED = "review.flagged"
    REVIEW_ASSIGNED = "review.assigned"
    REVIEW_COMPLETED = "review.completed"
    REVIEW_DISMISSED = "review.dismissed"
    
    # Access events
    API_ACCESS = "api.access"
    DATA_EXPORT = "data.export"
    
    # System events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    ERROR_OCCURRED = "error.occurred"


class AuditLogger:
    """
    Audit logger for Cloud Logging integration.
    
    Provides structured logging with consistent format for
    compliance and operational monitoring.
    """

    def __init__(self, logger_name: str = "document-processing-audit"):
        """
        Initialize the audit logger.
        
        Args:
            logger_name: Name of the Cloud Logging logger
        """
        self.logger_name = logger_name
        self._client: Optional[cloud_logging.Client] = None
        self._cloud_logger: Optional[cloud_logging.Logger] = None
        
        # Also set up standard Python logger for local development
        self._local_logger = logging.getLogger(f"audit.{logger_name}")
        self._local_logger.setLevel(logging.INFO)

    @property
    def client(self) -> cloud_logging.Client:
        """Get or create Cloud Logging client."""
        if self._client is None:
            try:
                self._client = cloud_logging.Client(project=settings.gcp_project_id)
            except Exception as e:
                self._local_logger.warning(f"Could not initialize Cloud Logging: {e}")
                self._client = None
        return self._client

    @property
    def cloud_logger(self) -> Optional[cloud_logging.Logger]:
        """Get or create Cloud Logging logger."""
        if self._cloud_logger is None and self.client:
            self._cloud_logger = self.client.logger(self.logger_name)
        return self._cloud_logger

    def _create_log_entry(
        self,
        event_type: AuditEventType,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        severity: str = "INFO",
    ) -> dict[str, Any]:
        """
        Create a structured log entry.
        
        Args:
            event_type: Type of audit event
            document_id: Optional document identifier
            user_id: Optional user identifier
            details: Optional additional details
            severity: Log severity level
            
        Returns:
            Structured log entry dictionary
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "service": "document-processing",
            "environment": settings.environment,
            "severity": severity,
        }
        
        if document_id:
            entry["document_id"] = document_id
        
        if user_id:
            entry["user_id"] = user_id
        
        if details:
            entry["details"] = details
        
        return entry

    def log(
        self,
        event_type: AuditEventType,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        severity: str = "INFO",
    ) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            document_id: Optional document identifier
            user_id: Optional user identifier
            details: Optional additional details
            severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        entry = self._create_log_entry(
            event_type=event_type,
            document_id=document_id,
            user_id=user_id,
            details=details,
            severity=severity,
        )
        
        # Log to Cloud Logging if available
        if self.cloud_logger:
            try:
                self.cloud_logger.log_struct(
                    entry,
                    severity=severity,
                )
            except Exception as e:
                self._local_logger.warning(f"Failed to log to Cloud Logging: {e}")
        
        # Always log locally for development/debugging
        log_message = json.dumps(entry, default=str)
        getattr(self._local_logger, severity.lower(), self._local_logger.info)(log_message)

    # Convenience methods for common events
    
    def log_upload(
        self,
        document_id: str,
        filename: str,
        user_id: Optional[str] = None,
        file_size: Optional[int] = None,
        content_type: Optional[str] = None,
    ) -> None:
        """Log a document upload event."""
        self.log(
            event_type=AuditEventType.DOCUMENT_UPLOADED,
            document_id=document_id,
            user_id=user_id,
            details={
                "filename": filename,
                "file_size": file_size,
                "content_type": content_type,
            },
        )

    def log_processing_start(
        self,
        document_id: str,
        processor: str = "gemini",
    ) -> None:
        """Log processing start event."""
        self.log(
            event_type=AuditEventType.PROCESSING_STARTED,
            document_id=document_id,
            details={"processor": processor},
        )

    def log_processing_complete(
        self,
        document_id: str,
        processing_time_ms: int,
        entities_extracted: int,
        confidence: float,
    ) -> None:
        """Log processing completion event."""
        self.log(
            event_type=AuditEventType.PROCESSING_COMPLETED,
            document_id=document_id,
            details={
                "processing_time_ms": processing_time_ms,
                "entities_extracted": entities_extracted,
                "confidence": confidence,
            },
        )

    def log_processing_failed(
        self,
        document_id: str,
        error: str,
        error_type: Optional[str] = None,
    ) -> None:
        """Log processing failure event."""
        self.log(
            event_type=AuditEventType.PROCESSING_FAILED,
            document_id=document_id,
            details={
                "error": error,
                "error_type": error_type,
            },
            severity="ERROR",
        )

    def log_low_confidence(
        self,
        document_id: str,
        confidence: float,
        flagged_entities: list[str],
    ) -> None:
        """Log low confidence extraction event."""
        self.log(
            event_type=AuditEventType.EXTRACTION_LOW_CONFIDENCE,
            document_id=document_id,
            details={
                "confidence": confidence,
                "flagged_entities": flagged_entities,
                "threshold": settings.low_confidence_threshold,
            },
            severity="WARNING",
        )

    def log_review_flagged(
        self,
        document_id: str,
        reason: str,
        severity_level: str = "medium",
    ) -> None:
        """Log document flagged for review."""
        self.log(
            event_type=AuditEventType.REVIEW_FLAGGED,
            document_id=document_id,
            details={
                "reason": reason,
                "severity_level": severity_level,
            },
            severity="WARNING",
        )

    def log_error(
        self,
        error: str,
        error_type: str,
        document_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Log an error event."""
        self.log(
            event_type=AuditEventType.ERROR_OCCURRED,
            document_id=document_id,
            details={
                "error": error,
                "error_type": error_type,
                "stack_trace": stack_trace,
            },
            severity="ERROR",
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
