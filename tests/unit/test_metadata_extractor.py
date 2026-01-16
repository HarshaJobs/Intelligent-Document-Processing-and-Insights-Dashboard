"""
Unit tests for document metadata extraction.
"""

import pytest

from src.api.models.document import DocumentStructure, DocumentType
from src.ingestion.metadata_extractor import DocumentMetadataExtractor


@pytest.fixture
def extractor():
    """Create metadata extractor instance."""
    return DocumentMetadataExtractor()


class TestDocumentTypeDetection:
    """Tests for document type detection."""

    def test_detect_sow(self, extractor):
        """Test SOW detection."""
        text = """
        STATEMENT OF WORK
        
        Project Scope: This SOW outlines the deliverables and milestones
        for the software development project.
        """
        doc_type = extractor.detect_document_type(text)
        assert doc_type == DocumentType.SOW

    def test_detect_contract(self, extractor):
        """Test contract detection."""
        text = """
        SERVICE AGREEMENT
        
        This Agreement is entered into by and between the parties.
        The terms and conditions set forth herein are binding.
        Both parties hereby agree to the following terms.
        """
        doc_type = extractor.detect_document_type(text)
        assert doc_type == DocumentType.CONTRACT

    def test_detect_email(self, extractor):
        """Test email detection."""
        text = """
        From: john@example.com
        To: jane@example.com
        Subject: Project Update
        
        Hi Jane,
        
        Please find attached the latest report.
        """
        doc_type = extractor.detect_document_type(text)
        assert doc_type == DocumentType.EMAIL

    def test_detect_msa(self, extractor):
        """Test MSA detection."""
        text = """
        MASTER SERVICE AGREEMENT
        
        This MSA governs the relationship between the parties
        and serves as a framework agreement for all future work.
        """
        doc_type = extractor.detect_document_type(text)
        assert doc_type == DocumentType.MSA

    def test_detect_amendment(self, extractor):
        """Test amendment detection."""
        text = """
        AMENDMENT NO. 1
        
        This Amendment modifies the original agreement dated January 1, 2024.
        The following changes are hereby incorporated.
        """
        doc_type = extractor.detect_document_type(text)
        assert doc_type == DocumentType.AMENDMENT

    def test_detect_other(self, extractor):
        """Test fallback to OTHER type."""
        text = "Just some random text without any keywords."
        doc_type = extractor.detect_document_type(text)
        assert doc_type == DocumentType.OTHER


class TestStructureDetection:
    """Tests for document structure detection."""

    def test_detect_structured(self, extractor):
        """Test structured document detection."""
        text = """
        Table of Contents
        
        Section 1. Introduction
        1.1 Purpose
        1.2 Scope
        
        Section 2. Definitions
        Article 2.1
        Clause 2.1.1
        """
        structure = extractor.detect_structure(text)
        assert structure == DocumentStructure.STRUCTURED

    def test_detect_semi_structured(self, extractor):
        """Test semi-structured document detection."""
        text = """
        As discussed in our meeting, please find attached
        the updated proposal regarding the project timeline.
        
        1. Phase 1 will complete by March.
        """
        structure = extractor.detect_structure(text)
        assert structure == DocumentStructure.SEMI_STRUCTURED

    def test_detect_unstructured(self, extractor):
        """Test unstructured document detection."""
        text = """
        Hey team,
        
        Just wanted to share some thoughts on the project.
        Let me know what you think about moving forward.
        
        Thanks!
        """
        structure = extractor.detect_structure(text)
        assert structure == DocumentStructure.UNSTRUCTURED


class TestTextExtraction:
    """Tests for text extraction."""

    def test_extract_text_from_txt(self, extractor):
        """Test text extraction from TXT file."""
        content = b"This is a test document."
        text = extractor.extract_text(content, "test.txt")
        assert text == "This is a test document."

    def test_extract_text_unsupported_type(self, extractor):
        """Test unsupported file type raises error."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            extractor.extract_text(b"content", "test.xyz")


class TestFullMetadataExtraction:
    """Tests for complete metadata extraction."""

    def test_extract_metadata(self, extractor):
        """Test full metadata extraction."""
        content = b"""STATEMENT OF WORK

Section 1. Project Scope
This SOW outlines the deliverables for the project.

Section 2. Timeline
All milestones must be completed by the deadline.
"""
        metadata = extractor.extract_metadata(content, "test.txt")
        
        assert metadata["document_type"] == DocumentType.SOW
        assert metadata["structure_type"] == DocumentStructure.STRUCTURED
        assert metadata["raw_text_length"] > 0
        assert metadata["filename"] == "test.txt"
        assert metadata["file_size"] == len(content)
