"""LLM service interface for text generation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ILLMService(ABC):
    """
    Interface for Large Language Model service.
    """

    @abstractmethod
    async def generate_script(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a video script based on a prompt.

        Returns:
            Dict with keys: title, hook, body, call_to_action
        """
        pass

    @abstractmethod
    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """General text generation."""
        pass
