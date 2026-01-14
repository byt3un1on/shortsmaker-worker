from datetime import datetime
from uuid import uuid4

from core.domain.enums.ticket_status import TicketStatus
from core.domain.ticket import Ticket


def test_ticket_creation():
    id = uuid4()
    now = datetime.now()
    ticket = Ticket(id=id, status=TicketStatus.PENDING, created_at=now, updated_at=now)
    assert ticket.id == id
    assert ticket.status == TicketStatus.PENDING


def test_ticket_is_processable():
    now = datetime.now()
    ticket = Ticket(uuid4(), TicketStatus.PENDING, now, now)
    assert ticket.is_processable() is True

    ticket_completed = Ticket(uuid4(), TicketStatus.COMPLETED, now, now)
    assert ticket_completed.is_processable() is False

    ticket_failed = Ticket(uuid4(), TicketStatus.FAILED, now, now)
    assert ticket_failed.is_processable() is False
