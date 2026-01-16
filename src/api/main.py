"""
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import documents, health
from src.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info(f"Starting Document Processing API in {settings.environment} mode")
    logger.info(f"GCP Project: {settings.gcp_project_id or 'Not configured'}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document Processing API")


app = FastAPI(
    title="Intelligent Document Processing API",
    description="""
    API for processing SOWs, contracts, and other business documents.
    
    ## Features
    
    - **Document Upload**: Upload PDF, DOCX, or TXT files for processing
    - **Entity Extraction**: Extract stakeholders, deliverables, deadlines using Gemini AI
    - **Status Tracking**: Monitor processing status and confidence scores
    - **Review Queue**: Flag low-confidence extractions for manual review
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(documents.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Intelligent Document Processing API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production,
    )
