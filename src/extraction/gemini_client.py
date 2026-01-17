"""
Gemini API client for entity extraction from documents.

Handles communication with Google's Gemini API for extracting
structured entities from SOWs, contracts, and other documents.
"""

import json
import logging
from typing import Any, Optional

import google.generativeai as genai

from src.api.models.document import DocumentStructure, DocumentType
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiExtractionClient:
    """
    Client for extracting entities using Google Gemini API.
    
    Handles document processing, prompt construction, and response parsing.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to config)
            model_name: Model name (defaults to config)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini client with model: {self.model_name}")

    def _build_extraction_prompt(
        self,
        document_text: str,
        document_type: DocumentType,
        structure_type: DocumentStructure,
    ) -> str:
        """
        Build extraction prompt for Gemini API.
        
        Args:
            document_text: Document content as text
            document_type: Type of document (SOW, contract, etc.)
            structure_type: Structure type (structured, semi-structured, unstructured)
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""You are an expert document analyst specializing in extracting structured information from {document_type.value} documents.

Analyze the following document (which is {structure_type.value}) and extract the following entities:

1. STAKEHOLDERS: People or organizations involved
   - Extract: name, type (client/vendor/contact/signatory/project_manager), role, organization, email, phone
   - Include confidence scores (0.0-1.0) for each extraction

2. DELIVERABLES: Products, services, or outcomes to be delivered
   - Extract: name, description, acceptance_criteria, milestone_id, dependencies
   - Include confidence scores

3. DEADLINES: Important dates and milestones
   - Extract: type (start/end/milestone/payment/review), date, description, associated_deliverable, is_firm
   - Include confidence scores

4. FINANCIAL: Financial terms and amounts
   - Extract: type (total_value/payment/penalty/milestone_payment), amount, currency, description, payment_terms, due_date
   - Include confidence scores

Return ONLY a valid JSON object with this exact structure:
{{
    "overall_confidence": <float 0.0-1.0>,
    "stakeholders": [
        {{
            "name": "<string>",
            "stakeholder_type": "<client|vendor|contact|signatory|project_manager>",
            "role": "<string or null>",
            "organization": "<string or null>",
            "email": "<string or null>",
            "phone": "<string or null>",
            "confidence": <float 0.0-1.0>,
            "source_text": "<excerpt from document>"
        }}
    ],
    "deliverables": [
        {{
            "deliverable_name": "<string>",
            "description": "<string or null>",
            "acceptance_criteria": "<string or null>",
            "milestone_id": "<string or null>",
            "dependencies": ["<string>"],
            "confidence": <float 0.0-1.0>,
            "source_text": "<excerpt from document>"
        }}
    ],
    "deadlines": [
        {{
            "deadline_type": "<start|end|milestone|payment|review>",
            "deadline_date": "<YYYY-MM-DD>",
            "description": "<string or null>",
            "associated_deliverable": "<string or null>",
            "is_firm": <boolean>,
            "confidence": <float 0.0-1.0>,
            "source_text": "<excerpt from document>"
        }}
    ],
    "financials": [
        {{
            "financial_type": "<total_value|payment|penalty|milestone_payment>",
            "amount": <float or null>,
            "currency": "<string, default USD>",
            "description": "<string or null>",
            "payment_terms": "<string or null>",
            "due_date": "<YYYY-MM-DD or null>",
            "confidence": <float 0.0-1.0>,
            "source_text": "<excerpt from document>"
        }}
    ]
}}

Document text (first 50000 characters):
{document_text[:50000]}

Extract entities and return ONLY the JSON object:"""

        return base_prompt

    def extract_entities(
        self,
        document_text: str,
        document_type: DocumentType = DocumentType.OTHER,
        structure_type: DocumentStructure = DocumentStructure.UNSTRUCTURED,
    ) -> dict[str, Any]:
        """
        Extract entities from document text using Gemini API.
        
        Args:
            document_text: Full document text content
            document_type: Type of document
            structure_type: Structure type of document
            
        Returns:
            Dictionary with extracted entities and metadata
            
        Raises:
            Exception: If extraction fails
        """
        try:
            # Build prompt
            prompt = self._build_extraction_prompt(
                document_text, document_type, structure_type
            )
            
            logger.info(
                f"Calling Gemini API for extraction (doc_type={document_type.value}, "
                f"structure={structure_type.value}, text_length={len(document_text)})"
            )
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            # Parse response text
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks if present)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.debug(f"Response text: {response_text[:500]}")
                raise ValueError(f"Invalid JSON response from Gemini: {e}")
            
            # Validate and normalize result
            normalized_result = self._normalize_extraction_result(result)
            
            logger.info(
                f"Extraction complete: {len(normalized_result.get('stakeholders', []))} stakeholders, "
                f"{len(normalized_result.get('deliverables', []))} deliverables, "
                f"{len(normalized_result.get('deadlines', []))} deadlines, "
                f"{len(normalized_result.get('financials', []))} financials"
            )
            
            return normalized_result
            
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}", exc_info=True)
            raise

    def _normalize_extraction_result(self, raw_result: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize and validate extraction result.
        
        Args:
            raw_result: Raw result from Gemini API
            
        Returns:
            Normalized result dictionary
        """
        # Ensure required fields exist
        normalized = {
            "overall_confidence": float(raw_result.get("overall_confidence", 0.5)),
            "stakeholders": raw_result.get("stakeholders", []),
            "deliverables": raw_result.get("deliverables", []),
            "deadlines": raw_result.get("deadlines", []),
            "financials": raw_result.get("financials", []),
        }
        
        # Validate confidence scores
        normalized["overall_confidence"] = max(
            0.0, min(1.0, normalized["overall_confidence"])
        )
        
        # Normalize entity lists
        for entity_list in [
            "stakeholders",
            "deliverables",
            "deadlines",
            "financials",
        ]:
            if not isinstance(normalized[entity_list], list):
                normalized[entity_list] = []
            
            # Ensure each entity has a confidence score
            for entity in normalized[entity_list]:
                if "confidence" not in entity:
                    entity["confidence"] = normalized["overall_confidence"]
                else:
                    entity["confidence"] = max(
                        0.0, min(1.0, float(entity["confidence"]))
                    )
        
        return normalized


def get_gemini_client(api_key: Optional[str] = None, model_name: Optional[str] = None) -> GeminiExtractionClient:
    """Get a Gemini extraction client instance."""
    return GeminiExtractionClient(api_key=api_key, model_name=model_name)