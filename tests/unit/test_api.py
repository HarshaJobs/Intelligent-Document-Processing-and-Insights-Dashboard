"""
Unit tests for FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_check(self, client):
        """Test readiness check."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data

    def test_liveness_check(self, client):
        """Test liveness check."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["docs"] == "/docs"


class TestDocumentEndpoints:
    """Tests for document endpoints."""

    def test_list_documents(self, client):
        """Test listing documents returns empty list."""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total_count" in data
        assert data["total_count"] == 0

    def test_get_document_status(self, client):
        """Test getting document status."""
        response = client.get("/api/v1/documents/test-doc-id/status")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-id"
        assert "status" in data

    def test_get_review_queue(self, client):
        """Test getting review queue."""
        response = client.get("/api/v1/documents/review-queue")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data

    def test_upload_invalid_file_type(self, client):
        """Test uploading unsupported file type."""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.exe", b"content", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
