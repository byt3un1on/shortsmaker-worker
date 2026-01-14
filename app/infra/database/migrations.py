import os

from alembic import command
from alembic.config import Config

from infra.logging.logger import get_logger

logger = get_logger(__name__)


def run_migrations():
    """Run alembic migrations programmatically."""
    logger.info("Running database migrations...")
    try:
        # Get the path to alembic.ini (it's in the root of the project)
        # Assuming the worker runs from the root
        ini_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../alembic.ini")
        )

        if not os.path.exists(ini_path):
            logger.error(f"alembic.ini not found at {ini_path}")
            return False

        alembic_cfg = Config(ini_path)
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        logger.info("✓ Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to run database migrations: {e}")
        return False
