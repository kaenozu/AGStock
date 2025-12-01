import os
import json
import logging
from typing import Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Determine storage mode from environment
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")  # "local" or "gcs"

class CloudStorageManager:
    """
    Abstraction layer for file storage.
    Supports local filesystem and Google Cloud Storage (GCS).
    """
    def __init__(self, storage_mode: str = STORAGE_MODE):
        self.storage_mode = storage_mode
        self.gcs_client = None
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "agstock-data")
        
        if self.storage_mode == "gcs":
            try:
                from google.cloud import storage
                self.gcs_client = storage.Client()
                logger.info(f"CloudStorageManager initialized with GCS (bucket: {self.bucket_name})")
            except ImportError:
                logger.warning("google-cloud-storage not installed. Falling back to local storage.")
                self.storage_mode = "local"
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}. Falling back to local storage.")
                self.storage_mode = "local"
        
        if self.storage_mode == "local":
            logger.info("CloudStorageManager initialized with local filesystem")

    def save_json(self, data: Any, file_path: str):
        """Save JSON data to storage."""
        if self.storage_mode == "gcs":
            self._save_gcs(json.dumps(data, ensure_ascii=False, indent=2), file_path)
        else:
            self._save_local(json.dumps(data, ensure_ascii=False, indent=2), file_path)

    def load_json(self, file_path: str) -> Optional[Any]:
        """Load JSON data from storage."""
        content = None
        if self.storage_mode == "gcs":
            content = self._load_gcs(file_path)
        else:
            content = self._load_local(file_path)
        
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from {file_path}: {e}")
                return None
        return None

    def _save_local(self, content: str, file_path: str):
        """Save to local filesystem."""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.debug(f"Saved to local: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save locally to {file_path}: {e}")

    def _load_local(self, file_path: str) -> Optional[str]:
        """Load from local filesystem."""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.debug(f"File not found locally: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load locally from {file_path}: {e}")
            return None

    def _save_gcs(self, content: str, file_path: str):
        """Save to Google Cloud Storage."""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(file_path)
            blob.upload_from_string(content, content_type="application/json")
            logger.debug(f"Saved to GCS: gs://{self.bucket_name}/{file_path}")
        except Exception as e:
            logger.error(f"Failed to save to GCS at {file_path}: {e}")

    def _load_gcs(self, file_path: str) -> Optional[str]:
        """Load from Google Cloud Storage."""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(file_path)
            if blob.exists():
                return blob.download_as_text()
            else:
                logger.debug(f"File not found in GCS: gs://{self.bucket_name}/{file_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load from GCS at {file_path}: {e}")
            return None
