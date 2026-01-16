"""
Pydantic models for extracted entities.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class StakeholderEntity(BaseModel):
    """Extracted stakeholder entity."""

    entity_id: str = Field(..., description="Unique entity identifier")
    document_id: str = Field(..., description="Parent document ID")
    stakeholder_type: str = Field(
        ..., description="Type: client, vendor, contact, signatory, project_manager"
    )
    name: str = Field(..., description="Stakeholder name")
    role: Optional[str] = Field(default=None, description="Role or title")
    organization: Optional[str] = Field(default=None, description="Organization name")
    email: Optional[str] = Field(default=None, description="Email address if found")
    phone: Optional[str] = Field(default=None, description="Phone number if found")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeliverableEntity(BaseModel):
    """Extracted deliverable entity."""

    entity_id: str = Field(..., description="Unique entity identifier")
    document_id: str = Field(..., description="Parent document ID")
    deliverable_name: str = Field(..., description="Deliverable name/title")
    description: Optional[str] = Field(default=None, description="Detailed description")
    acceptance_criteria: Optional[str] = Field(
        default=None, description="Acceptance criteria"
    )
    milestone_id: Optional[str] = Field(
        default=None, description="Associated milestone ID"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="List of dependencies"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeadlineEntity(BaseModel):
    """Extracted deadline entity."""

    entity_id: str = Field(..., description="Unique entity identifier")
    document_id: str = Field(..., description="Parent document ID")
    deadline_type: str = Field(
        ..., description="Type: start, end, milestone, payment, review"
    )
    deadline_date: date = Field(..., description="The deadline date")
    description: Optional[str] = Field(default=None, description="Description")
    associated_deliverable: Optional[str] = Field(
        default=None, description="Associated deliverable name"
    )
    is_firm: bool = Field(default=True, description="Whether deadline is firm")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


class FinancialEntity(BaseModel):
    """Extracted financial entity."""

    entity_id: str = Field(..., description="Unique entity identifier")
    document_id: str = Field(..., description="Parent document ID")
    financial_type: str = Field(
        ..., description="Type: total_value, payment, penalty, milestone_payment"
    )
    amount: Optional[float] = Field(default=None, description="Amount value")
    currency: str = Field(default="USD", description="Currency code")
    description: Optional[str] = Field(default=None, description="Description")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms")
    due_date: Optional[date] = Field(default=None, description="Due date if applicable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExtractionResult(BaseModel):
    """Complete extraction result for a document."""

    document_id: str
    document_type: str
    structure_type: str
    overall_confidence: float
    stakeholders: list[StakeholderEntity] = Field(default_factory=list)
    deliverables: list[DeliverableEntity] = Field(default_factory=list)
    deadlines: list[DeadlineEntity] = Field(default_factory=list)
    financials: list[FinancialEntity] = Field(default_factory=list)
    raw_text_preview: Optional[str] = Field(
        default=None, description="First 500 chars of raw text"
    )
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = Field(
        default=None, description="Processing time in milliseconds"
    )
    needs_review: bool = Field(
        default=False, description="Whether manual review is required"
    )
    review_reasons: list[str] = Field(
        default_factory=list, description="Reasons for review requirement"
    )
