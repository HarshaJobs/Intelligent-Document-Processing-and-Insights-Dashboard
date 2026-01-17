"""
Entity extraction pipeline using Gemini API.

Orchestrates the full extraction process from document text
to structured entities with confidence scoring.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from src.api.models.document import DocumentStructure, DocumentType
from src.api.models.entity import (
    DeadlineEntity,
    DeliverableEntity,
    ExtractionResult,
    FinancialEntity,
    StakeholderEntity,
)
from src.config import get_settings
from src.extraction.gemini_client import GeminiExtractionClient
from src.ingestion.status_tracker import ProcessingStatus, ProcessingStatusTracker

logger = logging.getLogger(__name__)
settings = get_settings()


class EntityExtractionPipeline:
    """
    Pipeline for extracting entities from documents.
    
    Handles the full extraction workflow including:
    - Gemini API calls
    - Entity normalization
    - Confidence scoring
    - Review flagging
    """

    def __init__(self):
        """Initialize extraction pipeline."""
        self.gemini_client = GeminiExtractionClient()
        self.status_tracker = ProcessingStatusTracker()

    def extract_entities_from_text(
        self,
        document_id: str,
        document_text: str,
        document_type: Optional[DocumentType] = None,
        structure_type: Optional[DocumentStructure] = None,
        update_status: bool = True,
    ) -> ExtractionResult:
        """
        Extract entities from document text.
        
        Args:
            document_id: Document identifier
            document_text: Full document text
            document_type: Document type (auto-detected if None)
            structure_type: Structure type (auto-detected if None)
            update_status: Whether to update processing status
            
        Returns:
            ExtractionResult with all extracted entities
            
        Raises:
            Exception: If extraction fails
        """
        start_time = time.time()
        
        try:
            # Default values if not provided
            if document_type is None:
                document_type = DocumentType.OTHER
            if structure_type is None:
                structure_type = DocumentStructure.UNSTRUCTURED
            
            # Update status to processing
            if update_status:
                self.status_tracker.update_status(
                    document_id, ProcessingStatus.PROCESSING
                )
            
            # Call Gemini API for extraction
            raw_extraction = self.gemini_client.extract_entities(
                document_text=document_text,
                document_type=document_type,
                structure_type=structure_type,
            )
            
            # Convert to structured entities
            stakeholders = self._convert_stakeholders(
                raw_extraction.get("stakeholders", []), document_id
            )
            deliverables = self._convert_deliverables(
                raw_extraction.get("deliverables", []), document_id
            )
            deadlines = self._convert_deadlines(
                raw_extraction.get("deadlines", []), document_id
            )
            financials = self._convert_financials(
                raw_extraction.get("financials", []), document_id
            )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                raw_extraction.get("overall_confidence", 0.5),
                stakeholders,
                deliverables,
                deadlines,
                financials,
            )
            
            # Determine if review is needed
            needs_review, review_reasons = self._assess_review_requirements(
                overall_confidence, stakeholders, deliverables, deadlines, financials
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Build result
            result = ExtractionResult(
                document_id=document_id,
                document_type=document_type.value,
                structure_type=structure_type.value,
                overall_confidence=overall_confidence,
                stakeholders=stakeholders,
                deliverables=deliverables,
                deadlines=deadlines,
                financials=financials,
                raw_text_preview=document_text[:500] if document_text else None,
                extraction_timestamp=datetime.utcnow(),
                processing_time_ms=processing_time_ms,
                needs_review=needs_review,
                review_reasons=review_reasons,
            )
            
            # Update status
            if update_status:
                final_status = (
                    ProcessingStatus.REVIEW_REQUIRED
                    if needs_review
                    else ProcessingStatus.COMPLETED
                )
                self.status_tracker.update_status(
                    document_id,
                    final_status,
                    confidence=overall_confidence,
                )
            
            logger.info(
                f"Extraction complete for {document_id}: "
                f"confidence={overall_confidence:.2f}, "
                f"review_required={needs_review}, "
                f"time_ms={processing_time_ms}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed for {document_id}: {e}", exc_info=True)
            
            if update_status:
                self.status_tracker.update_status(
                    document_id,
                    ProcessingStatus.FAILED,
                    error_message=str(e),
                )
            
            raise

    def _convert_stakeholders(
        self, raw_stakeholders: list[dict], document_id: str
    ) -> list[StakeholderEntity]:
        """Convert raw stakeholder data to entities."""
        entities = []
        
        for raw in raw_stakeholders:
            try:
                entity = StakeholderEntity(
                    entity_id=str(uuid.uuid4()),
                    document_id=document_id,
                    stakeholder_type=raw.get("stakeholder_type", "contact"),
                    name=raw.get("name", ""),
                    role=raw.get("role"),
                    organization=raw.get("organization"),
                    email=raw.get("email"),
                    phone=raw.get("phone"),
                    confidence=float(raw.get("confidence", 0.5)),
                    extraction_timestamp=datetime.utcnow(),
                )
                entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to convert stakeholder: {e}")
        
        return entities

    def _convert_deliverables(
        self, raw_deliverables: list[dict], document_id: str
    ) -> list[DeliverableEntity]:
        """Convert raw deliverable data to entities."""
        entities = []
        
        for raw in raw_deliverables:
            try:
                entity = DeliverableEntity(
                    entity_id=str(uuid.uuid4()),
                    document_id=document_id,
                    deliverable_name=raw.get("deliverable_name", ""),
                    description=raw.get("description"),
                    acceptance_criteria=raw.get("acceptance_criteria"),
                    milestone_id=raw.get("milestone_id"),
                    dependencies=raw.get("dependencies", []),
                    confidence=float(raw.get("confidence", 0.5)),
                    extraction_timestamp=datetime.utcnow(),
                )
                entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to convert deliverable: {e}")
        
        return entities

    def _convert_deadlines(
        self, raw_deadlines: list[dict], document_id: str
    ) -> list[DeadlineEntity]:
        """Convert raw deadline data to entities."""
        entities = []
        
        for raw in raw_deadlines:
            try:
                from datetime import date as date_type
                
                deadline_date_str = raw.get("deadline_date")
                deadline_date = None
                
                if deadline_date_str:
                    try:
                        deadline_date = datetime.strptime(
                            deadline_date_str, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        logger.warning(
                            f"Invalid date format: {deadline_date_str}"
                        )
                
                if deadline_date:
                    entity = DeadlineEntity(
                        entity_id=str(uuid.uuid4()),
                        document_id=document_id,
                        deadline_type=raw.get("deadline_type", "milestone"),
                        deadline_date=deadline_date,
                        description=raw.get("description"),
                        associated_deliverable=raw.get("associated_deliverable"),
                        is_firm=bool(raw.get("is_firm", True)),
                        confidence=float(raw.get("confidence", 0.5)),
                        extraction_timestamp=datetime.utcnow(),
                    )
                    entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to convert deadline: {e}")
        
        return entities

    def _convert_financials(
        self, raw_financials: list[dict], document_id: str
    ) -> list[FinancialEntity]:
        """Convert raw financial data to entities."""
        entities = []
        
        for raw in raw_financials:
            try:
                from datetime import date as date_type
                
                due_date_str = raw.get("due_date")
                due_date = None
                
                if due_date_str:
                    try:
                        due_date = datetime.strptime(
                            due_date_str, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        logger.warning(f"Invalid date format: {due_date_str}")
                
                entity = FinancialEntity(
                    entity_id=str(uuid.uuid4()),
                    document_id=document_id,
                    financial_type=raw.get("financial_type", "payment"),
                    amount=raw.get("amount"),
                    currency=raw.get("currency", "USD"),
                    description=raw.get("description"),
                    payment_terms=raw.get("payment_terms"),
                    due_date=due_date,
                    confidence=float(raw.get("confidence", 0.5)),
                    extraction_timestamp=datetime.utcnow(),
                )
                entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to convert financial: {e}")
        
        return entities

    def _calculate_overall_confidence(
        self,
        gemini_confidence: float,
        stakeholders: list[StakeholderEntity],
        deliverables: list[DeliverableEntity],
        deadlines: list[DeadlineEntity],
        financials: list[FinancialEntity],
    ) -> float:
        """
        Calculate overall confidence score.
        
        Weights entity-level confidences and combines with Gemini's overall confidence.
        """
        all_confidences = [gemini_confidence]
        
        for entity in stakeholders + deliverables + deadlines + financials:
            all_confidences.append(entity.confidence)
        
        if all_confidences:
            # Use weighted average (Gemini confidence weighted 40%, entity average 60%)
            entity_avg = sum(all_confidences[1:]) / len(all_confidences[1:]) if len(all_confidences) > 1 else gemini_confidence
            overall = (gemini_confidence * 0.4) + (entity_avg * 0.6)
            return max(0.0, min(1.0, overall))
        
        return gemini_confidence

    def _assess_review_requirements(
        self,
        overall_confidence: float,
        stakeholders: list[StakeholderEntity],
        deliverables: list[DeliverableEntity],
        deadlines: list[DeadlineEntity],
        financials: list[FinancialEntity],
    ) -> tuple[bool, list[str]]:
        """
        Assess if manual review is required.
        
        Returns:
            Tuple of (needs_review, review_reasons)
        """
        review_reasons = []
        needs_review = False
        
        # Check overall confidence threshold
        if overall_confidence < settings.review_required_threshold:
            needs_review = True
            review_reasons.append(
                f"Overall confidence ({overall_confidence:.2f}) below threshold "
                f"({settings.review_required_threshold})"
            )
        
        # Check for low-confidence entities
        low_confidence_count = 0
        for entity in stakeholders + deliverables + deadlines + financials:
            if entity.confidence < settings.low_confidence_threshold:
                low_confidence_count += 1
        
        if low_confidence_count > 0:
            needs_review = True
            review_reasons.append(
                f"{low_confidence_count} entity/entities with confidence "
                f"below {settings.low_confidence_threshold}"
            )
        
        # Check for missing critical entities
        if len(stakeholders) == 0:
            review_reasons.append("No stakeholders extracted")
        if len(deliverables) == 0 and len(deadlines) == 0:
            review_reasons.append("No deliverables or deadlines extracted")
        
        return needs_review, review_reasons


def get_extraction_pipeline() -> EntityExtractionPipeline:
    """Get an extraction pipeline instance."""
    return EntityExtractionPipeline()