"""PostgreSQL implementation of ticket repository."""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from core.domain.enums.ticket_status import TicketStatus
from core.domain.ticket import Ticket as DomainTicket
from core.domain.ticket_attribute import TicketAttributeKeys
from core.interfaces.repositories.i_ticket_repository import ITicketRepository
from infra.database.models import TicketAttributeModel as AttributeModel
from infra.database.models import TicketModel
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class PostgresTicketRepository(ITicketRepository):
    """
    PostgreSQL implementation of the ticket repository using SQLModel/SQLAlchemy.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory

    @asynccontextmanager
    async def _get_session(self):
        """Helper to handle both session factory and direct session."""
        if isinstance(self.session_factory, AsyncSession):
            yield self.session_factory
        else:
            async with self.session_factory() as session:
                yield session

    def _to_domain(self, ticket_db: TicketModel) -> DomainTicket:
        """Map database model to domain entity."""
        return DomainTicket(
            id=ticket_db.id,
            status=ticket_db.status,
            created_at=ticket_db.created_at,
            updated_at=ticket_db.updated_at,
            is_deleted=ticket_db.is_deleted,
        )

    async def get_next_ticket(self, step: str) -> Optional[DomainTicket]:
        """
        Get the next available ticket for a specific step.
        Filters by PENDING status, step attribute, and next_retry_at.
        """
        async with self._get_session() as session:
            try:
                # Aliases for multiple joins on the same table
                step_attr = aliased(AttributeModel)
                retry_attr = aliased(AttributeModel)

                now_str = datetime.utcnow().isoformat()

                query = (
                    select(TicketModel)
                    .join(step_attr, TicketModel.id == step_attr.ticket_id)
                    .outerjoin(
                        retry_attr,
                        (TicketModel.id == retry_attr.ticket_id)
                        & (retry_attr.key == TicketAttributeKeys.NEXT_RETRY_AT),
                    )
                    .where(TicketModel.status == TicketStatus.PENDING)
                    .where(step_attr.key == TicketAttributeKeys.STEP)
                    .where(step_attr.value == step)
                    .where(TicketModel.is_deleted.is_(False))
                    .where(or_(retry_attr.value.is_(None), retry_attr.value <= now_str))
                    .order_by(TicketModel.created_at.asc())
                    .limit(1)
                )

                # Only use FOR UPDATE SKIP LOCKED on PostgreSQL
                if session.bind.dialect.name == "postgresql":
                    query = query.with_for_update(skip_locked=True)

                result = await session.execute(query)
                ticket_db = result.scalar_one_or_none()

                if not ticket_db:
                    return None

                # Claim ticket
                ticket_db.status = TicketStatus.PROCESSING
                ticket_db.updated_at = datetime.utcnow()

                await session.commit()
                await session.refresh(ticket_db)

                return self._to_domain(ticket_db)
            except Exception as e:
                await session.rollback()
                logger.error(f"Error claiming ticket for step {step}: {e}")
                raise

    async def load_attributes(self, ticket_id: UUID) -> Dict[str, str]:
        """Load attributes for a ticket."""
        async with self._get_session() as session:
            query = (
                select(AttributeModel)
                .where(AttributeModel.ticket_id == ticket_id)
                .where(AttributeModel.is_deleted.is_(False))
            )
            result = await session.execute(query)
            attributes = result.scalars().all()
            return {attr.key: attr.value for attr in attributes}

    async def save_attributes(self, ticket_id: UUID, attr_dict: Dict[str, str]) -> None:
        """Upsert attributes for a ticket."""
        async with self._get_session() as session:
            try:
                for key, value in attr_dict.items():
                    stmt = insert(AttributeModel).values(
                        id=None,  # Auto-generated or explicit if needed
                        ticket_id=ticket_id,
                        key=key,
                        value=str(value),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )

                    # On conflict update
                    stmt = (
                        stmt.on_conflict_do_update(
                            index_elements=["ticket_id", "key"],
                            set_=dict(value=str(value), updated_at=datetime.utcnow()),
                        )
                        if session.bind.dialect.name == "postgresql"
                        else stmt
                    )

                    # Manual fallback for SQLite/others if needed (simple for now)
                    if session.bind.dialect.name != "postgresql":
                        # Check if exists
                        check = await session.execute(
                            select(AttributeModel).where(
                                AttributeModel.ticket_id == ticket_id,
                                AttributeModel.key == key,
                            )
                        )
                        existing = check.scalar_one_or_none()
                        if existing:
                            existing.value = str(value)
                            existing.updated_at = datetime.utcnow()
                        else:
                            session.add(
                                AttributeModel(
                                    ticket_id=ticket_id, key=key, value=str(value)
                                )
                            )
                    else:
                        await session.execute(stmt)

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving attributes for ticket {ticket_id}: {e}")
                raise

    async def complete_ticket(self, ticket_id: UUID) -> None:
        """Mark ticket as completed."""
        async with self._get_session() as session:
            try:
                ticket = await session.get(TicketModel, ticket_id)
                if ticket:
                    ticket.status = TicketStatus.COMPLETED
                    ticket.updated_at = datetime.utcnow()
                    await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error completing ticket {ticket_id}: {e}")
                raise

    async def fail_ticket(self, ticket_id: UUID, reason: str) -> None:
        """Mark ticket as failed and schedule retry."""
        async with self._get_session() as session:
            try:
                ticket = await session.get(TicketModel, ticket_id)
                if ticket:
                    # Logic for retries could go here
                    ticket.status = TicketStatus.FAILED
                    ticket.updated_at = datetime.utcnow()

                    # Save error reason
                    await self.save_attributes(
                        ticket_id, {TicketAttributeKeys.ERROR: reason}
                    )

                    await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error failing ticket {ticket_id}: {e}")
                raise

    async def _save_attrs_bulk(
        self, ticket_id: UUID, attr_dict: Dict[str, str], session
    ) -> None:
        """Helper to save attributes in a session."""
        for key, value in attr_dict.items():
            stmt = (
                insert(AttributeModel)
                .values(
                    ticket_id=ticket_id,
                    key=key,
                    value=value,
                    created_at=datetime.utcnow(),
                    is_deleted=False,
                )
                .on_conflict_do_update(
                    constraint="ticketattribute_ticket_id_key_key",
                    set_={"value": value, "is_deleted": False},
                )
            )
            await session.execute(stmt)

    async def update_status(self, ticket_id: UUID, new_status: TicketStatus) -> None:
        """Update ticket status."""
        async with self._get_session() as session:
            try:
                stmt = (
                    update(TicketModel)
                    .where(TicketModel.id == ticket_id)
                    .values(status=new_status, updated_at=datetime.utcnow())
                )
                await session.execute(stmt)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating status for ticket {ticket_id}: {e}")
                raise

    async def mark_error(self, ticket_id: UUID, error_message: str) -> None:
        """Mark ticket as FAILED."""
        async with self._get_session() as session:
            try:
                stmt = (
                    update(TicketModel)
                    .where(TicketModel.id == ticket_id)
                    .values(status=TicketStatus.FAILED, updated_at=datetime.utcnow())
                )
                await session.execute(stmt)

                attr_stmt = (
                    insert(AttributeModel)
                    .values(
                        ticket_id=ticket_id,
                        key=TicketAttributeKeys.ERROR_MESSAGE,
                        value=error_message,
                        created_at=datetime.utcnow(),
                        is_deleted=False,
                    )
                    .on_conflict_do_update(
                        constraint="ticketattribute_ticket_id_key_key",
                        set_={"value": error_message, "is_deleted": False},
                    )
                )
                await session.execute(attr_stmt)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error marking error for ticket {ticket_id}: {e}")
                raise

    async def mark_for_retry(
        self,
        ticket_id: UUID,
        error_message: str,
        next_retry_at: datetime,
    ) -> None:
        """Mark ticket for retry by resetting status to PENDING
        and updating retry attributes."""
        async with self._get_session() as session:
            try:
                # 1. Update status to PENDING
                stmt = (
                    update(TicketModel)
                    .where(TicketModel.id == ticket_id)
                    .values(status=TicketStatus.PENDING, updated_at=datetime.utcnow())
                )
                await session.execute(stmt)

                # 2. Get current retry count
                query = select(AttributeModel).where(
                    (AttributeModel.ticket_id == ticket_id)
                    & (AttributeModel.key == TicketAttributeKeys.RETRY_COUNT)
                )
                result = await session.execute(query)
                attr = result.scalar_one_or_none()
                retry_count = int(attr.value) if attr else 0

                # 3. Add/Update attributes
                new_attrs = {
                    TicketAttributeKeys.ERROR_MESSAGE: error_message,
                    TicketAttributeKeys.RETRY_COUNT: str(retry_count + 1),
                    TicketAttributeKeys.NEXT_RETRY_AT: next_retry_at.isoformat(),
                }

                for key, value in new_attrs.items():
                    attr_stmt = (
                        insert(AttributeModel)
                        .values(
                            ticket_id=ticket_id,
                            key=key,
                            value=value,
                            created_at=datetime.utcnow(),
                            is_deleted=False,
                        )
                        .on_conflict_do_update(
                            constraint="ticketattribute_ticket_id_key_key",
                            set_={"value": value, "is_deleted": False},
                        )
                    )
                    await session.execute(attr_stmt)

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error marking for retry for ticket {ticket_id}: {e}")
                raise

    async def pick_pending_ticket(self) -> Optional[DomainTicket]:
        """Pick the next pending ticket with row locking."""
        async with self._get_session() as session:
            try:
                query = (
                    select(TicketModel)
                    .where(TicketModel.status == TicketStatus.PENDING)
                    .where(TicketModel.is_deleted.is_(False))
                    .order_by(TicketModel.created_at.asc())
                    .limit(1)
                )

                # Only use FOR UPDATE SKIP LOCKED on PostgreSQL
                if session.bind.dialect.name == "postgresql":
                    query = query.with_for_update(skip_locked=True)

                result = await session.execute(query)
                ticket_db = result.scalar_one_or_none()

                if not ticket_db:
                    return None

                # Claim ticket
                ticket_db.status = TicketStatus.PROCESSING
                ticket_db.updated_at = datetime.utcnow()

                await session.commit()
                await session.refresh(ticket_db)

                return self._to_domain(ticket_db)
            except Exception as e:
                await session.rollback()
                logger.error(f"Error picking pending ticket: {e}")
                raise

    async def get_ticket_by_id(self, ticket_id: UUID) -> Optional[DomainTicket]:
        """Fetch ticket by ID."""
        async with self._get_session() as session:
            query = select(TicketModel).where(TicketModel.id == ticket_id)
            result = await session.execute(query)
            ticket_db = result.scalar_one_or_none()
            return self._to_domain(ticket_db) if ticket_db else None
