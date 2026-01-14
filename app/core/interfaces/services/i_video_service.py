"""Video service interface for video generation."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IVideoService(ABC):
    """
    Interface for video generation service.

    This service is responsible for generating video content,
    potentially using AI video generation services.

    Implementations can use different providers:
    - Google Gemini Veo
    - Stability AI Video
    - Replicate models
    """

    @abstractmethod
    async def generate_video(
        self,
        script: str,
        audio_url: str,
        theme: str,
        duration_seconds: Optional[int] = None,
    ) -> bytes:
        """
        Generate a video based on script, audio, and theme.

        The video generation may involve:
        - AI video generation (Gemini Veo, Synthesia, etc.)
        - Combining stock footage
        - Text-to-video models

        Args:
            script: The script content for the video.
            audio_url: URL to the background audio/music.
            theme: The theme/style for the video.
            duration_seconds: Target duration in seconds.

        Returns:
            The video file content as bytes (e.g., MP4 format).

        Raises:
            Exception: If video generation fails.
        """
        pass

    @abstractmethod
    async def check_generation_status(self, job_id: str) -> dict[str, Any]:
        """
        Check the status of an async video generation job.

        Some video generation services work asynchronously,
        requiring polling for completion.

        Args:
            job_id: The ID of the video generation job.

        Returns:
            Dictionary with status information (status, progress, etc.).
        """
        pass

    @abstractmethod
    async def generate_from_image(
        self, image_data: bytes, prompt: str, duration: Optional[int] = None
    ) -> str:
        """
        Generate video from an image + prompt (image-to-video).

        Args:
            image_data: The input image as bytes.
            prompt: Text prompt for video generation.
            duration: Video duration in seconds.

        Returns:
            Video generation task ID.

        Raises:
            Exception: If video generation fails.
        """
        pass

    @abstractmethod
    async def get_provider_name(self) -> str:
        """
        Get the name of the video provider being used.

        Returns:
            Provider name (e.g., "gemini", "stability").
        """
        pass

    @abstractmethod
    async def extract_subtitles(self, video_data: bytes) -> str:
        """
        Extract or generate VTT subtitles from video.

        This may involve:
        - Speech-to-text from audio track
        - Using embedded subtitle data
        - Generating subtitles from the script with timing

        Args:
            video_data: The video file content as bytes.

        Returns:
            VTT (WebVTT) formatted subtitle content as string.

        Raises:
            Exception: If subtitle extraction fails.
        """
        pass
