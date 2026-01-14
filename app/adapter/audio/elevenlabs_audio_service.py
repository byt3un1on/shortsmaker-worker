"""ElevenLabs Audio Service implementation (TTS)."""

from typing import Optional

from elevenlabs.client import AsyncElevenLabs

from core.interfaces.services.i_audio_service import IAudioService
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class ElevenLabsAudioService(IAudioService):
    """
    Implementation of IAudioService using ElevenLabs API.
    """

    def __init__(
        self,
        api_key: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel)
        model_id: str = "eleven_multilingual_v2",
    ):
        """
        Initialize ElevenLabs service.
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id

        self.client = AsyncElevenLabs(api_key=api_key)

        logger.info(
            "ElevenLabsAudioService initialized", voice_id=voice_id, model_id=model_id
        )

    async def generate_audio(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Generate audio from text using ElevenLabs."""
        target_voice = voice_id or self.voice_id
        logger.info("Generating audio with ElevenLabs", voice_id=target_voice)

        try:
            # convert() returns an AsyncIterator of bytes
            # For simplicity in this worker, we'll collect all chunks
            audio_generator = await self.client.text_to_speech.convert(
                voice_id=target_voice,
                text=text,
                model_id=self.model_id,
            )

            audio_data = b""
            async for chunk in audio_generator:
                audio_data += chunk

            return audio_data
        except Exception as e:
            logger.error("Error generating audio with ElevenLabs", error=str(e))
            raise

    async def get_voices(self):
        """Fetch available voices."""
        try:
            response = await self.client.voices.get_all()
            return response.voices
        except Exception as e:
            logger.error("Error fetching voices from ElevenLabs", error=str(e))
            return []
