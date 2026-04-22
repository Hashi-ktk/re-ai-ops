from dataclasses import dataclass
from openai import OpenAI
import json

from utils.logging_config import get_logger

logger = get_logger(__name__)

VALID_CATEGORIES = ("maintenance_request", "lease_inquiry", "payment_issue", "general")


class EmailTriageError(Exception):
    pass


@dataclass
class EmailResult:
    email_id: str
    category: str
    draft_reply: str
    correlation_id: str


class EmailTriageAgent:
    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model

    def process(self, email: dict, correlation_id: str) -> EmailResult:
        email_id = email.get("id", "unknown")
        logger.debug(
            "EmailTriageAgent: received email",
            extra={"correlation_id": correlation_id, "agent": "email_triage", "subject": email.get("subject", "")},
        )

        try:
            category = self._classify(email, correlation_id)
            draft = self._generate_draft(email, category, correlation_id)
        except Exception as exc:
            logger.error(
                "EmailTriageAgent: processing failed",
                extra={"correlation_id": correlation_id, "agent": "email_triage", "error": str(exc)},
            )
            raise EmailTriageError(f"Failed to triage email '{email_id}': {exc}") from exc

        result = EmailResult(
            email_id=email_id,
            category=category,
            draft_reply=draft,
            correlation_id=correlation_id,
        )
        logger.info(
            "EmailTriageAgent: complete",
            extra={"correlation_id": correlation_id, "agent": "email_triage", "category": category},
        )
        return result

    def _classify(self, email: dict, correlation_id: str) -> str:
        prompt = (
            "Classify this property management email into exactly one of these categories: "
            f"{', '.join(VALID_CATEGORIES)}.\n\n"
            f"Subject: {email.get('subject', '')}\n"
            f"Body: {email.get('body', '')}\n\n"
            "Return a JSON object with a single key 'category'."
        )
        logger.debug(
            "EmailTriageAgent: calling classify",
            extra={"correlation_id": correlation_id, "agent": "email_triage"},
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        category = data.get("category", "general")
        if category not in VALID_CATEGORIES:
            logger.warning(
                "EmailTriageAgent: unexpected category, defaulting to general",
                extra={"correlation_id": correlation_id, "agent": "email_triage"},
            )
            category = "general"
        return category

    def _generate_draft(self, email: dict, category: str, correlation_id: str) -> str:
        prompt = (
            "You are a professional property manager. Write a concise, polite draft reply "
            f"to the following email. The email has been classified as: {category}.\n\n"
            f"Subject: {email.get('subject', '')}\n"
            f"Body: {email.get('body', '')}\n\n"
            "Return a JSON object with a single key 'draft'."
        )
        logger.debug(
            "EmailTriageAgent: calling draft generation",
            extra={"correlation_id": correlation_id, "agent": "email_triage"},
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return data.get("draft", "Thank you for reaching out. We will follow up shortly.")
