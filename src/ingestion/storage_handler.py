"""
Cloud Storage handler for document ingestion.

Provides functionality to upload, download, and manage documents
in Google Cloud Storage with signed URL generation.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from src.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class StorageHandler:
    """Handler for Cloud Storage operations."""

    def __init__(
        self,
        raw_bucket: Optional[str] = None,
        processed_bucket: Optional[str] = None,
    ):
        """
        Initialize the storage handler.
        
        Args:
            raw_bucket: Bucket name for raw documents
            processed_bucket: Bucket name for processed results
        """
        self.client = storage.Client(project=settings.gcp_project_id)
        self.raw_bucket_name = raw_bucket or settings.gcs_raw_bucket
        self.processed_bucket_name = processed_bucket or settings.gcs_processed_bucket
        
        self._raw_bucket: Optional[storage.Bucket] = None
        self._processed_bucket: Optional[storage.Bucket] = None

    @property
    def raw_bucket(self) -> storage.Bucket:
        """Get or create the raw documents bucket."""
        if self._raw_bucket is None:
            self._raw_bucket = self.client.bucket(self.raw_bucket_name)
        return self._raw_bucket

    @property
    def processed_bucket(self) -> storage.Bucket:
        """Get or create the processed documents bucket."""
        if self._processed_bucket is None:
            self._processed_bucket = self.client.bucket(self.processed_bucket_name)
        return self._processed_bucket

    def upload_document(
        self,
        file_content: BinaryIO,
        document_id: str,
        filename: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a document to the raw bucket.
        
        Args:
            file_content: File content as binary stream
            document_id: Unique document identifier
            filename: Original filename
            content_type: MIME type of the file
            metadata: Optional metadata to attach
            
        Returns:
            The blob path in the bucket
        """
        # Create blob path with date prefix for organization
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        extension = Path(filename).suffix
        blob_path = f"{date_prefix}/{document_id}{extension}"
        
        blob = self.raw_bucket.blob(blob_path)
        
        # Set metadata
        blob.metadata = {
            "document_id": document_id,
            "original_filename": filename,
            "upload_timestamp": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }
        
        try:
            blob.upload_from_file(
                file_content,
                content_type=content_type,
                timeout=300,
            )
            logger.info(f"Uploaded document {document_id} to {blob_path}")
            return blob_path
            
        except GoogleCloudError as e:
            logger.error(f"Failed to upload document {document_id}: {e}")
            raise

    def download_document(self, blob_path: str, bucket_type: str = "raw") -> bytes:
        """
        Download a document from storage.
        
        Args:
            blob_path: Path to the blob in the bucket
            bucket_type: 'raw' or 'processed'
            
        Returns:
            Document content as bytes
        """
        bucket = self.raw_bucket if bucket_type == "raw" else self.processed_bucket
        blob = bucket.blob(blob_path)
        
        try:
            content = blob.download_as_bytes()
            logger.info(f"Downloaded document from {blob_path}")
            return content
            
        except GoogleCloudError as e:
            logger.error(f"Failed to download document from {blob_path}: {e}")
            raise

    def generate_signed_url(
        self,
        blob_path: str,
        bucket_type: str = "raw",
        expiration_minutes: int = 60,
        method: str = "GET",
    ) -> str:
        """
        Generate a signed URL for document access.
        
        Args:
            blob_path: Path to the blob
            bucket_type: 'raw' or 'processed'
            expiration_minutes: URL expiration time in minutes
            method: HTTP method (GET for download, PUT for upload)
            
        Returns:
            Signed URL string
        """
        bucket = self.raw_bucket if bucket_type == "raw" else self.processed_bucket
        blob = bucket.blob(blob_path)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method=method,
        )
        
        logger.debug(f"Generated signed URL for {blob_path}")
        return url

    def move_to_processed(self, source_blob_path: str, document_id: str) -> str:
        """
        Move a document from raw to processed bucket.
        
        Args:
            source_blob_path: Path in the raw bucket
            document_id: Document identifier
            
        Returns:
            New blob path in processed bucket
        """
        source_blob = self.raw_bucket.blob(source_blob_path)
        
        # Create destination path
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        extension = Path(source_blob_path).suffix
        dest_blob_path = f"{date_prefix}/{document_id}{extension}"
        
        # Copy to processed bucket
        dest_blob = self.raw_bucket.copy_blob(
            source_blob,
            self.processed_bucket,
            dest_blob_path,
        )
        
        # Delete from raw bucket
        source_blob.delete()
        
        logger.info(f"Moved document from {source_blob_path} to processed/{dest_blob_path}")
        return dest_blob_path

    def get_document_metadata(self, blob_path: str, bucket_type: str = "raw") -> dict:
        """
        Get metadata for a document.
        
        Args:
            blob_path: Path to the blob
            bucket_type: 'raw' or 'processed'
            
        Returns:
            Document metadata dictionary
        """
        bucket = self.raw_bucket if bucket_type == "raw" else self.processed_bucket
        blob = bucket.blob(blob_path)
        blob.reload()
        
        return {
            "blob_path": blob_path,
            "bucket": bucket.name,
            "size": blob.size,
            "content_type": blob.content_type,
            "created": blob.time_created.isoformat() if blob.time_created else None,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "metadata": blob.metadata or {},
        }

    def list_documents(
        self,
        prefix: Optional[str] = None,
        bucket_type: str = "raw",
        max_results: int = 100,
    ) -> list[dict]:
        """
        List documents in a bucket.
        
        Args:
            prefix: Optional path prefix filter
            bucket_type: 'raw' or 'processed'
            max_results: Maximum number of results
            
        Returns:
            List of document metadata dictionaries
        """
        bucket = self.raw_bucket if bucket_type == "raw" else self.processed_bucket
        blobs = bucket.list_blobs(prefix=prefix, max_results=max_results)
        
        documents = []
        for blob in blobs:
            documents.append({
                "blob_path": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "metadata": blob.metadata or {},
            })
        
        return documents

    def delete_document(self, blob_path: str, bucket_type: str = "raw") -> bool:
        """
        Delete a document from storage.
        
        Args:
            blob_path: Path to the blob
            bucket_type: 'raw' or 'processed'
            
        Returns:
            True if deleted successfully
        """
        bucket = self.raw_bucket if bucket_type == "raw" else self.processed_bucket
        blob = bucket.blob(blob_path)
        
        try:
            blob.delete()
            logger.info(f"Deleted document from {bucket_type}/{blob_path}")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"Failed to delete document from {blob_path}: {e}")
            raise


# Factory function for dependency injection
def get_storage_handler() -> StorageHandler:
    """Get a storage handler instance."""
    return StorageHandler()
