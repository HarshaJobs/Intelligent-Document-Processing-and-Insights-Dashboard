"""
Entity extraction module using Gemini API.

Provides extraction pipeline for stakeholders, deliverables, deadlines, and financials.
"""

from src.extraction.extraction_pipeline import (
    EntityExtractionPipeline,
    get_extraction_pipeline,
)
from src.extraction.gemini_client import GeminiExtractionClient, get_gemini_client

__all__ = [
    "EntityExtractionPipeline",
    "GeminiExtractionClient",
    "get_extraction_pipeline",
    "get_gemini_client",
]
