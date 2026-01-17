# Test Execution Script (PowerShell for Windows)

Write-Host "Running tests for Intelligent Document Processing Dashboard" -ForegroundColor Green
Write-Host ""

# Check if pytest is installed
if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Host "pytest not found. Installing dependencies..." -ForegroundColor Yellow
    pip install -e ".[dev]"
}

# Set environment variables for testing
if (-not $env:GCP_PROJECT_ID) {
    $env:GCP_PROJECT_ID = "test-project"
}
if (-not $env:GEMINI_API_KEY) {
    $env:GEMINI_API_KEY = "test-key"
}
$env:BIGQUERY_DATASET = "document_processing"

Write-Host "Running unit tests..." -ForegroundColor Yellow
pytest tests/unit/ -v --cov=src --cov-report=term-missing --cov-report=html

Write-Host ""
Write-Host "Running integration tests..." -ForegroundColor Yellow
pytest tests/integration/ -v -m "not slow" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Note: Some integration tests may require GCP credentials" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Test Summary" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Unit tests: tests/unit/"
Write-Host "Integration tests: tests/integration/"
Write-Host "Coverage report: htmlcov/index.html"
Write-Host ""
