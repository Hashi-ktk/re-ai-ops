import uuid
from typing import Any, Literal
from openai import OpenAI

from agents.email_triage_agent import EmailTriageAgent, EmailResult
from agents.document_parser_agent import DocumentParserAgent, LeaseFields
from utils.logging_config import get_logger

logger = get_logger(__name__)

InputType = Literal["email", "document"]

DRY_RUN_EMAIL_RESULT = EmailResult(
    email_id="dry-run",
    category="general",
    draft_reply="[DRY RUN] No API call made.",
    correlation_id="dry-run",
)

DRY_RUN_DOCUMENT_RESULT = LeaseFields(
    tenant_name="[DRY RUN]",
    monthly_rent=None,
    lease_start=None,
    lease_end=None,
    key_clauses=[],
    correlation_id="dry-run",
)


class OrchestratorError(Exception):
    pass


class Orchestrator:
    def __init__(self, client: OpenAI, dry_run: bool = False):
        self.dry_run = dry_run
        self._email_agent = EmailTriageAgent(client)
        self._doc_agent = DocumentParserAgent(client)

    def process(self, input_type: InputType, payload: Any) -> Any:
        correlation_id = str(uuid.uuid4())[:8]
        logger.info(
            "Orchestrator: routing request",
            extra={"correlation_id": correlation_id, "input_type": input_type, "dry_run": self.dry_run},
        )

        if self.dry_run:
            logger.info(
                "Orchestrator: dry_run active, skipping API calls",
                extra={"correlation_id": correlation_id},
            )
            if input_type == "email":
                return DRY_RUN_EMAIL_RESULT
            return DRY_RUN_DOCUMENT_RESULT

        try:
            if input_type == "email":
                return self._email_agent.process(payload, correlation_id)
            elif input_type == "document":
                return self._doc_agent.process(payload, correlation_id)
            else:
                raise OrchestratorError(f"Unknown input_type: '{input_type}'")
        except OrchestratorError:
            raise
        except Exception as exc:
            logger.error(
                "Orchestrator: unhandled error",
                extra={"correlation_id": correlation_id, "input_type": input_type, "error": str(exc)},
            )
            raise OrchestratorError(f"Processing failed for input_type='{input_type}': {exc}") from exc
