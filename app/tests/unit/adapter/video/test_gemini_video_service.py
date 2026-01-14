"""Unit tests for GeminiVideoService."""

from unittest.mock import patch

import pytest

from adapter.video.gemini_video_service import GeminiVideoService


class TestGeminiVideoService:
    """Test cases for GeminiVideoService."""

    @patch("vertexai.init")
    def test_init_success(self, mock_vertexai_init):
        """Test successful initialization."""
        service = GeminiVideoService(
            project_id="test-project",
            location="us-central1",
            model="veo-003",
            timeout=600,
        )

        assert service.project_id == "test-project"
        assert service.location == "us-central1"
        assert service.model == "veo-003"
        assert service.timeout == 600

        mock_vertexai_init.assert_called_once_with(
            project="test-project", location="us-central1"
        )

    @patch("vertexai.init")
    def test_init_vertexai_failure(self, mock_vertexai_init):
        """Test initialization failure when VertexAI fails."""
        mock_vertexai_init.side_effect = Exception("VertexAI error")

        with pytest.raises(RuntimeError, match="VertexAI initialization failed"):
            GeminiVideoService(project_id="test-project")

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_generate_video_with_duration(self, mock_vertexai_init):
        """Test video generation with explicit duration."""
        service = GeminiVideoService(project_id="test-project")

        with patch.object(service, "_generate_placeholder_video") as mock_generate:
            mock_generate.return_value = b"fake_video_data"

            result = await service.generate_video(
                script="Test script",
                audio_url="http://example.com/audio.mp3",
                theme="test theme",
                duration_seconds=45,
            )

            mock_generate.assert_called_once_with("Test script", "test theme", 45)
            assert result == b"fake_video_data"

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_generate_video_without_duration(self, mock_vertexai_init):
        """Test video generation with default duration."""
        service = GeminiVideoService(project_id="test-project")

        with patch.object(service, "_generate_placeholder_video") as mock_generate:
            mock_generate.return_value = b"fake_video_data"

            result = await service.generate_video(
                script="Test script",
                audio_url="http://example.com/audio.mp3",
                theme="test theme",
            )

            mock_generate.assert_called_once_with("Test script", "test theme", 30)
            assert result == b"fake_video_data"

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_generate_video_duration_clamp_min(self, mock_vertexai_init):
        """Test duration clamping to minimum."""
        service = GeminiVideoService(project_id="test-project")

        with patch.object(service, "_generate_placeholder_video") as mock_generate:
            mock_generate.return_value = b"fake_video_data"

            result = await service.generate_video(
                script="Test script",
                audio_url="http://example.com/audio.mp3",
                theme="test theme",
                duration_seconds=2,  # Below minimum
            )

            mock_generate.assert_called_once_with("Test script", "test theme", 5)
            assert result == b"fake_video_data"

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_generate_video_duration_clamp_max(self, mock_vertexai_init):
        """Test duration clamping to maximum."""
        service = GeminiVideoService(project_id="test-project")

        with patch.object(service, "_generate_placeholder_video") as mock_generate:
            mock_generate.return_value = b"fake_video_data"

            result = await service.generate_video(
                script="Test script",
                audio_url="http://example.com/audio.mp3",
                theme="test theme",
                duration_seconds=120,  # Above maximum
            )

            mock_generate.assert_called_once_with("Test script", "test theme", 60)
            assert result == b"fake_video_data"

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_check_generation_status(self, mock_vertexai_init):
        """Test generation status check."""
        service = GeminiVideoService(project_id="test-project")

        result = await service.check_generation_status("job-123")

        assert result["status"] == "SUCCEEDED"
        assert result["progress"] == 100
        assert result["output_url"] == "vertexai://test-project/placeholder/job-123"
        assert "completed_at" in result

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_generate_from_image_with_duration(self, mock_vertexai_init):
        """Test image-to-video generation with explicit duration."""
        service = GeminiVideoService(project_id="test-project")

        result = await service.generate_from_image(
            image_data=b"fake_image_data", prompt="A beautiful sunset", duration=45
        )

        assert result.startswith("veo-image-")
        assert len(result) > len("veo-image-")

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_generate_from_image_without_duration(self, mock_vertexai_init):
        """Test image-to-video generation with default duration."""
        service = GeminiVideoService(project_id="test-project")

        result = await service.generate_from_image(
            image_data=b"fake_image_data", prompt="A beautiful sunset"
        )

        assert result.startswith("veo-image-")

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_generate_from_image_duration_clamp(self, mock_vertexai_init):
        """Test image-to-video duration clamping."""
        service = GeminiVideoService(project_id="test-project")

        # Test minimum clamp
        result = await service.generate_from_image(
            image_data=b"fake_image_data", prompt="A beautiful sunset", duration=2
        )
        assert result.startswith("veo-image-")

        # Test maximum clamp
        result = await service.generate_from_image(
            image_data=b"fake_image_data", prompt="A beautiful sunset", duration=120
        )
        assert result.startswith("veo-image-")

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_get_provider_name(self, mock_vertexai_init):
        """Test provider name retrieval."""
        service = GeminiVideoService(project_id="test-project")

        result = await service.get_provider_name()
        assert result == "gemini-veo"

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_extract_subtitles(self, mock_vertexai_init):
        """Test subtitle extraction."""
        service = GeminiVideoService(project_id="test-project")

        result = await service.extract_subtitles(b"fake_video_data")

        assert "WEBVTT" in result
        assert "[Video content generated by Gemini Veo]" in result
        assert "00:00:00.000 --> 00:00:05.000" in result

    @patch("vertexai.init")
    @pytest.mark.asyncio
    async def test_extract_subtitles_failure(self, mock_vertexai_init):
        """Test subtitle extraction failure."""
        service = GeminiVideoService(project_id="test-project")

        # Mock logger to raise exception
        with patch("adapter.video.gemini_video_service.logger") as mock_logger:
            mock_logger.info.side_effect = Exception("Logger error")

            with pytest.raises(Exception, match="Failed to extract subtitles"):
                await service.extract_subtitles(b"fake_video_data")

    @patch("vertexai.init")
    def test_generate_placeholder_video(self, mock_vertexai_init):
        """Test placeholder video generation."""
        service = GeminiVideoService(project_id="test-project")

        result = service._generate_placeholder_video(
            script="Test script content", theme="test theme", duration=30
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Should contain MP4 header
        assert result.startswith(b"\x00\x00\x00\x20ftypmp41")
