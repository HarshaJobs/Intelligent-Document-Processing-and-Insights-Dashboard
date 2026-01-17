"""
Unit tests for Gemini API client.

Tests entity extraction using Gemini API with mock responses.
"""

import json
import pytest
from unittest.mock import Mock, patch

from src.api.models.document import DocumentType, DocumentStructure
from src.extraction.gemini_client import GeminiExtractionClient


class TestGeminiClient:
    """Unit tests for Gemini extraction client."""

    @pytest.fixture
    def sample_extraction_response(self):
        """Sample Gemini API response."""
        return {
            "overall_confidence": 0.85,
            "stakeholders": [
                {
                    "name": "John Smith",
                    "stakeholder_type": "project_manager",
                    "role": "Project Manager",
                    "organization": "Tech Solutions Inc.",
                    "email": "john.smith@techsolutions.com",
                    "phone": None,
                    "confidence": 0.9,
                    "source_text": "Project Manager: John Smith",
                }
            ],
            "deliverables": [
                {
                    "deliverable_name": "System Design Document",
                    "description": "Detailed system design specification",
                    "acceptance_criteria": None,
                    "milestone_id": None,
                    "dependencies": [],
                    "confidence": 0.85,
                    "source_text": "DELIVERABLES: 1. System Design Document",
                }
            ],
            "deadlines": [
                {
                    "deadline_type": "milestone",
                    "deadline_date": "2024-03-15",
                    "description": "Due date for design document",
                    "associated_deliverable": "System Design Document",
                    "is_firm": True,
                    "confidence": 0.8,
                    "source_text": "Due: 2024-03-15",
                }
            ],
            "financials": [
                {
                    "financial_type": "total_value",
                    "amount": 150000.0,
                    "currency": "USD",
                    "description": "Total Project Value",
                    "payment_terms": None,
                    "due_date": None,
                    "confidence": 0.88,
                    "source_text": "Total Project Value: $150,000 USD",
                }
            ],
        }

    def test_normalize_extraction_result(self, sample_extraction_response):
        """Test normalization of extraction results."""
        client = GeminiExtractionClient(api_key="test-key", model_name="test-model")
        
        normalized = client._normalize_extraction_result(sample_extraction_response)
        
        assert normalized["overall_confidence"] == 0.85
        assert len(normalized["stakeholders"]) == 1
        assert len(normalized["deliverables"]) == 1
        assert len(normalized["deadlines"]) == 1
        assert len(normalized["financials"]) == 1
        
        # Validate confidence scores are normalized
        assert 0.0 <= normalized["overall_confidence"] <= 1.0
        for entity in normalized["stakeholders"]:
            assert 0.0 <= entity["confidence"] <= 1.0

    def test_build_extraction_prompt(self):
        """Test prompt construction."""
        client = GeminiExtractionClient(api_key="test-key", model_name="test-model")
        
        prompt = client._build_extraction_prompt(
            document_text="Sample document text",
            document_type=DocumentType.SOW,
            structure_type=DocumentStructure.STRUCTURED,
        )
        
        assert "STAKEHOLDERS" in prompt
        assert "DELIVERABLES" in prompt
        assert "DEADLINES" in prompt
        assert "FINANCIAL" in prompt
        assert "JSON" in prompt

    @patch("src.extraction.gemini_client.genai.GenerativeModel")
    def test_extract_entities_mock(self, mock_model_class, sample_extraction_response):
        """Test entity extraction with mocked Gemini API."""
        # Mock the model response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(sample_extraction_response)
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        client = GeminiExtractionClient(api_key="test-key", model_name="test-model")
        client.model = mock_model
        
        result = client.extract_entities(
            document_text="Sample document",
            document_type=DocumentType.SOW,
            structure_type=DocumentStructure.STRUCTURED,
        )
        
        assert result["overall_confidence"] == 0.85
        assert len(result["stakeholders"]) == 1
        assert result["stakeholders"][0]["name"] == "John Smith"
