"""
Annotation module for ground truth data management.
"""

from src.annotation.annotation_service import (
    Annotation,
    AnnotationService,
    InterAnnotatorComparison,
    get_annotation_service,
)

__all__ = [
    "Annotation",
    "AnnotationService",
    "InterAnnotatorComparison",
    "get_annotation_service",
]
