"""MinIO Storage Service implementation (S3-compatible) with real cleanup."""

import asyncio
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

from minio import Minio
from minio.datatypes import Object as MinioObject
from minio.error import S3Error

from core.interfaces.services.i_storage_service import IStorageService
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class MinIOStorageService(IStorageService):
    """
    Implementation of IStorageService using MinIO (S3-compatible) with real cleanup.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str = "videos",
        secure: bool = False,
        region: str = "us-east-1",
    ):
        """
        Initialize MinIO storage service.

        Args:
            endpoint: MinIO server endpoint (e.g., "localhost:9000")
            access_key: MinIO access key
            secret_key: MinIO secret key
            bucket: Default bucket name
            secure: Whether to use HTTPS
            region: AWS region (for S3 compatibility)
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self.region = region

        # Initialize MinIO client
        try:
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                region=region,
            )

            # Ensure bucket exists
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                logger.info(f"Created bucket: {bucket}")

            logger.info(
                f"MinIOStorageService initialized (bucket: {bucket}, "
                f"endpoint: {endpoint})"
            )

        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise

    async def upload_file(
        self, file_data: bytes, file_path: str, content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to MinIO storage.

        Args:
            file_data: The file content as bytes
            file_path: The destination path/key in the bucket
            content_type: MIME type of the file

        Returns:
            The public URL to access the uploaded file

        Raises:
            Exception: If upload fails
        """
        logger.info(f"Uploading file to MinIO: {file_path} ({len(file_data)} bytes)")

        try:
            # Upload file using thread pool executor since minio client is sync
            await asyncio.get_event_loop().run_in_executor(
                None, self._upload_file_sync, file_data, file_path, content_type
            )

            # Generate public URL
            protocol = "https" if self.secure else "http"
            public_url = f"{protocol}://{self.endpoint}/{self.bucket}/{file_path}"

            logger.info(f"File uploaded successfully: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise Exception(f"MinIO upload failed: {str(e)}")

    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from MinIO storage.

        Args:
            file_path: The path/key of the file in the bucket

        Returns:
            The file content as bytes

        Raises:
            Exception: If download fails or file doesn't exist
        """
        logger.info(f"Downloading file from MinIO: {file_path}")

        try:
            # Download file using thread pool executor
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_object, self.bucket, file_path
            )

            # Read all data from response
            file_data = response.read()
            response.close()
            response.release_conn()

            logger.info(
                f"File downloaded successfully: {file_path} ({len(file_data)} bytes)"
            )
            return file_data

        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warn(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")
            else:
                logger.error(f"MinIO download error for {file_path}: {e}")
                raise Exception(f"MinIO download failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            raise Exception(f"MinIO download failed: {str(e)}")

    async def delete_file(self, file_path: str) -> None:
        """
        Delete a file from MinIO storage.

        Args:
            file_path: The path/key of the file to delete

        Raises:
            Exception: If deletion fails
        """
        logger.info(f"Deleting file from MinIO: {file_path}")

        try:
            # Delete file using thread pool executor
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.remove_object, self.bucket, file_path
            )

            logger.info(f"File deleted successfully: {file_path}")

        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warn(f"File not found for deletion: {file_path}")
                # Don't raise error for non-existent files
            else:
                logger.error(f"MinIO delete error for {file_path}: {e}")
                raise Exception(f"MinIO delete failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise Exception(f"MinIO delete failed: {str(e)}")

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in MinIO storage.

        Args:
            file_path: The path/key to check

        Returns:
            True if the file exists, False otherwise
        """
        try:
            # Use stat_object to check existence
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.stat_object, self.bucket, file_path
            )
            return True

        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            else:
                logger.error(f"MinIO stat error for {file_path}: {e}")
                raise Exception(f"MinIO stat failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to check file existence {file_path}: {e}")
            raise Exception(f"MinIO stat failed: {str(e)}")

    def generate_file_path(self, ticket_id: str, file_type: str, extension: str) -> str:
        """
        Generate a standardized file path for storage.

        Args:
            ticket_id: The ticket UUID
            file_type: Type of file (e.g., 'audio', 'video', 'vtt')
            extension: File extension (e.g., 'mp3', 'mp4', 'vtt')

        Returns:
            A standardized path like 'tickets/{ticket_id}/{file_type}.{extension}'
        """
        return f"tickets/{ticket_id}/{file_type}.{extension}"

    async def cleanup_old_files(self, days: int) -> int:
        """
        Delete files older than specified days from MinIO storage.

        This method lists all objects in the bucket, checks their last modified date,
        and deletes files older than the specified retention period.

        Args:
            days: Number of days to retain files (files older than this will be deleted)

        Returns:
            Number of files deleted

        Raises:
            Exception: If cleanup operation fails
        """
        logger.info(
            f"Starting cleanup of files older than {days} days in bucket {self.bucket}"
        )

        try:
            deleted_count = 0
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            # List all objects in the bucket
            objects = await asyncio.get_event_loop().run_in_executor(
                None, self._list_all_objects
            )

            # Check each object's modification date
            for obj in objects:
                if obj.last_modified and obj.last_modified < cutoff_date:
                    try:
                        # Delete the old file
                        await self.delete_file(obj.object_name)
                        deleted_count += 1
                        logger.debug(
                            f"Deleted old file: {obj.object_name} "
                            f"(modified: {obj.last_modified})"
                        )
                    except Exception as e:
                        logger.warn(f"Failed to delete old file {obj.object_name}: {e}")
                        # Continue with other files even if one fails

            logger.info(f"Cleanup completed: {deleted_count} files deleted")
            return deleted_count

        except Exception as e:
            logger.error(f"Cleanup operation failed: {e}")
            raise Exception(f"MinIO cleanup failed: {str(e)}")

    def _upload_file_sync(
        self, file_data: bytes, file_path: str, content_type: Optional[str]
    ) -> None:
        """Synchronous file upload to MinIO."""
        # Convert bytes to file-like object
        file_obj = io.BytesIO(file_data)
        file_size = len(file_data)

        # Upload the file
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=file_path,
            data=file_obj,
            length=file_size,
            content_type=content_type or "application/octet-stream",
        )

    def _list_all_objects(self) -> list[MinioObject]:
        """List all objects in the bucket synchronously."""
        objects = []
        # List objects with pagination
        for obj in self.client.list_objects(self.bucket, recursive=True):
            objects.append(obj)
        return objects
