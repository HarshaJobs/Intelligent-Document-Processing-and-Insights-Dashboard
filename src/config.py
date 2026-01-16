"""
Configuration management for Document Processing Dashboard.

Loads settings from environment variables with sensible defaults
for development.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GCP Configuration
    gcp_project_id: str = Field(default="", description="GCP Project ID")
    gcp_region: str = Field(default="us-central1", description="GCP Region")

    # Gemini API
    gemini_api_key: str = Field(default="", description="Gemini API Key")
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp", description="Gemini model to use"
    )

    # Cloud Storage
    gcs_raw_bucket: str = Field(
        default="doc-processing-raw", description="Bucket for raw documents"
    )
    gcs_processed_bucket: str = Field(
        default="doc-processing-processed", description="Bucket for processed results"
    )

    # BigQuery
    bigquery_dataset: str = Field(
        default="document_processing", description="BigQuery dataset name"
    )
    bigquery_location: str = Field(default="US", description="BigQuery location")

    # Application
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment name"
    )

    # Confidence Thresholds
    low_confidence_threshold: float = Field(
        default=0.7, description="Threshold for flagging low confidence extractions"
    )
    review_required_threshold: float = Field(
        default=0.5, description="Threshold for mandatory manual review"
    )

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8080, description="API port")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def documents_table(self) -> str:
        """Full BigQuery table path for documents."""
        return f"{self.gcp_project_id}.{self.bigquery_dataset}.documents"

    @property
    def stakeholders_table(self) -> str:
        """Full BigQuery table path for stakeholders."""
        return f"{self.gcp_project_id}.{self.bigquery_dataset}.stakeholders"

    @property
    def deliverables_table(self) -> str:
        """Full BigQuery table path for deliverables."""
        return f"{self.gcp_project_id}.{self.bigquery_dataset}.deliverables"

    @property
    def deadlines_table(self) -> str:
        """Full BigQuery table path for deadlines."""
        return f"{self.gcp_project_id}.{self.bigquery_dataset}.deadlines"

    @property
    def processing_log_table(self) -> str:
        """Full BigQuery table path for processing log."""
        return f"{self.gcp_project_id}.{self.bigquery_dataset}.processing_log"

    @property
    def review_queue_table(self) -> str:
        """Full BigQuery table path for review queue."""
        return f"{self.gcp_project_id}.{self.bigquery_dataset}.review_queue"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
