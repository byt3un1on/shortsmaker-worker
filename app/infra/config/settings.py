"""
Configurações do Worker.
Carrega de variáveis de ambiente ou arquivo .env
"""

from functools import lru_cache
from typing import Any, Optional

from pydantic_settings import BaseSettings

from core.interfaces.infra.config.i_config import IConfig


class Settings(BaseSettings, IConfig):
    """
    Configurações centralizadas do Worker.
    Implementa IConfig para garantir que todas as partes do sistema usem a
    mesma interface.
    """

    # ================== APP INFO ==================
    app_name: str = "Shortsmaker Worker"
    app_version: str = "1.0.0"
    app_environment: str = "production"

    # ================== DATABASE (PostgreSQL) ==================
    database_url: str = "postgresql+asyncpg://user:password@postgres:5432/shortsmaker"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # ================== LOGGING ==================
    log_level: str = "INFO"
    log_format: str = "json"  # json ou text

    # ================== WORKER ==================
    worker_poll_interval: int = 5  # segundos entre polls
    worker_max_retries: int = 3
    worker_retry_delay: int = 10  # segundos
    worker_shutdown_timeout: int = 30  # segundos para graceful shutdown

    # Storage Cleanup
    storage_retention_days: int = 7
    storage_cleanup_interval_hours: int = 24

    # Número de workers concorrentes por tipo
    script_workers_count: int = 2
    audio_workers_count: int = 2
    video_workers_count: int = 1

    # ================== LLM SERVICES (TEXT GENERATION) ==================
    # Provider para geração de texto/roteiro: openai, gemini
    llm_provider: str = "gemini"
    llm_primary: str = "gemini"  # Used when provider is 'both'

    # OpenAI - Text Generation
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = "http://wiremock:8080"  # Para mocks/testes
    openai_model: str = "gpt-4o"  # Modelo para geração de texto/roteiro
    openai_timeout: int = 60
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7

    # Google Gemini - Text Generation
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash-exp"  # Modelo para geração de texto/roteiro
    gemini_timeout: int = 60
    gemini_max_tokens: int = 4000
    gemini_temperature: float = 0.7

    # ================== IMAGE GENERATION SERVICES ==================
    # Provider para geração de imagens: openai, gemini, stability
    image_provider: str = "openai"

    # OpenAI DALL-E
    openai_model_image: str = "dall-e-3"
    openai_image_size: str = "1024x1024"
    openai_image_quality: str = "standard"

    # Gemini - Image Generation (futuro)
    gemini_model_image: str = "imagen-3.0-generate-001"

    # Stability AI
    stability_api_key: Optional[str] = None
    stability_model: str = "stable-diffusion-xl-1024-v1-0"

    # ================== VIDEO GENERATION SERVICES ==================
    # Provider para geração de vídeo: gemini, stability
    video_provider: str = "gemini"

    # Gemini - Video Generation (Veo)
    gemini_model_video: str = "veo-003"  # Atualizado para Veo 3 conforme solicitado
    gemini_video_timeout: int = 600

    # Stability AI Video
    stability_video_model: str = "stable-video-diffusion-img2vid-xt-1-1"

    # ================== AUDIO/MUSIC SERVICES ==================
    # Provider para áudio/música: placeholder, elevenlabs, openai
    audio_provider: str = "placeholder"

    # ElevenLabs (TTS)
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    elevenlabs_model: str = "eleven_multilingual_v2"

    # OpenAI TTS
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "alloy"

    # ================== STORAGE SERVICES (MinIO / Supabase) ==================
    # Provider: minio, supabase
    storage_provider: str = "minio"

    # MinIO (S3-compatible)
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "shortsmaker"
    minio_secure: bool = False
    minio_region: str = "us-east-1"

    # Supabase Storage
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_bucket: str = "shortsmaker"

    # ================== FEATURE FLAGS ==================
    enable_cache: bool = True
    enable_metrics: bool = False
    enable_tracing: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def validate_required_configs(self):
        """Valida se as chaves de API necessárias estão presentes."""
        errors = []

        # LLM validation
        if self.llm_provider in ["openai", "both"] and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI LLM")
        if self.llm_provider in ["gemini", "both"] and not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required when using Gemini LLM")

        # Audio validation
        if self.audio_provider == "elevenlabs" and not self.elevenlabs_api_key:
            errors.append("ELEVENLABS_API_KEY is required for ElevenLabs audio")

        # Video validation
        if self.video_provider == "gemini" and not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required for Gemini video (Veo)")

        # Storage validation
        if self.storage_provider == "supabase":
            if not self.supabase_url:
                errors.append("SUPABASE_URL is required when using Supabase storage")
            if not self.supabase_key:
                errors.append("SUPABASE_KEY is required when using Supabase storage")

        if errors:
            raise ValueError("\n".join(errors))

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retorna o valor de uma configuração.
        Se não existir, retorna o default.
        """
        return getattr(self, key, default)


@lru_cache()
def get_settings() -> Settings:
    """Helper function to get settings singleton."""
    return Settings()
