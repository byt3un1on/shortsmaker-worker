"""Manager for running multiple worker loops concurrently."""

import asyncio
from typing import List

from core.application.use_cases.process_audio_step import \
    ProcessAudioStepUseCase
from core.application.use_cases.process_script_step import \
    ProcessScriptStepUseCase
from core.application.use_cases.process_video_step import \
    ProcessVideoStepUseCase
from core.interfaces.infra.config.i_config import IConfig
from core.interfaces.repositories.i_ticket_repository import ITicketRepository
from infra.logging.logger import get_logger
from services.worker_loop import (audio_worker_loop, script_worker_loop,
                                  video_worker_loop)

logger = get_logger(__name__)


class WorkerManager:
    """Manages the lifecycle of multiple background worker loops."""

    def __init__(
        self,
        ticket_repository: ITicketRepository,
        process_script_use_case: ProcessScriptStepUseCase,
        process_audio_use_case: ProcessAudioStepUseCase,
        process_video_use_case: ProcessVideoStepUseCase,
        settings: IConfig,
    ):
        self.ticket_repository = ticket_repository
        self.process_script_use_case = process_script_use_case
        self.process_audio_use_case = process_audio_use_case
        self.process_video_use_case = process_video_use_case
        self.settings = settings
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Starts all worker loops as concurrent tasks."""
        logger.info(
            f"Starting Worker Manager with poll interval: "
            f"{self.settings.worker_poll_interval}s"
        )

        # Create tasks for each worker loop
        self._tasks.append(
            asyncio.create_task(
                script_worker_loop(
                    self.ticket_repository,
                    self.process_script_use_case,
                    poll_interval=self.settings.worker_poll_interval,
                    shutdown_event=self._shutdown_event,
                ),
                name="script_worker",
            )
        )

        self._tasks.append(
            asyncio.create_task(
                audio_worker_loop(
                    self.ticket_repository,
                    self.process_audio_use_case,
                    poll_interval=self.settings.worker_poll_interval,
                    shutdown_event=self._shutdown_event,
                ),
                name="audio_worker",
            )
        )

        self._tasks.append(
            asyncio.create_task(
                video_worker_loop(
                    self.ticket_repository,
                    self.process_video_use_case,
                    poll_interval=self.settings.worker_poll_interval,
                    shutdown_event=self._shutdown_event,
                ),
                name="video_worker",
            )
        )

        # Wait for all tasks to complete (they only stop on shutdown or error)
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self) -> None:
        """Gracefully stops all running worker loops."""
        logger.info("Shutting down Worker Manager...")
        self._shutdown_event.set()

        # Give tasks a moment to catch the event
        if self._tasks:
            # Wait a bit for tasks to exit gracefully
            await asyncio.sleep(1)
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks = []

        logger.info("Worker Manager stopped")
