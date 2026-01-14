"""Unit tests for MinIOStorageService."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from minio.datatypes import Object as MinioObject
from minio.error import S3Error

from adapter.storage.minio_storage_service import MinIOStorageService


class TestMinIOStorageService:
    """Test cases for MinIOStorageService."""

    @patch("adapter.storage.minio_storage_service.Minio")
    def test_init_success(self, mock_minio_class):
        """Test successful initialization."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
            secure=False,
            region="us-east-1",
        )

        assert service.endpoint == "localhost:9000"
        assert service.access_key == "test_key"
        assert service.secret_key == "test_secret"
        assert service.bucket == "test-bucket"
        assert service.secure is False
        assert service.region == "us-east-1"
        assert service.client == mock_client

        mock_minio_class.assert_called_once_with(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            secure=False,
            region="us-east-1",
        )
        mock_client.bucket_exists.assert_called_once_with("test-bucket")
        mock_client.make_bucket.assert_not_called()

    @patch("adapter.storage.minio_storage_service.Minio")
    def test_init_create_bucket(self, mock_minio_class):
        """Test initialization creates bucket if it doesn't exist."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = False

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        assert service.bucket == "test-bucket"
        mock_client.make_bucket.assert_called_once_with("test-bucket")

    @patch("adapter.storage.minio_storage_service.Minio")
    def test_init_minio_failure(self, mock_minio_class):
        """Test initialization failure."""
        mock_minio_class.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            MinIOStorageService(
                endpoint="localhost:9000",
                access_key="test_key",
                secret_key="test_secret",
            )

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_upload_file_success(self, mock_minio_class):
        """Test successful file upload."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
            secure=False,
        )

        file_data = b"test file content"
        file_path = "videos/test.mp4"

        result = await service.upload_file(file_data, file_path, "video/mp4")

        assert result == "http://localhost:9000/test-bucket/videos/test.mp4"
        # Verify _upload_file_sync was called via run_in_executor
        assert mock_client.put_object.called

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_upload_file_https(self, mock_minio_class):
        """Test file upload with HTTPS."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        service = MinIOStorageService(
            endpoint="minio.example.com",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
            secure=True,
        )

        file_data = b"test file content"
        file_path = "videos/test.mp4"

        result = await service.upload_file(file_data, file_path)

        assert result == "https://minio.example.com/test-bucket/videos/test.mp4"

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_download_file_success(self, mock_minio_class):
        """Test successful file download."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Mock the response from get_object
        mock_response = MagicMock()
        mock_response.read.return_value = b"downloaded content"
        mock_client.get_object.return_value = mock_response

        service = MinIOStorageService(
            endpoint="localhost:9000", access_key="test_key", secret_key="test_secret"
        )

        result = await service.download_file("videos/test.mp4")

        assert result == b"downloaded content"
        mock_client.get_object.assert_called_once_with("videos", "videos/test.mp4")

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_download_file_not_found(self, mock_minio_class):
        """Test file download when file doesn't exist."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        mock_client.get_object.side_effect = S3Error(
            code="NoSuchKey",
            message="The specified key does not exist",
            resource="videos/test.mp4",
            request_id="test",
            host_id="test",
            response=MagicMock(),
        )

        service = MinIOStorageService(
            endpoint="localhost:9000", access_key="test_key", secret_key="test_secret"
        )

        with pytest.raises(FileNotFoundError, match="File not found"):
            await service.download_file("videos/test.mp4")

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_delete_file_success(self, mock_minio_class):
        """Test successful file deletion."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        await service.delete_file("videos/test.mp4")

        mock_client.remove_object.assert_called_once_with(
            "test-bucket", "videos/test.mp4"
        )

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_file_exists_true(self, mock_minio_class):
        """Test file exists check returns True."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Mock stat_object to succeed
        mock_client.stat_object.return_value = MagicMock()

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        result = await service.file_exists("videos/test.mp4")

        assert result is True
        mock_client.stat_object.assert_called_once_with(
            "test-bucket", "videos/test.mp4"
        )

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_file_exists_false(self, mock_minio_class):
        """Test file exists check returns False."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Mock stat_object to raise S3Error
        mock_client.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="The specified key does not exist",
            resource="videos/test.mp4",
            request_id="test",
            host_id="test",
            response=MagicMock(),
        )

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        result = await service.file_exists("videos/test.mp4")

        assert result is False

    @patch("adapter.storage.minio_storage_service.Minio")
    def test_generate_file_path(self, mock_minio_class):
        """Test file path generation."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        service = MinIOStorageService(
            endpoint="localhost:9000", access_key="test_key", secret_key="test_secret"
        )

        result = service.generate_file_path("ticket-123", "video", "mp4")

        assert result.startswith("tickets/ticket-123/")
        assert result.endswith(".mp4")

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, mock_minio_class):
        """Test cleanup of old files."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Create mock objects with different modification dates
        now = datetime.now(timezone.utc)
        old_obj = MinioObject(
            bucket_name="test-bucket",
            object_name="old-file.mp4",
            last_modified=now - timedelta(days=10),
            etag="etag1",
            size=1000,
            content_type="video/mp4",
            storage_class="STANDARD",
            version_id=None,
            metadata=None,
            owner_id=None,
            owner_name=None,
        )
        new_obj = MinioObject(
            bucket_name="test-bucket",
            object_name="new-file.mp4",
            last_modified=now - timedelta(days=1),
            etag="etag2",
            size=1000,
            content_type="video/mp4",
            storage_class="STANDARD",
            version_id=None,
            metadata=None,
            owner_id=None,
            owner_name=None,
        )

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        with patch.object(
            service, "_list_all_objects", return_value=[old_obj, new_obj]
        ):
            result = await service.cleanup_old_files(
                7
            )  # Delete files older than 7 days

            assert result == 1  # One file should be deleted
            mock_client.remove_object.assert_called_once_with(
                "test-bucket", "old-file.mp4"
            )

    @patch("adapter.storage.minio_storage_service.Minio")
    @pytest.mark.asyncio
    async def test_cleanup_old_files_no_last_modified(self, mock_minio_class):
        """Test cleanup when object has no last_modified date."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Create mock object with None last_modified
        obj_no_date = MinioObject(
            bucket_name="test-bucket",
            object_name="file-no-date.mp4",
            last_modified=None,  # No modification date
            etag="etag1",
            size=1000,
            content_type="video/mp4",
            storage_class="STANDARD",
            version_id=None,
            metadata=None,
            owner_id=None,
            owner_name=None,
        )

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        with patch.object(service, "_list_all_objects", return_value=[obj_no_date]):
            result = await service.cleanup_old_files(7)

            assert result == 0  # No files should be deleted
            mock_client.remove_object.assert_not_called()

    @patch("adapter.storage.minio_storage_service.Minio")
    def test_upload_file_sync(self, mock_minio_class):
        """Test synchronous file upload."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        file_data = b"test content"
        file_path = "test/file.txt"

        service._upload_file_sync(file_data, file_path, "text/plain")

        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args[1]["bucket_name"] == "test-bucket"
        assert call_args[1]["object_name"] == file_path
        assert call_args[1]["data"].getvalue() == file_data
        assert call_args[1]["length"] == len(file_data)
        assert call_args[1]["content_type"] == "text/plain"

    @patch("adapter.storage.minio_storage_service.Minio")
    def test_list_all_objects(self, mock_minio_class):
        """Test listing all objects in bucket."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Mock list_objects
        mock_objects = [MagicMock(), MagicMock()]
        mock_client.list_objects.return_value = mock_objects

        service = MinIOStorageService(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        result = service._list_all_objects()

        assert result == mock_objects
        mock_client.list_objects.assert_called_once_with("test-bucket", recursive=True)
