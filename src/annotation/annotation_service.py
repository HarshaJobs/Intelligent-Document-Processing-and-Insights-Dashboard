"""
Ground truth annotation service for training data.

Handles entity label schema, inter-annotator agreement calculation,
and model evaluation against ground truth.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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


@dataclass
class Annotation:
    """Annotation record for an entity."""

    entity_id: str
    document_id: str
    entity_type: str  # stakeholder, deliverable, deadline, financial
    annotated_value: dict  # The ground truth entity data
    annotator_id: str
    annotation_timestamp: datetime
    confidence: float = 1.0  # Annotator confidence
    notes: Optional[str] = None


@dataclass
class InterAnnotatorComparison:
    """Comparison between two annotators for the same entity."""

    entity_id: str
    document_id: str
    entity_type: str
    annotator1_id: str
    annotator2_id: str
    agreement_score: float  # 0.0 to 1.0
    differences: list[str]


class AnnotationService:
    """
    Service for managing ground truth annotations.
    
    Handles annotation storage, inter-annotator agreement calculation,
    and model evaluation against ground truth.
    """

    def __init__(self):
        """Initialize annotation service."""
        # In-memory storage for annotations (should be replaced with BigQuery/Storage)
        self._annotations: dict[str, list[Annotation]] = {}  # document_id -> annotations

    def add_annotation(
        self,
        document_id: str,
        entity_id: str,
        entity_type: str,
        annotated_value: dict,
        annotator_id: str,
        confidence: float = 1.0,
        notes: Optional[str] = None,
    ) -> Annotation:
        """
        Add an annotation for an entity.
        
        Args:
            document_id: Document identifier
            entity_id: Entity identifier
            entity_type: Type of entity (stakeholder, deliverable, deadline, financial)
            annotated_value: Ground truth entity data
            annotator_id: Identifier of the annotator
            confidence: Annotator confidence (0.0-1.0)
            notes: Optional annotation notes
            
        Returns:
            Created annotation
        """
        annotation = Annotation(
            entity_id=entity_id,
            document_id=document_id,
            entity_type=entity_type,
            annotated_value=annotated_value,
            annotator_id=annotator_id,
            annotation_timestamp=datetime.utcnow(),
            confidence=confidence,
            notes=notes,
        )
        
        if document_id not in self._annotations:
            self._annotations[document_id] = []
        
        # Remove existing annotation by same annotator for same entity
        self._annotations[document_id] = [
            a
            for a in self._annotations[document_id]
            if not (a.entity_id == entity_id and a.annotator_id == annotator_id)
        ]
        
        self._annotations[document_id].append(annotation)
        
        logger.info(
            f"Added annotation for {document_id}/{entity_id} by {annotator_id}"
        )
        
        return annotation

    def get_annotations(self, document_id: str) -> list[Annotation]:
        """Get all annotations for a document."""
        return self._annotations.get(document_id, [])

    def calculate_inter_annotator_agreement(
        self, document_id: str, entity_id: str, entity_type: str
    ) -> list[InterAnnotatorComparison]:
        """
        Calculate inter-annotator agreement for an entity.
        
        Compares annotations from different annotators and calculates
        agreement scores.
        
        Returns:
            List of comparisons between annotator pairs
        """
        annotations = [
            a
            for a in self.get_annotations(document_id)
            if a.entity_id == entity_id and a.entity_type == entity_type
        ]
        
        if len(annotations) < 2:
            return []
        
        comparisons = []
        
        # Compare all pairs of annotators
        for i, ann1 in enumerate(annotations):
            for ann2 in annotations[i + 1:]:
                agreement_score = self._calculate_agreement_score(
                    ann1.annotated_value, ann2.annotated_value, entity_type
                )
                differences = self._find_differences(
                    ann1.annotated_value, ann2.annotated_value, entity_type
                )
                
                comparison = InterAnnotatorComparison(
                    entity_id=entity_id,
                    document_id=document_id,
                    entity_type=entity_type,
                    annotator1_id=ann1.annotator_id,
                    annotator2_id=ann2.annotator_id,
                    agreement_score=agreement_score,
                    differences=differences,
                )
                
                comparisons.append(comparison)
        
        return comparisons

    def _calculate_agreement_score(
        self, value1: dict, value2: dict, entity_type: str
    ) -> float:
        """Calculate agreement score between two annotation values."""
        # Simple exact match for now
        # In production, this could use more sophisticated similarity metrics
        
        if entity_type == "stakeholder":
            # Compare key fields
            fields_to_compare = ["name", "stakeholder_type", "role", "organization"]
            matches = sum(
                1
                for field in fields_to_compare
                if value1.get(field) == value2.get(field)
            )
            return matches / len(fields_to_compare)
        
        elif entity_type == "deliverable":
            fields_to_compare = ["deliverable_name", "description", "milestone_id"]
            matches = sum(
                1
                for field in fields_to_compare
                if value1.get(field) == value2.get(field)
            )
            return matches / len(fields_to_compare)
        
        elif entity_type == "deadline":
            fields_to_compare = ["deadline_date", "deadline_type", "is_firm"]
            matches = sum(
                1
                for field in fields_to_compare
                if value1.get(field) == value2.get(field)
            )
            return matches / len(fields_to_compare)
        
        elif entity_type == "financial":
            fields_to_compare = ["amount", "currency", "financial_type", "due_date"]
            matches = sum(
                1
                for field in fields_to_compare
                if value1.get(field) == value2.get(field)
            )
            return matches / len(fields_to_compare)
        
        return 0.0

    def _find_differences(
        self, value1: dict, value2: dict, entity_type: str
    ) -> list[str]:
        """Find differences between two annotation values."""
        differences = []
        
        all_keys = set(value1.keys()) | set(value2.keys())
        
        for key in all_keys:
            val1 = value1.get(key)
            val2 = value2.get(key)
            
            if val1 != val2:
                differences.append(f"{key}: '{val1}' vs '{val2}'")
        
        return differences

    def evaluate_model_performance(
        self,
        document_id: str,
        model_result: ExtractionResult,
        ground_truth_annotations: list[Annotation],
    ) -> dict:
        """
        Evaluate model performance against ground truth annotations.
        
        Calculates precision, recall, F1 score, and other metrics.
        
        Args:
            document_id: Document identifier
            model_result: Model extraction result
            ground_truth_annotations: Ground truth annotations
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Group annotations by entity type
        gt_by_type = {}
        for ann in ground_truth_annotations:
            if ann.entity_type not in gt_by_type:
                gt_by_type[ann.entity_type] = []
            gt_by_type[ann.entity_type].append(ann)
        
        # Calculate metrics per entity type
        metrics = {}
        
        for entity_type in ["stakeholder", "deliverable", "deadline", "financial"]:
            gt_entities = gt_by_type.get(entity_type, [])
            
            if entity_type == "stakeholder":
                model_entities = model_result.stakeholders
            elif entity_type == "deliverable":
                model_entities = model_result.deliverables
            elif entity_type == "deadline":
                model_entities = model_result.deadlines
            else:  # financial
                model_entities = model_result.financials
            
            precision, recall, f1 = self._calculate_prf1(
                model_entities, gt_entities, entity_type
            )
            
            metrics[entity_type] = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "true_positives": 0,  # TODO: Calculate actual TP/FP/FN
                "false_positives": 0,
                "false_negatives": len(gt_entities) - len(model_entities),
            }
        
        # Overall metrics
        overall_precision = sum(m["precision"] for m in metrics.values()) / len(metrics)
        overall_recall = sum(m["recall"] for m in metrics.values()) / len(metrics)
        overall_f1 = 2 * (overall_precision * overall_recall) / (
            overall_precision + overall_recall
        ) if (overall_precision + overall_recall) > 0 else 0.0
        
        return {
            "document_id": document_id,
            "overall_metrics": {
                "precision": overall_precision,
                "recall": overall_recall,
                "f1_score": overall_f1,
            },
            "entity_type_metrics": metrics,
            "evaluation_timestamp": datetime.utcnow().isoformat(),
        }

    def _calculate_prf1(
        self, model_entities: list, gt_entities: list[Annotation], entity_type: str
    ) -> tuple[float, float, float]:
        """Calculate precision, recall, and F1 score."""
        # Simplified calculation - in production, use entity matching logic
        # For now, assume perfect match if counts are similar
        
        tp = min(len(model_entities), len(gt_entities))
        fp = max(0, len(model_entities) - len(gt_entities))
        fn = max(0, len(gt_entities) - len(model_entities))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        
        return precision, recall, f1


def get_annotation_service() -> AnnotationService:
    """Get an annotation service instance."""
    return AnnotationService()
