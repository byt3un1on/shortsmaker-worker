"""Google Gemini LLM Service implementation."""

import json
from typing import Any, Dict, Optional

import google.generativeai as genai

from core.interfaces.services.i_llm_service import ILLMService
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class GeminiLLMService(ILLMService):
    """
    Implementation of ILLMService using Google Gemini API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        timeout: int = 60,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ):
        self.api_key = api_key
        self.model_name = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature

        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_name)

        logger.info("GeminiLLMService initialized", model=model)

    async def generate_script(self, prompt: str) -> Dict[str, Any]:
        """Generate a video script using Gemini in JSON format."""
        logger.info("Generating script with Gemini")

        system_instruction = (
            "You are a professional video script writer for short social media videos. "
            "Output MUST be valid JSON with 'title', 'hook', 'body', and "
            "'call_to_action' fields. Do not include any Markdown formatting like "
            "```json in the output, just the raw JSON string."
        )

        full_prompt = f"{system_instruction}\n\nPrompt: {prompt}"

        try:
            response = await self.client.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens, temperature=self.temperature
                ),
            )
            # Remove possible markdown markers if LLM adds them
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error calling Gemini API for script: {e}")
            raise

    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate text from prompt using Gemini."""
        logger.info("Generating text with Gemini")

        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            response = await self.client.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens, temperature=self.temperature
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API for text: {e}")
            raise
