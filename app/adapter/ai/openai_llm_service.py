"""OpenAI LLM Service implementation."""

import json
from typing import Any, Dict, List, Optional, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from core.interfaces.services.i_llm_service import ILLMService
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class OpenAILLMService(ILLMService):
    """
    Implementation of ILLMService using OpenAI API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

        logger.info("OpenAILLMService initialized", model=model)

    async def generate_script(self, prompt: str) -> Dict[str, Any]:
        """Generates a video script in JSON format."""
        logger.info("Generating script with OpenAI")

        system_instruction = (
            "You are a professional video script writer. Output MUST be valid JSON "
            "with 'title', 'hook', 'body', and 'call_to_action' fields."
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=cast(
                    List[ChatCompletionMessageParam],
                    [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                ),
                response_format={"type": "json_object"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned empty content")
            return json.loads(content)
        except Exception as e:
            logger.error("Error generating script with OpenAI", error=str(e))
            raise

    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate text from prompt using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=cast(List[ChatCompletionMessageParam], messages),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned empty content")
            return content
        except Exception as e:
            logger.error("Error generating text with OpenAI", error=str(e))
            raise

    async def generate_image_prompts(self, script: Dict[str, Any]) -> List[str]:
        """Generates image prompts based on a script."""
        prompt_text = (
            f"Based on this script: {json.dumps(script)}, generate 5 descriptive "
            "visual prompts for AI. Return only JSON list 'prompts'."
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=cast(
                    List[ChatCompletionMessageParam],
                    [
                        {
                            "role": "system",
                            "content": "You are a visual director. Output JSON only.",
                        },
                        {"role": "user", "content": prompt_text},
                    ],
                ),
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned empty content")
            data = json.loads(content)
            return data.get("prompts", [])
        except Exception as e:
            logger.error("Error generating image prompts with OpenAI", error=str(e))
            raise
