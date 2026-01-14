import json
from datetime import datetime, timedelta

from core.domain.ticket import Ticket
from core.domain.ticket_attribute import TicketAttributeKeys, TicketSteps
from core.interfaces.repositories.i_ticket_repository import ITicketRepository
from core.interfaces.services.i_llm_service import ILLMService
from infra.config.settings import get_settings
from infra.logging.logger import get_logger

logger = get_logger(__name__)


class ProcessScriptStepUseCase:
    def __init__(self, ticket_repository: ITicketRepository, llm_service: ILLMService):
        self.ticket_repository = ticket_repository
        self.llm_service = llm_service
        self.settings = get_settings()

    async def execute(self, ticket: Ticket) -> None:
        try:
            logger.info(f"Processing script for ticket {ticket.id}")

            # 1. Load attributes
            attrs = await self.ticket_repository.load_attributes(ticket.id)
            prompt = attrs.get(TicketAttributeKeys.PROMPT)

            if not prompt:
                raise ValueError("Prompt not found in ticket attributes")

            # 2. Generate script
            script = await self.llm_service.generate_script(prompt)

            # 3. Save script and move to next step
            await self.ticket_repository.save_attributes(
                ticket.id,
                {
                    TicketAttributeKeys.SCRIPT: json.dumps(script),
                    TicketAttributeKeys.STEP: TicketSteps.AUDIO,
                },
            )

            # 4. Mark as PENDING so it's picked up by the next worker
            from core.domain.enums.ticket_status import TicketStatus

            await self.ticket_repository.update_status(ticket.id, TicketStatus.PENDING)

            logger.info(f"Script generated for ticket {ticket.id}")

        except Exception as e:
            logger.error(f"Error processing script for ticket {ticket.id}: {e}")
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
