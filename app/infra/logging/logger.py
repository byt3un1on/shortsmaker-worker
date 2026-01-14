import logging

from core.interfaces.infra.tools.i_logger import ILogger


class Logger(ILogger):
    def __init__(self, name: str = "shortsmaker"):
        self.logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message, **kwargs)

    def success(self, message: str, **kwargs) -> None:
        self.logger.info(f"SUCCESS: {message}", **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self.logger.error(message, **kwargs)


def setup_logging() -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def get_logger(name: str = "shortsmaker") -> ILogger:
    """Get a logger instance for a specific module."""
    return Logger(name)
