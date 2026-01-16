"""
Pydantic models for document-related requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document type classification."""

    SOW = "sow"
    CONTRACT = "contract"
    EMAIL = "email"
    AMENDMENT = "amendment"
    MSA = "msa"
    OTHER = "other"


class DocumentStructure(str, Enum):
    """Document structure type."""

    STRUCTURED = "structured"
    SEMI_STRUCTURED = "semi_structured"
    UNSTRUCTURED = "unstructured"


class ProcessingStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the document")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    upload_url: Optional[str] = Field(default=None, description="Signed upload URL")
    status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING, description="Processing status"
    )
    message: str = Field(default="Document uploaded successfully")


class DocumentMetadata(BaseModel):
    """Document metadata model."""

    document_id: str
    filename: str
    document_type: Optional[DocumentType] = None
    structure_type: Optional[DocumentStructure] = None
    upload_timestamp: datetime
    processing_status: ProcessingStatus
    overall_confidence: Optional[float] = None
    source_bucket: str
    raw_text_length: Optional[int] = None
    error_message: Optional[str] = None


class DocumentStatusResponse(BaseModel):
    """Response model for document status query."""

    document_id: str
    status: ProcessingStatus
    document_type: Optional[DocumentType] = None
    confidence: Optional[float] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    entities_extracted: Optional[int] = None


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""

    documents: list[DocumentMetadata]
    total_count: int
    page: int = 1
    page_size: int = 50
