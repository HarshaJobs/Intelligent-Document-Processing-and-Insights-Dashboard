"""
Document management routes.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from src.api.models.document import (
    DocumentListResponse,
    DocumentMetadata,
    DocumentStatusResponse,
    DocumentType,
    DocumentUploadResponse,
    ProcessingStatus,
)
from src.api.models.entity import ExtractionResult
from src.config import get_settings

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[DocumentType] = Query(
        default=None, description="Optional document type hint"
    ),
) -> DocumentUploadResponse:
    """
    Upload a document for processing.
    
    Accepts PDF, DOCX, or TXT files. The document will be stored in
    Cloud Storage and queued for processing.
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX, TXT",
        )
    
    # Generate unique document ID
    document_id = str(uuid.uuid4())
    
    # TODO: Integrate with storage_handler to upload to GCS
    # TODO: Trigger processing pipeline
    
    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename or "unknown",
        status=ProcessingStatus.PENDING,
        message=f"Document queued for processing. ID: {document_id}",
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str) -> DocumentStatusResponse:
    """
    Get the processing status of a document.
    
    Returns the current status and any available metadata.
    """
    # TODO: Query BigQuery for document status
    
    # Placeholder response
    return DocumentStatusResponse(
        document_id=document_id,
        status=ProcessingStatus.PENDING,
        document_type=None,
        confidence=None,
        processed_at=None,
        error_message=None,
        entities_extracted=None,
    )


@router.get("/{document_id}/entities", response_model=ExtractionResult)
async def get_document_entities(document_id: str) -> ExtractionResult:
    """
    Get extracted entities for a processed document.
    
    Returns all stakeholders, deliverables, deadlines, and financials
    extracted from the document.
    """
    # TODO: Query BigQuery for extracted entities
    
    # Placeholder response
    return ExtractionResult(
        document_id=document_id,
        document_type="sow",
        structure_type="structured",
        overall_confidence=0.0,
        stakeholders=[],
        deliverables=[],
        deadlines=[],
        financials=[],
        extraction_timestamp=datetime.utcnow(),
        needs_review=False,
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    status: Optional[ProcessingStatus] = Query(default=None),
    document_type: Optional[DocumentType] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> DocumentListResponse:
    """
    List documents with optional filtering.
    
    Supports pagination and filtering by status and document type.
    """
    # TODO: Query BigQuery for documents
    
    return DocumentListResponse(
        documents=[],
        total_count=0,
        page=page,
        page_size=page_size,
    )


@router.get("/review-queue", response_model=DocumentListResponse)
async def get_review_queue(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> DocumentListResponse:
    """
    Get documents that require manual review.
    
    Returns documents flagged for review due to low confidence scores.
    """
    # TODO: Query BigQuery review_queue table
    
    return DocumentListResponse(
        documents=[],
        total_count=0,
        page=page,
        page_size=page_size,
    )


@router.post("/{document_id}/reprocess")
async def reprocess_document(document_id: str) -> dict:
    """
    Trigger reprocessing of a document.
    
    Useful after manual corrections or for low-confidence documents.
    """
    # TODO: Trigger reprocessing pipeline
    
    return {
        "document_id": document_id,
        "status": "reprocessing_queued",
        "message": "Document has been queued for reprocessing",
    }
