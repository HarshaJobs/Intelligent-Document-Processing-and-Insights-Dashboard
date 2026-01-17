"""
Document management routes.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

logger = logging.getLogger(__name__)

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
from src.extraction import get_extraction_pipeline
from src.ingestion.metadata_extractor import get_metadata_extractor
from src.ingestion.status_tracker import ProcessingStatusTracker
from src.ingestion.storage_handler import get_storage_handler

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


@router.post("/process")
async def process_document(request: dict) -> dict:
    """
    Process a document from Cloud Storage.
    
    Called by Cloud Function when a document is uploaded.
    Extracts text, processes with Gemini, and stores results.
    """
    document_id = request.get("document_id")
    bucket_name = request.get("bucket")
    blob_path = request.get("blob_path")
    content_type = request.get("content_type", "")
    
    if not all([document_id, bucket_name, blob_path]):
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: document_id, bucket, blob_path",
        )
    
    try:
        # Initialize services
        storage_handler = get_storage_handler()
        metadata_extractor = get_metadata_extractor()
        extraction_pipeline = get_extraction_pipeline()
        status_tracker = ProcessingStatusTracker()
        
        # Download document from Cloud Storage
        document_content = storage_handler.download_document(blob_path, bucket_type="raw")
        
        # Extract metadata
        metadata = metadata_extractor.extract_metadata(document_content, blob_path.split("/")[-1])
        
        # Create document record
        status_tracker.create_document_record(
            document_id=document_id,
            filename=metadata["filename"],
            source_bucket=bucket_name,
            blob_path=blob_path,
            document_type=metadata["document_type"],
            structure_type=metadata["structure_type"],
            raw_text_length=metadata["raw_text_length"],
            metadata={"content_type": content_type},
        )
        
        # Extract entities using Gemini
        extraction_result = extraction_pipeline.extract_entities_from_text(
            document_id=document_id,
            document_text=metadata["raw_text"],
            document_type=metadata["document_type"],
            structure_type=metadata["structure_type"],
            update_status=True,
        )
        
        # Load entities into BigQuery
        from src.storage import get_bigquery_loader
        
        bigquery_loader = get_bigquery_loader()
        bigquery_loader.load_extraction_result(extraction_result)
        
        # Add to review queue if needed
        if extraction_result.needs_review:
            flagged_entities = [
                e.entity_id for e in extraction_result.stakeholders
                + extraction_result.deliverables
                + extraction_result.deadlines
                + extraction_result.financials
                if e.confidence < settings.low_confidence_threshold
            ]
            bigquery_loader.add_to_review_queue(
                document_id=document_id,
                flagged_entities=flagged_entities,
                reason="low_confidence" if extraction_result.overall_confidence < settings.review_required_threshold else "validation_required",
            )
        
        return {
            "document_id": document_id,
            "status": "completed",
            "overall_confidence": extraction_result.overall_confidence,
            "entities_extracted": (
                len(extraction_result.stakeholders)
                + len(extraction_result.deliverables)
                + len(extraction_result.deadlines)
                + len(extraction_result.financials)
            ),
            "needs_review": extraction_result.needs_review,
        }
        
    except Exception as e:
        logger.error(f"Processing failed for {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
