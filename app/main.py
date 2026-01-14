"""
Shortsmaker Worker - Main entry point.

This is the main entry point for the Worker application that processes
video generation tickets asynchronously using a "Database as a Queue" pattern.
"""

import asyncio
import sys

from infra.config.container import build_container
from infra.config.settings import get_settings
from infra.logging.logger import get_logger, setup_logging

logger = get_logger(__name__)


def validate_configuration():
    """
    Validate all required configuration before starting the worker.
    """
    try:
        settings = get_settings()
        settings.validate_required_configs()
        logger.info("✓ Configuration validated successfully")
        return settings
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed:\n{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during configuration validation: {e}")
        sys.exit(1)


def print_startup_banner(settings):
    """Print a nice startup banner with configuration info."""
    model = (
        settings.gemini_model
        if settings.llm_provider in ["gemini", "both"]
        else settings.openai_model
    )
    bucket = (
        settings.minio_bucket if settings.storage_provider == "minio" else "supabase"
    )
    banner = f"""
╔═══════════════════════════════════════════════════════════════╗
║              🎬 SHORTSMAKER WORKER v{settings.app_version}              ║
╚═══════════════════════════════════════════════════════════════╝

Environment:  {settings.app_environment}
LLM Provider: {settings.llm_provider}
  ├─ Model:   {model}

Storage:      {settings.storage_provider}
  └─ Bucket:  {bucket}

Video:        {settings.video_provider}
Audio:        {settings.audio_provider}

Workers Enabled:
  ├─ Script Worker
  ├─ Audio Worker
  └─ Video Worker

Poll Interval: {settings.worker_poll_interval}s
Log Level:     {settings.log_level}

Starting workers...
"""
    print(banner)


async def run_worker():
    """Run the worker manager."""
    # 1. Setup Logging
    setup_logging()

    # 2. Validate configuration
    settings = validate_configuration()

    # 3. Print startup banner
    print_startup_banner(settings)

    logger.info("Initializing Shortsmaker Worker...")

    # 4. Build dependency injection container
    try:
        container = build_container(settings)
        logger.info("✓ Dependency injection container built")
    except Exception as e:
        logger.error(f"❌ Failed to build container: {e}")
        sys.exit(1)

    # 5. Ensure Schema via Alembic Migrations (No dangerous fallback)
    try:
        from infra.database.migrations import run_migrations

        if not run_migrations():
            logger.error(
                "❌ Database migrations failed. Please run migrations manually."
            )
            logger.error("   Run: alembic upgrade head")
            sys.exit(1)
        logger.info("✓ Database migrations verified")
    except Exception as e:
        logger.error(f"❌ Failed to run database migrations: {e}")
        logger.error(
            "   Ensure PostgreSQL is running and alembic.ini is configured correctly."
        )
        sys.exit(1)

    # 6. Start the worker manager
    worker_manager = container.worker_manager()
    try:
        await worker_manager.start()
    except asyncio.CancelledError:
        logger.info("Shutting down worker manager due to cancellation...")
        await worker_manager.stop()
    except Exception as e:
        logger.error(f"Critical error in worker manager: {e}", exc_info=True)
        await worker_manager.stop()
        raise


def main():
    """Main entry point."""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Application terminated with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
