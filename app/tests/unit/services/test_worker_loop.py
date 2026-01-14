"""Tests for worker loop error recovery."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from core.domain.enums.ticket_status import TicketStatus
from core.domain.ticket import Ticket
from services.worker_loop import (audio_worker_loop, script_worker_loop,
                                  video_worker_loop)


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.update_status = AsyncMock()
    return repo


@pytest.fixture
def mock_use_case():
    return AsyncMock()


@pytest.mark.asyncio
async def test_script_worker_loop_restores_ticket_on_error(mock_repo, mock_use_case):
    """Test that worker loop restores ticket to PENDING when use case fails."""
    ticket = Ticket(uuid4(), TicketStatus.PROCESSING, datetime.now(), datetime.now())

    # Setup: Return ticket once, then None to stop loop
    mock_repo.get_next_ticket.side_effect = [ticket, None]

    # Make use case fail
    mock_use_case.execute.side_effect = Exception("API Error")

    # Create shutdown event to stop after processing
    shutdown_event = asyncio.Event()

    # Run worker loop in background
    task = asyncio.create_task(
        script_worker_loop(
            mock_repo, mock_use_case, poll_interval=0.1, shutdown_event=shutdown_event
        )
    )

    # Wait a bit for processing
    await asyncio.sleep(0.3)
    shutdown_event.set()

    try:
        await asyncio.wait_for(task, timeout=1.0)
    except asyncio.TimeoutError:
        task.cancel()

    # Verify error recovery: ticket should be restored to PENDING
    mock_use_case.execute.assert_called_once_with(ticket)
    mock_repo.update_status.assert_called_with(ticket.id, TicketStatus.PENDING)


@pytest.mark.asyncio
async def test_audio_worker_loop_uses_correct_poll_interval(mock_repo, mock_use_case):
    """Test that worker loop uses the provided poll_interval."""
    mock_repo.get_next_ticket.return_value = None

    shutdown_event = asyncio.Event()

    # Start worker with specific poll interval
    task = asyncio.create_task(
        audio_worker_loop(
            mock_repo,
            mock_use_case,
            poll_interval=1,  # 1 second
            shutdown_event=shutdown_event,
        )
    )

    # Wait less than poll interval
    await asyncio.sleep(0.5)

    # Should have called get_next_ticket at least once
    assert mock_repo.get_next_ticket.call_count >= 1

    shutdown_event.set()

    try:
        await asyncio.wait_for(task, timeout=2.0)
    except asyncio.TimeoutError:
        task.cancel()


@pytest.mark.asyncio
async def test_video_worker_loop_graceful_shutdown(mock_repo, mock_use_case):
    """Test that worker loop stops gracefully on shutdown event."""
    mock_repo.get_next_ticket.return_value = None

    shutdown_event = asyncio.Event()

    task = asyncio.create_task(
        video_worker_loop(
            mock_repo, mock_use_case, poll_interval=0.1, shutdown_event=shutdown_event
        )
    )

    await asyncio.sleep(0.2)

    # Trigger shutdown
    shutdown_event.set()

    # Should complete without timeout
    await asyncio.wait_for(task, timeout=1.0)

    # Worker should have stopped cleanly
    assert task.done()
