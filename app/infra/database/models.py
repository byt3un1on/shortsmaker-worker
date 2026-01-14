from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from core.domain.enums.ticket_status import TicketStatus


class TicketModel(SQLModel, table=True):
    __tablename__ = "ticket"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: TicketStatus = Field(default=TicketStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)

    # Relationships
    attributes: List["TicketAttributeModel"] = Relationship(back_populates="ticket")


class TicketAttributeModel(SQLModel, table=True):
    __tablename__ = "ticketattribute"
    __table_args__ = (
        UniqueConstraint("ticket_id", "key", name="ticketattribute_ticket_id_key_key"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticket_id: UUID = Field(foreign_key="ticket.id")
    key: str = Field(index=True)
    value: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)

    # Relationships
    ticket: TicketModel = Relationship(back_populates="attributes")


async def create_db_and_tables(engine):
    """Ensure database tables exist."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
