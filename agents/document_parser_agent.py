from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI
import json

from utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentParseError(Exception):
    pass


@dataclass
class LeaseFields:
    tenant_name: Optional[str]
    monthly_rent: Optional[str]
    lease_start: Optional[str]
    lease_end: Optional[str]
    key_clauses: list[str] = field(default_factory=list)
    correlation_id: str = ""
    parse_warnings: list[str] = field(default_factory=list)


class DocumentParserAgent:
    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model

    def process(self, document_text: str, correlation_id: str) -> LeaseFields:
        logger.debug(
            "DocumentParserAgent: received document",
            extra={"correlation_id": correlation_id, "agent": "document_parser", "chars": len(document_text)},
        )

        try:
            fields = self._extract_fields(document_text, correlation_id)
        except Exception as exc:
            logger.error(
                "DocumentParserAgent: extraction failed",
                extra={"correlation_id": correlation_id, "agent": "document_parser", "error": str(exc)},
            )
            raise DocumentParseError(f"Failed to parse document: {exc}") from exc

        warnings = self._check_missing(fields)
        fields.parse_warnings = warnings
        fields.correlation_id = correlation_id

        if warnings:
            logger.warning(
                "DocumentParserAgent: missing fields detected",
                extra={"correlation_id": correlation_id, "agent": "document_parser", "warnings": warnings},
            )

        logger.info(
            "DocumentParserAgent: complete",
            extra={
                "correlation_id": correlation_id,
                "agent": "document_parser",
                "tenant": fields.tenant_name,
                "warnings_count": len(warnings),
            },
        )
        return fields

    def _extract_fields(self, text: str, correlation_id: str) -> LeaseFields:
        prompt = (
            "Extract structured lease information from the text below. "
            "Return a JSON object with these keys: "
            "tenant_name (string or null), monthly_rent (string or null), "
            "lease_start (string or null), lease_end (string or null), "
            "key_clauses (array of strings).\n\n"
            f"Document:\n{text}"
        )
        logger.debug(
            "DocumentParserAgent: calling extraction",
            extra={"correlation_id": correlation_id, "agent": "document_parser"},
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return LeaseFields(
            tenant_name=data.get("tenant_name"),
            monthly_rent=data.get("monthly_rent"),
            lease_start=data.get("lease_start"),
            lease_end=data.get("lease_end"),
            key_clauses=data.get("key_clauses") or [],
        )

    @staticmethod
    def _check_missing(fields: LeaseFields) -> list[str]:
        warnings = []
        if not fields.tenant_name:
            warnings.append("tenant_name missing")
        if not fields.monthly_rent:
            warnings.append("monthly_rent missing")
        if not fields.lease_start:
            warnings.append("lease_start missing")
        if not fields.lease_end:
            warnings.append("lease_end missing")
        return warnings
