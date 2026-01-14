"""Worker loop implementations for ticket processing."""

import asyncio
from typing import Optional

from core.application.use_cases.process_audio_step import \
    ProcessAudioStepUseCase
from core.application.use_cases.process_script_step import \
    ProcessScriptStepUseCase
from core.application.use_cases.process_video_step import \
    ProcessVideoStepUseCase
from core.domain.enums.ticket_status import TicketStatus
from core.domain.ticket_attribute import TicketSteps
from core.interfaces.repositories.i_ticket_repository import ITicketRepository
from infra.logging.logger import get_logger

logger = get_logger(__name__)


async def script_worker_loop(
    ticket_repository: ITicketRepository,
    process_script_use_case: ProcessScriptStepUseCase,
    poll_interval: int,
    shutdown_event: Optional[asyncio.Event] = None,
) -> None:
    """
    Worker loop for processing script generation step.
    """
    logger.info(f"Starting script worker loop (poll interval: {poll_interval}s)")

    while shutdown_event is None or not shutdown_event.is_set():
        try:
            # 1. Fetch next ticket for SCRIPT step
            ticket = await ticket_repository.get_next_ticket(TicketSteps.SCRIPT)

            if ticket is None:
                await asyncio.sleep(poll_interval)
                continue

            logger.info(f"Worker claimed ticket {ticket.id} for script processing")

            # 2. Execute use case
            try:
                await process_script_use_case.execute(ticket)
            except Exception as e:
                error_msg = "Error processing script for ticket {}: {}".format(
                    ticket.id, e
                )
                logger.error(error_msg, exc_info=True)
                # Use case already marks error in DB, but ensure we don't
                # leave ticket in PROCESSING
                try:
                    await ticket_repository.update_status(
                        ticket.id, TicketStatus.PENDING
                    )
                    restore_msg = "Restored ticket {} to PENDING after error".format(
                        ticket.id
                    )
                    logger.info(restore_msg)
                except Exception as restore_error:
                    failed_msg = "Failed to restore ticket {} status: {}".format(
                        ticket.id, restore_error
                    )
                    logger.error(failed_msg)

        except Exception as e:
            logger.error(f"Unexpected error in script worker loop: {e}")
            await asyncio.sleep(poll_interval)

    logger.info("Script worker loop stopped")


async def audio_worker_loop(
    ticket_repository: ITicketRepository,
    process_audio_use_case: ProcessAudioStepUseCase,
    poll_interval: int,
    shutdown_event: Optional[asyncio.Event] = None,
) -> None:
    """
    Worker loop for processing audio generation step.
    """
    logger.info(f"Starting audio worker loop (poll interval: {poll_interval}s)")

    while shutdown_event is None or not shutdown_event.is_set():
        try:
            # 1. Fetch next ticket for AUDIO step
            ticket = await ticket_repository.get_next_ticket(TicketSteps.AUDIO)

            if ticket is None:
                await asyncio.sleep(poll_interval)
                continue

            logger.info(f"Worker claimed ticket {ticket.id} for audio processing")

            # 2. Execute use case
            try:
                await process_audio_use_case.execute(ticket)
            except Exception as e:
                audio_error_msg = "Error processing audio for ticket {}: {}".format(
                    ticket.id, e
                )
                logger.error(audio_error_msg, exc_info=True)
                # Ensure we don't leave ticket in PROCESSING
                try:
                    await ticket_repository.update_status(
                        ticket.id, TicketStatus.PENDING
                    )
                    restore_msg = "Restored ticket {} to PENDING after error".format(
                        ticket.id
                    )
                    logger.info(restore_msg)
                except Exception as restore_error:
                    failed_msg = (
                        f"Failed to restore ticket {ticket.id} status: {restore_error}"
                    )
                    logger.error(failed_msg)

        except Exception as e:
            logger.error("Unexpected error in audio worker loop: {}".format(e))
            await asyncio.sleep(poll_interval)

    logger.info("Audio worker loop stopped")


async def video_worker_loop(
    ticket_repository: ITicketRepository,
    process_video_use_case: ProcessVideoStepUseCase,
    poll_interval: int,
    shutdown_event: Optional[asyncio.Event] = None,
) -> None:
    """
    Worker loop for processing video generation step.
    """
    logger.info(f"Starting video worker loop (poll interval: {poll_interval}s)")

    while shutdown_event is None or not shutdown_event.is_set():
        try:
            # 1. Fetch next ticket for VIDEO step
            ticket = await ticket_repository.get_next_ticket(TicketSteps.VIDEO)

            if ticket is None:
                await asyncio.sleep(poll_interval)
                continue

            logger.info(f"Worker claimed ticket {ticket.id} for video processing")

            # 2. Execute use case
            try:
                await process_video_use_case.execute(ticket)
            except Exception as e:
                video_error_msg = "Error processing video for ticket {}: {}".format(
                    ticket.id, e
                )
                logger.error(video_error_msg, exc_info=True)
                # Ensure we don't leave ticket in PROCESSING
                try:
                    await ticket_repository.update_status(
                        ticket.id, TicketStatus.PENDING
                    )
                    restore_msg = "Restored ticket {} to PENDING after error".format(
                        ticket.id
                    )
                    logger.info(restore_msg)
                except Exception as restore_error:
                    failed_msg = "Failed to restore ticket {} status: {}".format(
                        ticket.id, restore_error
                    )
                    logger.error(failed_msg)

        except Exception as e:
            logger.error("Unexpected error in video worker loop: {}".format(e))
            await asyncio.sleep(poll_interval)

    logger.info("Video worker loop stopped")
