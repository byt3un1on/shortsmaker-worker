"""Dependency injection container."""

from dependency_injector import containers, providers

from adapter.ai.gemini_llm_service import GeminiLLMService
from adapter.ai.openai_llm_service import OpenAILLMService
from adapter.audio.elevenlabs_audio_service import ElevenLabsAudioService
from adapter.audio.placeholder_audio_service import PlaceholderAudioService
from adapter.repositories.postgres_ticket_repository import \
    PostgresTicketRepository
from adapter.storage.minio_storage_service import MinIOStorageService
from adapter.storage.supabase_storage_service import SupabaseStorageService
from adapter.video.gemini_video_service import GeminiVideoService
from core.application.use_cases.process_audio_step import \
    ProcessAudioStepUseCase
from core.application.use_cases.process_script_step import \
    ProcessScriptStepUseCase
from core.application.use_cases.process_video_step import \
    ProcessVideoStepUseCase
from infra.config.settings import Settings
from infra.database.session import DatabaseSessionManager
from services.worker_manager import WorkerManager


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    settings = providers.Singleton(Settings)

    # Database
    db_manager = providers.Singleton(
        DatabaseSessionManager, db_url=settings.provided.database_url
    )

    # Repositories
    ticket_repository = providers.Factory(
        PostgresTicketRepository, session_factory=db_manager.provided.get_session
    )

    # Services
    llm_service = providers.Selector(
        settings.provided.llm_provider,
        gemini=providers.Factory(
            GeminiLLMService,
            api_key=settings.provided.gemini_api_key,
            model=settings.provided.gemini_model,
            timeout=settings.provided.gemini_timeout,
            max_tokens=settings.provided.gemini_max_tokens,
            temperature=settings.provided.gemini_temperature,
        ),
        openai=providers.Factory(
            OpenAILLMService,
            api_key=settings.provided.openai_api_key,
            model=settings.provided.openai_model,
        ),
    )

    audio_service = providers.Selector(
        settings.provided.audio_provider,
        elevenlabs=providers.Factory(
            ElevenLabsAudioService,
            api_key=settings.provided.elevenlabs_api_key,
            voice_id=settings.provided.elevenlabs_voice_id,
        ),
        placeholder=providers.Factory(PlaceholderAudioService),
    )

    storage_service = providers.Selector(
        settings.provided.storage_provider,
        minio=providers.Factory(
            MinIOStorageService,
            endpoint=settings.provided.minio_endpoint,
            access_key=settings.provided.minio_access_key,
            secret_key=settings.provided.minio_secret_key,
            bucket=settings.provided.minio_bucket,
            secure=settings.provided.minio_secure,
        ),
        supabase=providers.Factory(
            SupabaseStorageService,
            supabase_url=settings.provided.supabase_url,
            supabase_key=settings.provided.supabase_key,
            bucket=settings.provided.supabase_bucket,
        ),
    )

    video_service = providers.Factory(
        GeminiVideoService,
        api_key=settings.provided.gemini_api_key,
        model=settings.provided.gemini_model_video,
    )

    # Use Cases
    process_script_use_case = providers.Factory(
        ProcessScriptStepUseCase,
        ticket_repository=ticket_repository,
        llm_service=llm_service,
    )

    process_audio_use_case = providers.Factory(
        ProcessAudioStepUseCase,
        ticket_repository=ticket_repository,
        audio_service=audio_service,
        storage_service=storage_service,
    )

    process_video_use_case = providers.Factory(
        ProcessVideoStepUseCase,
        ticket_repository=ticket_repository,
        video_service=video_service,
        storage_service=storage_service,
    )

    # Worker Manager
    worker_manager = providers.Factory(
        WorkerManager,
        ticket_repository=ticket_repository,
        process_script_use_case=process_script_use_case,
        process_audio_use_case=process_audio_use_case,
        process_video_use_case=process_video_use_case,
        settings=settings,
    )


def build_container(settings: Settings) -> Container:
    """Helper function to build and wire the container."""
    container = Container()
    container.settings.override(providers.Singleton(lambda: settings))
    return container
