"""Ticket domain entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .enums.ticket_status import TicketStatus


@dataclass(frozen=True)
class Ticket:
    """
    Ticket domain entity representing a video generation request.

    This is an immutable domain object that represents the lifecycle
    and metadata of a shorts video generation request.
    """

    id: UUID
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    def is_processable(self) -> bool:
        """
        Check if the ticket can be processed.

        Returns:
            True if the ticket is not deleted and not in a terminal state.
        """
        terminal_states = {TicketStatus.COMPLETED, TicketStatus.FAILED}
        return not self.is_deleted and self.status not in terminal_states

    def is_in_pipeline(self) -> bool:
        """
        Check if the ticket is in the processing pipeline.

        Returns:
            True if the ticket is in one of the processable states.
        """
        pipeline_states = {
            TicketStatus.PENDING,
            TicketStatus.PROCESSING,
        }
        return self.status in pipeline_states


class TicketSteps:
    """
    Constants for standard ticket processing steps.

    This helps maintain consistency across the codebase when
    reading/writing ticket step attributes.
    """

    SCRIPT = "SCRIPT"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    COMPLETED = "COMPLETED"
