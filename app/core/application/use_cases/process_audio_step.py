from datetime import datetime, timedelta

from core.domain.ticket import Ticket
from core.domain.ticket_attribute import TicketAttributeKeys, TicketSteps
from core.interfaces.repositories.i_ticket_repository import ITicketRepository
from core.interfaces.services.i_audio_service import IAudioService
from core.interfaces.services.i_storage_service import IStorageService
from infra.config.settings import get_settings
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class ProcessAudioStepUseCase:
    def __init__(
        self,
        ticket_repository: ITicketRepository,
        audio_service: IAudioService,
        storage_service: IStorageService,
    ):
        self.ticket_repository = ticket_repository
        self.audio_service = audio_service
        self.storage_service = storage_service
        self.settings = get_settings()

    async def execute(self, ticket: Ticket) -> None:
        try:
            logger.info(f"Processing audio for ticket {ticket.id}")

            # 1. Load attributes
            attrs = await self.ticket_repository.load_attributes(ticket.id)
            script = attrs.get(TicketAttributeKeys.SCRIPT)

            if not script:
                raise ValueError("Script not found in ticket attributes")

            # 2. Generate audio
            script_text = " ".join(str(v) for v in script.values())
            audio_content = await self.audio_service.generate_audio(script_text)

            # 3. Upload to storage
            file_path = f"audio/{ticket.id}.mp3"
            audio_url = await self.storage_service.upload_file(audio_content, file_path)

            # 4. Save audio URL and move to next step
            await self.ticket_repository.save_attributes(
                ticket.id,
                {
                    TicketAttributeKeys.AUDIO_URL: audio_url,
                    TicketAttributeKeys.STEP: TicketSteps.VIDEO,
                },
            )

            # 5. Mark as PENDING
            from core.domain.enums.ticket_status import TicketStatus

            await self.ticket_repository.update_status(ticket.id, TicketStatus.PENDING)

            logger.info(f"Audio generated and uploaded for ticket {ticket.id}")

        except Exception as e:
            logger.error(f"Error processing audio for ticket {ticket.id}: {e}")
            await self._handle_failure(ticket, str(e))

    async def _handle_failure(self, ticket: Ticket, error_message: str) -> None:
        attrs = await self.ticket_repository.load_attributes(ticket.id)
        retry_count = int(attrs.get(TicketAttributeKeys.RETRY_COUNT, "0"))

        if retry_count < self.settings.worker_max_retries:
            base_delay = self.settings.worker_retry_delay
            delay_seconds = base_delay * (2**retry_count)
            retry_dt = datetime.utcnow()
            next_retry = retry_dt + timedelta(seconds=delay_seconds)
            msg = "Scheduling retry {} for ticket {} at {}".format(
                retry_count + 1, ticket.id, next_retry
            )
            logger.info(msg)
            await self.ticket_repository.mark_for_retry(
                ticket.id,
                error_message,
                next_retry,
            )
        else:
            logger.error(
                f"Max retries reached for ticket {ticket.id}. Marking as FAILED."
            )
            await self.ticket_repository.mark_error(ticket.id, error_message)
