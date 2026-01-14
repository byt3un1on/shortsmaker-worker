from datetime import datetime
from uuid import uuid4

import pytest

from adapter.repositories.postgres_ticket_repository import \
    PostgresTicketRepository
from core.domain.enums.ticket_status import TicketStatus
from infra.database.models import TicketModel


@pytest.mark.asyncio
async def test_save_and_load_attributes(session):
    # Setup
    id = uuid4()
    # Create the base ticket in DB first (simulating API existence)
    ticket_db = TicketModel(
        id=id,
        status=TicketStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(ticket_db)
    await session.commit()

    repo = PostgresTicketRepository(session)

    # Action: Save attributes
    attrs = {"prompt": "Integration test prompt", "step": "SCRIPT"}
    await repo.save_attributes(id, attrs)

    # Action: Load attributes
    loaded_attrs = await repo.load_attributes(id)

    # Assert
    assert loaded_attrs["prompt"] == "Integration test prompt"
    assert loaded_attrs["step"] == "SCRIPT"


@pytest.mark.asyncio
async def test_update_status(session):
    id = uuid4()
    ticket_db = TicketModel(
        id=id,
        status=TicketStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(ticket_db)
    await session.commit()

    repo = PostgresTicketRepository(session)

    # Action
    await repo.update_status(id, TicketStatus.PROCESSING)

    # Assert
    await session.refresh(ticket_db)
    assert ticket_db.status == TicketStatus.PROCESSING


@pytest.mark.asyncio
async def test_pick_pending_ticket_with_lock(session):
    id = uuid4()
    ticket_db = TicketModel(
        id=id,
        status=TicketStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(ticket_db)
    await session.commit()

    repo = PostgresTicketRepository(session)

    # Action: Try to pick it
    ticket = await repo.pick_pending_ticket()

    # Assert
    assert ticket is not None
    assert ticket.id == id

    # Verify it updated to PROCESSING
    await session.refresh(ticket_db)
    assert ticket_db.status == TicketStatus.PROCESSING
