"""Ticket repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from core.domain.enums.ticket_status import TicketStatus
from core.domain.ticket import Ticket


class ITicketRepository(ABC):
    """
    Interface for Ticket repository operations.

    This repository is responsible for managing ticket lifecycle,
    status transitions, and attribute storage using the TICKET and
    TICKET_ATTRIBUTES tables in the database.

    Implementation should use PostgreSQL features like
    SELECT ... FOR UPDATE SKIP LOCKED for concurrent ticket processing
    to avoid race conditions between multiple workers.
    """

    @abstractmethod
    async def get_next_ticket(self, step: str) -> Optional[Ticket]:
        """
        Get the next available ticket for a specific pipeline step.

        This method should implement SELECT ... FOR UPDATE SKIP LOCKED
        to safely retrieve a ticket for processing in a concurrent environment.
        It filters by status=PENDING and the "step" attribute.

        Args:
            step: The pipeline step to filter by (SCRIPT, AUDIO, VIDEO).

        Returns:
            The next available Ticket or None if no tickets are available.
        """
        pass

    @abstractmethod
    async def load_attributes(self, ticket_id: UUID) -> dict[str, str]:
        """
        Load all attributes for a ticket.

        Retrieves all key-value pairs from TICKET_ATTRIBUTES table
        for the specified ticket.

        Args:
            ticket_id: The UUID of the ticket.

        Returns:
            A dictionary mapping attribute keys to their values.
        """
        pass

    @abstractmethod
    async def save_attributes(self, ticket_id: UUID, attrs: dict[str, str]) -> None:
        """
        Save or update multiple attributes for a ticket.

        For each key-value pair, either inserts a new attribute
        or updates an existing one (upsert logic).

        Args:
            ticket_id: The UUID of the ticket.
            attrs: Dictionary of attributes to save/update.
        """
        pass

    @abstractmethod
    async def update_status(self, ticket_id: UUID, new_status: TicketStatus) -> None:
        """
        Update the status of a ticket.

        Updates the status field in the TICKET table and sets
        updated_at to the current timestamp.

        Args:
            ticket_id: The UUID of the ticket.
            new_status: The new status to set.
        """
        pass

    @abstractmethod
    async def mark_error(self, ticket_id: UUID, error_message: str) -> None:
        """
        Mark a ticket as failed with an error message.
        """
        pass

    @abstractmethod
    async def mark_for_retry(
        self, ticket_id: UUID, error_message: str, next_retry_at: datetime
    ) -> None:
        """
        Mark a ticket for retry, incrementing retry count and setting next attempt time.
        """
        pass

    @abstractmethod
    async def get_ticket_by_id(self, ticket_id: UUID) -> Optional[Ticket]:
        """
        Retrieve a ticket by its ID.

        Args:
            ticket_id: The UUID of the ticket.

        Returns:
            The Ticket if found, None otherwise.
        """
        pass
