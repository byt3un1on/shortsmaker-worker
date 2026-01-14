"""Ticket attribute domain entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TicketAttribute:
    """
    TicketAttribute domain entity representing a key-value pair for a ticket.

    Attributes are used to store dynamic data related to a ticket, such as:
    - theme: The theme/topic of the video
    - description: The description provided by the user
    - script: The generated script
    - audio_url: URL to the audio file in storage
    - video_url: URL to the video file in storage
    - error_message: Error details if processing fails
    """

    id: UUID
    ticket_id: UUID
    key: str
    value: str
    created_at: datetime
    is_deleted: bool = False


class TicketAttributeKeys:
    """
    Constants for standard ticket attribute keys.

    This helps maintain consistency across the codebase when
    reading/writing ticket attributes.
    """

    # Control attributes
    STEP = "step"  # Current pipeline step: SCRIPT, AUDIO, VIDEO

    # Input attributes (provided by user/API)
    THEME = "theme"
    DESCRIPTION = "description"
    PROMPT = "prompt"

    # Generated attributes (produced by worker steps)
    SCRIPT = "script"
    AUDIO_URL = "audio_url"
    VIDEO_URL = "video_url"

    # Error tracking
    ERROR_MESSAGE = "error_message"
    ERROR_STEP = "error_step"
    RETRY_COUNT = "retry_count"
    NEXT_RETRY_AT = "next_retry_at"

    # Metadata
    DURATION_SECONDS = "duration_seconds"
    ASPECT_RATIO = "aspect_ratio"


class TicketSteps:
    """Constants for pipeline steps."""

    SCRIPT = "SCRIPT"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    DONE = "DONE"
