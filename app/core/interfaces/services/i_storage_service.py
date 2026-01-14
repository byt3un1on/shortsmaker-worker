"""Storage service interface for file persistence."""

from abc import ABC, abstractmethod
from typing import Optional


class IStorageService(ABC):
    """
    Interface for object storage service.

    This service is responsible for persisting generated assets
    (audio, video, VTT files) to cloud storage (S3, GCS, etc.).
    """

    @abstractmethod
    async def upload_file(
        self, file_data: bytes, file_path: str, content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to object storage.

        Args:
            file_data: The file content as bytes.
            file_path: The destination path/key in the bucket.
            content_type: MIME type of the file (e.g., 'video/mp4').

        Returns:
            The public URL or path to the uploaded file.

        Raises:
            Exception: If upload fails.
        """
        pass

    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from object storage.

        Args:
            file_path: The path/key of the file in the bucket.

        Returns:
            The file content as bytes.

        Raises:
            Exception: If download fails or file doesn't exist.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """
        Delete a file from object storage.

        Args:
            file_path: The path/key of the file to delete.

        Raises:
            Exception: If deletion fails.
        """
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_path: The path/key to check.

        Returns:
            True if the file exists, False otherwise.
        """
        pass

    @abstractmethod
    def generate_file_path(self, ticket_id: str, file_type: str, extension: str) -> str:
        """
        Generate a standardized file path for storage.

        Args:
            ticket_id: The ticket UUID.
            file_type: Type of file (e.g., 'audio', 'video', 'vtt').
            extension: File extension (e.g., 'mp3', 'mp4', 'vtt').

        Returns:
            A standardized path like 'tickets/{ticket_id}/{file_type}.{extension}'.
        """
        pass

    @abstractmethod
    async def cleanup_old_files(self, days: int) -> int:
        """
        Delete files older than specified days.

        Args:
            days: Retention period.

        Returns:
            Number of deleted files.
        """
        pass
