"""
Automated weekly report generation using GenAI.

Generates synthesis reports of processed documents for PM review.
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

import google.generativeai as genai

from src.config import get_settings
from src.storage.bigquery_loader import get_bigquery_loader

logger = logging.getLogger(__name__)
settings = get_settings()


class WeeklyReportGenerator:
    """
    Generator for automated weekly reports using Gemini API.
    
    Synthesizes document processing insights and generates
    reports for project manager review.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize report generator.
        
        Args:
            api_key: Gemini API key (defaults to config)
            model_name: Model name (defaults to config)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Weekly Report Generator with model: {self.model_name}")

    def generate_weekly_report(
        self,
        week_start: Optional[date] = None,
        week_end: Optional[date] = None,
        include_details: bool = True,
    ) -> dict:
        """
        Generate weekly report for processed documents.
        
        Args:
            week_start: Start date of the week (defaults to last Monday)
            week_end: End date of the week (defaults to last Sunday)
            include_details: Whether to include detailed entity breakdown
            
        Returns:
            Dictionary with report data and generated content
        """
        # Calculate week dates if not provided
        if not week_start or not week_end:
            today = date.today()
            days_since_monday = today.weekday()
            week_end = today - timedelta(days=days_since_monday + 1)  # Last Sunday
            week_start = week_end - timedelta(days=6)  # Previous Monday
        
        logger.info(f"Generating weekly report for {week_start} to {week_end}")
        
        # Fetch weekly metrics from BigQuery
        metrics = self._fetch_weekly_metrics(week_start, week_end)
        
        # Build prompt for Gemini
        prompt = self._build_report_prompt(metrics, week_start, week_end, include_details)
        
        # Generate report content using Gemini
        try:
            response = self.model.generate_content(prompt)
            report_content = response.text.strip()
            
            logger.info(f"Generated weekly report content ({len(report_content)} chars)")
            
        except Exception as e:
            logger.error(f"Failed to generate report content: {e}", exc_info=True)
            report_content = self._generate_fallback_report(metrics, week_start, week_end)
        
        # Create report record
        report_id = str(uuid.uuid4())
        report_data = {
            "report_id": report_id,
            "report_date": date.today().isoformat(),
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "documents_processed": metrics.get("documents_processed", 0),
            "documents_pending": metrics.get("documents_pending", 0),
            "avg_confidence": metrics.get("avg_confidence", 0.0),
            "documents_flagged_for_review": metrics.get("review_required_count", 0),
            "stakeholders_extracted": metrics.get("stakeholders_extracted", 0),
            "deliverables_extracted": metrics.get("deliverables_extracted", 0),
            "deadlines_extracted": metrics.get("deadlines_extracted", 0),
            "report_content": report_content,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": "system",
        }
        
        # Save to BigQuery
        self._save_report_to_bigquery(report_data)
        
        return report_data

    def _fetch_weekly_metrics(
        self, week_start: date, week_end: date
    ) -> dict:
        """
        Fetch weekly processing metrics from BigQuery.
        
        Args:
            week_start: Week start date
            week_end: Week end date
            
        Returns:
            Dictionary with metrics
        """
        # TODO: Query BigQuery for actual metrics
        # For now, return placeholder data
        
        from google.cloud import bigquery
        
        client = bigquery.Client(
            project=settings.gcp_project_id, location=settings.bigquery_location
        )
        
        query = f"""
        SELECT
            COUNT(DISTINCT document_id) AS documents_processed,
            COUNTIF(processing_status IN ('pending', 'processing')) AS documents_pending,
            AVG(overall_confidence) AS avg_confidence,
            COUNTIF(processing_status = 'review_required') AS review_required_count
        FROM `{settings.documents_table}`
        WHERE DATE(upload_timestamp) BETWEEN '{week_start}' AND '{week_end}'
        """
        
        try:
            job = client.query(query)
            results = job.result()
            row = next(iter(results), None)
            
            if row:
                metrics = {
                    "documents_processed": row.documents_processed or 0,
                    "documents_pending": row.documents_pending or 0,
                    "avg_confidence": float(row.avg_confidence or 0.0),
                    "review_required_count": row.review_required_count or 0,
                }
            else:
                metrics = {
                    "documents_processed": 0,
                    "documents_pending": 0,
                    "avg_confidence": 0.0,
                    "review_required_count": 0,
                }
            
            # Fetch entity counts
            entity_query = f"""
            SELECT
                COUNT(DISTINCT entity_id) AS count
            FROM `{settings.stakeholders_table}`
            WHERE DATE(extraction_timestamp) BETWEEN '{week_start}' AND '{week_end}'
            """
            
            job = client.query(entity_query)
            results = job.result()
            row = next(iter(results), None)
            metrics["stakeholders_extracted"] = row.count if row else 0
            
            # Similar for deliverables and deadlines
            # (Simplified for brevity)
            metrics["deliverables_extracted"] = 0
            metrics["deadlines_extracted"] = 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to fetch weekly metrics: {e}", exc_info=True)
            return {
                "documents_processed": 0,
                "documents_pending": 0,
                "avg_confidence": 0.0,
                "review_required_count": 0,
                "stakeholders_extracted": 0,
                "deliverables_extracted": 0,
                "deadlines_extracted": 0,
            }

    def _build_report_prompt(
        self, metrics: dict, week_start: date, week_end: date, include_details: bool
    ) -> str:
        """Build prompt for Gemini to generate report."""
        prompt = f"""You are a project management assistant. Generate a concise weekly summary report for document processing activities.

Week: {week_start} to {week_end}

Processing Metrics:
- Documents Processed: {metrics.get('documents_processed', 0)}
- Documents Pending: {metrics.get('documents_pending', 0)}
- Average Confidence Score: {metrics.get('avg_confidence', 0.0):.2f}
- Documents Flagged for Review: {metrics.get('review_required_count', 0)}
- Stakeholders Extracted: {metrics.get('stakeholders_extracted', 0)}
- Deliverables Extracted: {metrics.get('deliverables_extracted', 0)}
- Deadlines Extracted: {metrics.get('deadlines_extracted', 0)}

Generate a professional weekly report that includes:
1. Executive Summary (2-3 sentences)
2. Processing Volume Highlights
3. Quality Metrics and Confidence Trends
4. Items Requiring Attention (if any)
5. Recommendations for Next Week

Keep the tone professional and concise. Focus on actionable insights.
"""
        return prompt

    def _generate_fallback_report(
        self, metrics: dict, week_start: date, week_end: date
    ) -> str:
        """Generate a fallback report if Gemini fails."""
        return f"""Weekly Processing Report
Week: {week_start} to {week_end}

Executive Summary:
During this week, {metrics.get('documents_processed', 0)} documents were processed with an average confidence score of {metrics.get('avg_confidence', 0.0):.2f}. {metrics.get('review_required_count', 0)} documents require manual review.

Processing Volume:
- Total Documents Processed: {metrics.get('documents_processed', 0)}
- Pending Documents: {metrics.get('documents_pending', 0)}
- Stakeholders Extracted: {metrics.get('stakeholders_extracted', 0)}
- Deliverables Extracted: {metrics.get('deliverables_extracted', 0)}
- Deadlines Extracted: {metrics.get('deadlines_extracted', 0)}

Quality Metrics:
- Average Confidence: {metrics.get('avg_confidence', 0.0):.2f}
- Review Required: {metrics.get('review_required_count', 0)} documents

Recommendations:
- Monitor documents with low confidence scores
- Review flagged documents to improve extraction accuracy
"""

    def _save_report_to_bigquery(self, report_data: dict) -> None:
        """Save generated report to BigQuery."""
        try:
            from google.cloud import bigquery
            
            client = bigquery.Client(
                project=settings.gcp_project_id, location=settings.bigquery_location
            )
            
            table_id = f"{settings.gcp_project_id}.{settings.bigquery_dataset}.weekly_reports"
            
            errors = client.insert_rows_json(table_id, [report_data])
            if errors:
                logger.error(f"Errors inserting weekly report: {errors}")
            else:
                logger.info(f"Saved weekly report {report_data['report_id']} to BigQuery")
                
        except Exception as e:
            logger.error(f"Failed to save report to BigQuery: {e}", exc_info=True)


def get_report_generator(
    api_key: Optional[str] = None, model_name: Optional[str] = None
) -> WeeklyReportGenerator:
    """Get a weekly report generator instance."""
    return WeeklyReportGenerator(api_key=api_key, model_name=model_name)
