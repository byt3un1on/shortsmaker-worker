from datetime import datetime
from uuid import uuid4

import pytest

from adapter.repositories.postgres_ticket_repository import \
    PostgresTicketRepository
from core.application.use_cases.process_script_step import \
    ProcessScriptStepUseCase
from core.domain.enums.ticket_status import TicketStatus
from core.domain.ticket_attribute import TicketAttributeKeys, TicketSteps
from infra.database.models import TicketModel


@pytest.mark.asyncio
async def test_complete_script_processing_workflow(session, mock_llm_service):
    # 1. Prepare Ticket in DB
    ticket_id = uuid4()
    ticket_db = TicketModel(
        id=ticket_id,
        status=TicketStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(ticket_db)
    await session.commit()

    repo = PostgresTicketRepository(session)
    await repo.save_attributes(
        ticket_id,
        {TicketAttributeKeys.PROMPT: "Social media video about Python testing"},
    )

    # 2. Setup Use Case with Mocks
    use_case = ProcessScriptStepUseCase(repo, mock_llm_service)

    # Simulate the worker picking up the ticket
    ticket = await repo.pick_pending_ticket()
    assert ticket is not None
    assert ticket.id == ticket_id

    # 3. Execute
    await use_case.execute(ticket)

    # 4. Verify Final State
    # Check status moved to PENDING (for next step)
    await session.refresh(ticket_db)
    assert ticket_db.status == TicketStatus.PENDING

    # Check attributes
    attrs = await repo.load_attributes(ticket_id)
    assert TicketAttributeKeys.SCRIPT in attrs
    assert attrs[TicketAttributeKeys.STEP] == TicketSteps.AUDIO
