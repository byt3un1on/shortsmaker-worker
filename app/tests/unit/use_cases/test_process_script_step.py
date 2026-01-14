from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from core.application.use_cases.process_script_step import \
    ProcessScriptStepUseCase
from core.domain.enums.ticket_status import TicketStatus
from core.domain.ticket import Ticket
from core.domain.ticket_attribute import TicketAttributeKeys


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.load_attributes.return_value = {
        TicketAttributeKeys.PROMPT: "Create a video about cats"
    }
    repo.save_attributes = AsyncMock()
    repo.update_status = AsyncMock()
    return repo


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate_script.return_value = {
        "title": "Cat Video",
        "hook": "Look at these cats",
    }
    return llm


@pytest.mark.asyncio
async def test_process_script_step_success(mock_repo, mock_llm):
    ticket = Ticket(uuid4(), TicketStatus.PROCESSING, datetime.now(), datetime.now())
    use_case = ProcessScriptStepUseCase(mock_repo, mock_llm)

    await use_case.execute(ticket)

    # Verify logic
    mock_repo.load_attributes.assert_called_once_with(ticket.id)
    mock_llm.generate_script.assert_called_once_with("Create a video about cats")
    mock_repo.save_attributes.assert_called_once()
    mock_repo.update_status.assert_called_once_with(ticket.id, TicketStatus.PENDING)


@pytest.mark.asyncio
async def test_process_script_step_failure_triggers_retry(mock_repo, mock_llm):
    ticket_id = uuid4()
    now = datetime.now()
    ticket = Ticket(ticket_id, TicketStatus.PROCESSING, now, now)
    mock_llm.generate_script.side_effect = Exception("API Down")

    use_case = ProcessScriptStepUseCase(mock_repo, mock_llm)
    # Mocking internal handle failure to avoid deep testing of retry logic here
    # or testing it fully
    use_case._handle_failure = AsyncMock()

    await use_case.execute(ticket)

    use_case._handle_failure.assert_called_once()
