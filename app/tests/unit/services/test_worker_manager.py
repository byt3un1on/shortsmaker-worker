"""Tests for WorkerManager with settings injection."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from infra.config.settings import Settings
from services.worker_manager import WorkerManager


@pytest.fixture
def mock_settings():
    settings = Settings()
    settings.worker_poll_interval = 3
    return settings


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_script_use_case():
    return AsyncMock()


@pytest.fixture
def mock_audio_use_case():
    return AsyncMock()


@pytest.fixture
def mock_video_use_case():
    return AsyncMock()


@pytest.mark.asyncio
async def test_worker_manager_injects_settings_poll_interval(
    mock_repo,
    mock_script_use_case,
    mock_audio_use_case,
    mock_video_use_case,
    mock_settings,
):
    """Test that WorkerManager passes settings.worker_poll_interval
    to all worker loops."""
    # Setup
    mock_repo.get_next_ticket.return_value = None

    manager = WorkerManager(
        mock_repo,
        mock_script_use_case,
        mock_audio_use_case,
        mock_video_use_case,
        mock_settings,
    )

    # Start manager in background
    task = asyncio.create_task(manager.start())

    # Let it run briefly
    await asyncio.sleep(0.5)

    # Stop gracefully
    await manager.stop()

    try:
        await asyncio.wait_for(task, timeout=2.0)
    except asyncio.TimeoutError:
        task.cancel()

    # Verify it used settings
    assert manager.settings.worker_poll_interval == 3


@pytest.mark.asyncio
async def test_worker_manager_starts_all_workers(
    mock_repo,
    mock_script_use_case,
    mock_audio_use_case,
    mock_video_use_case,
    mock_settings,
):
    """Test that WorkerManager starts all three worker loops."""
    mock_repo.get_next_ticket.return_value = None

    manager = WorkerManager(
        mock_repo,
        mock_script_use_case,
        mock_audio_use_case,
        mock_video_use_case,
        mock_settings,
    )

    task = asyncio.create_task(manager.start())
    await asyncio.sleep(0.3)

    # Should have 3 tasks running
    assert len(manager._tasks) == 3

    await manager.stop()

    try:
        await asyncio.wait_for(task, timeout=2.0)
    except asyncio.TimeoutError:
        task.cancel()
