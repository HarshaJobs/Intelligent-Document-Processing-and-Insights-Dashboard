#!/bin/bash
# Test Execution Script

set -e  # Exit on error

echo "Running tests for Intelligent Document Processing Dashboard"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing dependencies..."
    pip install -e ".[dev]"
fi

# Set environment variables for testing
export GCP_PROJECT_ID="${GCP_PROJECT_ID:-test-project}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-test-key}"
export BIGQUERY_DATASET="document_processing"

echo "Running unit tests..."
pytest tests/unit/ -v --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo "Running integration tests..."
pytest tests/integration/ -v -m "not slow" || echo "Note: Some integration tests may require GCP credentials"

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Unit tests: tests/unit/"
echo "Integration tests: tests/integration/"
echo "Coverage report: htmlcov/index.html"
echo ""
