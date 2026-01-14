"""Audio service interface for music/audio handling."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IAudioService(ABC):
    """
    Interface for audio service.

    This service is responsible for finding, generating, or collecting
    background music and audio assets for the video.
    """

    @abstractmethod
    async def get_audio_for_theme(
        self, theme: str, duration_seconds: Optional[int] = None
    ) -> bytes:
        """
        Get audio content matching the theme.

        This could involve:
        - Searching a music library
        - Generating audio with AI
        - Using pre-selected stock music

        Args:
            theme: The theme/mood for the audio.
            duration_seconds: Desired duration in seconds, if specific length needed.

        Returns:
            The audio file content as bytes (e.g., MP3 format).

        Raises:
            Exception: If audio retrieval/generation fails.
        """
        pass

    @abstractmethod
    async def get_audio_metadata(self, audio_data: bytes) -> dict[str, Any]:
        """
        Extract metadata from audio data.

        Args:
            audio_data: The audio file content as bytes.

        Returns:
            Dictionary containing metadata like duration, format, bitrate, etc.
        """
        pass
