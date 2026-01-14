from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapter.ai.gemini_llm_service import GeminiLLMService


@pytest.mark.asyncio
async def test_generate_script_gemini_success():
    # Mocking the google-generativeai client
    with patch("google.generativeai.GenerativeModel") as mock_model_class:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            '{"title": "Gemini Video", "hook": "Awesome hook", '
            '"body": "Great content", "call_to_action": "Subscribe"}'
        )

        # Async mock for generate_content_async
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        service = GeminiLLMService(api_key="fake_key", model="gemini-pro")

        script = await service.generate_script("Generate a video about AI")

        assert script["title"] == "Gemini Video"
        mock_model.generate_content_async.assert_called_once()


@pytest.mark.asyncio
async def test_generate_script_gemini_invalid_json_retry():
    with patch("google.generativeai.GenerativeModel") as mock_model_class:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is not JSON"

        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        service = GeminiLLMService(api_key="fake_key")

        with pytest.raises(Exception):  # Or specific json.JSONDecodeError if not caught
            await service.generate_script("Invalid JSON test")
