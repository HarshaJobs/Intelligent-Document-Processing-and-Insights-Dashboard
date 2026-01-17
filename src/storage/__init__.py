"""
BigQuery storage module for entity persistence.
"""

from src.storage.bigquery_loader import BigQueryEntityLoader, get_bigquery_loader

__all__ = ["BigQueryEntityLoader", "get_bigquery_loader"]
