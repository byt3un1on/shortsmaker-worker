"""Image generation service interface."""

from abc import ABC, abstractmethod
from typing import Optional


class IImageService(ABC):
    """
    Interface for image generation services.

    Implementations can use different providers:
    - OpenAI DALL-E
    - Google Gemini Imagen
    - Stability AI
    - Replicate
    """

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        style: Optional[str] = None,
    ) -> bytes:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the desired image.
            size: Image size (e.g., "1024x1024", "16:9").
            quality: Image quality level.
            style: Style preset (e.g., "vivid", "natural", "cinematic").

        Returns:
            Image data as bytes.

        Raises:
            Exception: If image generation fails.
        """
        pass

    @abstractmethod
    async def get_provider_name(self) -> str:
        """
        Get the name of the provider being used.

        Returns:
            Provider name (e.g., "openai", "gemini", "stability").
        """
        pass
