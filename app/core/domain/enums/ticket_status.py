"""Ticket status enumeration representing the state machine of a ticket."""

from enum import Enum


class TicketStatus(str, Enum):
    """
    Enum representing all possible states in the ticket processing pipeline.

    The ticket flows through these states:
    PENDING -> PROCESSING -> COMPLETED

    At any point, if an error occurs, the ticket moves to FAILED state.
    """

    # Initial state or waiting for next step
    PENDING = "PENDING"

    # Currently being processed
    PROCESSING = "PROCESSING"

    # All steps completed successfully
    COMPLETED = "COMPLETED"

    # An error occurred during processing
    FAILED = "FAILED"
