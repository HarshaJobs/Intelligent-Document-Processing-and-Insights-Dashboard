"""
Health check routes for the API.
"""

from datetime import datetime

from fastapi import APIRouter, Response

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """
    Basic health check endpoint.
    
    Returns service status and timestamp.
    """
    return {
        "status": "healthy",
        "service": "document-processing-api",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check() -> dict:
    """
    Readiness check for Kubernetes/Cloud Run.
    
    Checks if the service is ready to accept traffic.
    """
    # TODO: Add checks for dependencies (BigQuery, GCS, etc.)
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "api": True,
            "bigquery": True,  # Placeholder
            "storage": True,   # Placeholder
        },
    }


@router.get("/health/live")
async def liveness_check(response: Response) -> dict:
    """
    Liveness check for Kubernetes/Cloud Run.
    
    Returns 200 if the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
