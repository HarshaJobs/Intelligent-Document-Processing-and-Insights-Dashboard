"""
BigQuery data loader for extracted entities.

Loads extracted entities from the extraction pipeline into BigQuery
tables for dashboard consumption and analysis.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from src.api.models.entity import (
    DeadlineEntity,
    DeliverableEntity,
    ExtractionResult,
    FinancialEntity,
    StakeholderEntity,
)
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BigQueryEntityLoader:
    """
    Loader for inserting extracted entities into BigQuery.
    
    Handles batch insertion and updates for all entity types.
    """

    def __init__(self):
        """Initialize BigQuery client."""
        self.client = bigquery.Client(
            project=settings.gcp_project_id,
            location=settings.bigquery_location,
        )

    def load_extraction_result(
        self, extraction_result: ExtractionResult, update_existing: bool = True
    ) -> bool:
        """
        Load complete extraction result into BigQuery.
        
        Args:
            extraction_result: Complete extraction result with all entities
            update_existing: Whether to update existing records
            
        Returns:
            True if loaded successfully
            
        Raises:
            Exception: If loading fails
        """
        try:
            # Load stakeholders
            self._load_stakeholders(
                extraction_result.document_id, extraction_result.stakeholders
            )
            
            # Load deliverables
            self._load_deliverables(
                extraction_result.document_id, extraction_result.deliverables
            )
            
            # Load deadlines
            self._load_deadlines(
                extraction_result.document_id, extraction_result.deadlines
            )
            
            # Load financials
            self._load_financials(
                extraction_result.document_id, extraction_result.financials
            )
            
            logger.info(
                f"Loaded extraction result for {extraction_result.document_id}: "
                f"{len(extraction_result.stakeholders)} stakeholders, "
                f"{len(extraction_result.deliverables)} deliverables, "
                f"{len(extraction_result.deadlines)} deadlines, "
                f"{len(extraction_result.financials)} financials"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to load extraction result for {extraction_result.document_id}: {e}",
                exc_info=True,
            )
            raise

    def _load_stakeholders(
        self, document_id: str, stakeholders: list[StakeholderEntity]
    ) -> None:
        """Load stakeholders into BigQuery."""
        if not stakeholders:
            return
        
        table_id = settings.stakeholders_table
        rows_to_insert = []
        
        for entity in stakeholders:
            rows_to_insert.append({
                "entity_id": entity.entity_id,
                "document_id": document_id,
                "stakeholder_type": entity.stakeholder_type,
                "name": entity.name,
                "role": entity.role,
                "organization": entity.organization,
                "email": entity.email,
                "phone": entity.phone,
                "confidence": float(entity.confidence),
                "extraction_timestamp": entity.extraction_timestamp.isoformat(),
                "source_text": None,  # TODO: Extract from source if available
                "created_at": datetime.utcnow().isoformat(),
            })
        
        try:
            errors = self.client.insert_rows_json(table_id, rows_to_insert)
            if errors:
                logger.error(f"Errors inserting stakeholders: {errors}")
                raise ValueError(f"BigQuery insert errors: {errors}")
            
            logger.debug(f"Inserted {len(rows_to_insert)} stakeholders for {document_id}")
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error inserting stakeholders: {e}")
            raise

    def _load_deliverables(
        self, document_id: str, deliverables: list[DeliverableEntity]
    ) -> None:
        """Load deliverables into BigQuery."""
        if not deliverables:
            return
        
        table_id = settings.deliverables_table
        rows_to_insert = []
        
        for entity in deliverables:
            rows_to_insert.append({
                "entity_id": entity.entity_id,
                "document_id": document_id,
                "deliverable_name": entity.deliverable_name,
                "description": entity.description,
                "acceptance_criteria": entity.acceptance_criteria,
                "milestone_id": entity.milestone_id,
                "dependencies": entity.dependencies,
                "confidence": float(entity.confidence),
                "extraction_timestamp": entity.extraction_timestamp.isoformat(),
                "source_text": None,  # TODO: Extract from source if available
                "created_at": datetime.utcnow().isoformat(),
            })
        
        try:
            errors = self.client.insert_rows_json(table_id, rows_to_insert)
            if errors:
                logger.error(f"Errors inserting deliverables: {errors}")
                raise ValueError(f"BigQuery insert errors: {errors}")
            
            logger.debug(f"Inserted {len(rows_to_insert)} deliverables for {document_id}")
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error inserting deliverables: {e}")
            raise

    def _load_deadlines(
        self, document_id: str, deadlines: list[DeadlineEntity]
    ) -> None:
        """Load deadlines into BigQuery."""
        if not deadlines:
            return
        
        table_id = settings.deadlines_table
        rows_to_insert = []
        
        for entity in deadlines:
            rows_to_insert.append({
                "entity_id": entity.entity_id,
                "document_id": document_id,
                "deadline_type": entity.deadline_type,
                "deadline_date": entity.deadline_date.isoformat(),
                "description": entity.description,
                "associated_deliverable": entity.associated_deliverable,
                "is_firm": bool(entity.is_firm),
                "confidence": float(entity.confidence),
                "extraction_timestamp": entity.extraction_timestamp.isoformat(),
                "source_text": None,  # TODO: Extract from source if available
                "created_at": datetime.utcnow().isoformat(),
            })
        
        try:
            errors = self.client.insert_rows_json(table_id, rows_to_insert)
            if errors:
                logger.error(f"Errors inserting deadlines: {errors}")
                raise ValueError(f"BigQuery insert errors: {errors}")
            
            logger.debug(f"Inserted {len(rows_to_insert)} deadlines for {document_id}")
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error inserting deadlines: {e}")
            raise

    def _load_financials(
        self, document_id: str, financials: list[FinancialEntity]
    ) -> None:
        """Load financials into BigQuery."""
        if not financials:
            return
        
        table_id = settings.financials_table
        rows_to_insert = []
        
        for entity in financials:
            rows_to_insert.append({
                "entity_id": entity.entity_id,
                "document_id": document_id,
                "financial_type": entity.financial_type,
                "amount": float(entity.amount) if entity.amount else None,
                "currency": entity.currency,
                "description": entity.description,
                "payment_terms": entity.payment_terms,
                "due_date": entity.due_date.isoformat() if entity.due_date else None,
                "confidence": float(entity.confidence),
                "extraction_timestamp": entity.extraction_timestamp.isoformat(),
                "source_text": None,  # TODO: Extract from source if available
                "created_at": datetime.utcnow().isoformat(),
            })
        
        try:
            errors = self.client.insert_rows_json(table_id, rows_to_insert)
            if errors:
                logger.error(f"Errors inserting financials: {errors}")
                raise ValueError(f"BigQuery insert errors: {errors}")
            
            logger.debug(f"Inserted {len(rows_to_insert)} financials for {document_id}")
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error inserting financials: {e}")
            raise

    def add_to_review_queue(
        self,
        document_id: str,
        flagged_entities: list[str],
        reason: str,
        severity: str = "medium",
    ) -> str:
        """
        Add document to review queue.
        
        Args:
            document_id: Document identifier
            flagged_entities: List of entity IDs that need review
            reason: Reason for review (low_confidence, ambiguous_extraction, etc.)
            severity: Severity level (low, medium, high)
            
        Returns:
            Queue ID
        """
        queue_id = str(uuid.uuid4())
        table_id = settings.review_queue_table
        
        row = {
            "queue_id": queue_id,
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
            errors = self.client.insert_rows_json(table_id, [row])
            if errors:
                logger.error(f"Errors inserting review queue entry: {errors}")
                raise ValueError(f"BigQuery insert errors: {errors}")
            
            logger.info(f"Added {document_id} to review queue (queue_id={queue_id})")
            return queue_id
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error adding to review queue: {e}")
            raise


def get_bigquery_loader() -> BigQueryEntityLoader:
    """Get a BigQuery loader instance."""
    return BigQueryEntityLoader()
