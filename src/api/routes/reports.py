"""
Weekly report generation routes.
"""

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.reports import get_report_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportGenerateRequest(BaseModel):
    """Request model for report generation."""

    week_start: Optional[date] = None
    week_end: Optional[date] = None
    include_details: bool = True


@router.post("/generate")
async def generate_weekly_report(request: ReportGenerateRequest) -> dict:
    """
    Generate a weekly report for processed documents.
    
    Can be called manually or by Cloud Scheduler.
    """
    try:
        report_generator = get_report_generator()
        
        report_data = report_generator.generate_weekly_report(
            week_start=request.week_start,
            week_end=request.week_end,
            include_details=request.include_details,
        )
        
        logger.info(f"Generated weekly report: {report_data['report_id']}")
        
        return {
            "status": "success",
            "report_id": report_data["report_id"],
            "week_start": report_data["week_start"],
            "week_end": report_data["week_end"],
            "generated_at": report_data["generated_at"],
            "metrics": {
                "documents_processed": report_data["documents_processed"],
                "avg_confidence": report_data["avg_confidence"],
                "review_required": report_data["documents_flagged_for_review"],
            },
        }
        
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/latest")
async def get_latest_report() -> dict:
    """Get the latest weekly report."""
    # TODO: Query BigQuery for latest report
    # For now, return placeholder
    return {
        "message": "Latest report endpoint - implementation pending",
        "note": "Query BigQuery weekly_reports table for latest report",
    }
