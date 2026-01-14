"""Supabase Storage Service implementation."""

from typing import Optional

from supabase import Client, create_client

from core.interfaces.services.i_storage_service import IStorageService
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class SupabaseStorageService(IStorageService):
    """
    Implementation of IStorageService using Supabase Storage.
    """

    def __init__(
        self, supabase_url: str, supabase_key: str, bucket: str = "shortsmaker"
    ):
        self.url = supabase_url
        self.key = supabase_key
        self.bucket_name = bucket
        self.client: Client = create_client(self.url, self.key)

        logger.info(f"SupabaseStorageService initialized (bucket: {bucket})")

    async def upload_file(
        self, file_data: bytes, file_path: str, content_type: Optional[str] = None
    ) -> str:
        logger.info(f"Uploading file to Supabase: {file_path}")
        try:
            # Supabase Python SDK upload is synchronous in its current version (v2)
            # but we wrap it for consistency.
            self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_data,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "upsert": "true",
                },
            )

            # Get public URL
            res = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return res
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {e}")
            raise

    async def download_file(self, file_path: str) -> bytes:
        logger.info(f"Downloading file from Supabase: {file_path}")
        try:
            res = self.client.storage.from_(self.bucket_name).download(file_path)
            return res
        except Exception as e:
            logger.error(f"Error downloading from Supabase: {e}")
            raise

    async def delete_file(self, file_path: str) -> None:
        logger.info(f"Deleting file from Supabase: {file_path}")
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
        except Exception as e:
            logger.error(f"Error deleting from Supabase: {e}")
            raise

    async def file_exists(self, file_path: str) -> bool:
        logger.info(f"Checking if file exists in Supabase: {file_path}")
        try:
            # list() can be used to check existence
            path_parts = file_path.rsplit("/", 1)
            folder = path_parts[0] if len(path_parts) > 1 else ""
            filename = path_parts[-1]

            files = self.client.storage.from_(self.bucket_name).list(folder)
            return any(f["name"] == filename for f in files)
        except Exception:
            return False

    def generate_file_path(self, ticket_id: str, file_type: str, extension: str) -> str:
        return f"tickets/{ticket_id}/{file_type}.{extension}"

    async def cleanup_old_files(self, days: int) -> int:
        # Supabase doesn't easily expose 'LastModified' in the list API for batch
        # cleanup through the basic SDK. This would typically be handled via
        # Supabase Edge Functions or database triggers on bucket objects.
        logger.warn("cleanup_old_files not fully implemented for Supabase adapter")
        return 0
