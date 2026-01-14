from abc import ABC, abstractmethod
from typing import Any, Optional


class IConfig(ABC):
    """
    Interface para o sistema de gerenciamento de configurações.
    Garante que as configurações sejam carregadas com valores padrão
    e permitam sobrescrita via variáveis de ambiente.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retorna o valor de uma configuração pelo seu nome (chave).
        """
        pass

    # ================== APP INFO ==================
    app_name: str
    app_version: str
    app_environment: str

    # ================== DATABASE ==================
    database_url: str

    # ================== LOGGING ==================
    log_level: str

    # ================== WORKER ==================
    worker_poll_interval: int

    # ================== LLM ==================
    llm_provider: str
    gemini_api_key: Optional[str]
    openai_api_key: Optional[str]

    # ================== LLM Details ==================
    gemini_model: str
    gemini_timeout: int
    gemini_max_tokens: int
    gemini_temperature: float
    openai_model: str

    # ================== Audio ==================
    audio_provider: str
    elevenlabs_api_key: Optional[str]
    elevenlabs_voice_id: Optional[str]

    # ================== Storage ==================
    storage_provider: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool
    supabase_url: Optional[str]
    supabase_key: Optional[str]
    supabase_bucket: str

    # ================== Video ==================
    video_provider: str
    gemini_model_video: str

    @abstractmethod
    def validate_required_configs(self) -> None:
        """
        Valida se as configurações obrigatórias estão presentes.
        """
        pass
