import json
import pytest
from unittest.mock import MagicMock

from agents.document_parser_agent import DocumentParserAgent, DocumentParseError
from utils.mock_data import SAMPLE_LEASE_TEXT, SAMPLE_DOCUMENT_INVALID


def _make_client(fields: dict) -> MagicMock:
    """Return a mock OpenAI client that responds with the given lease fields JSON."""
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = json.dumps(fields)
    response = MagicMock()
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client


FULL_FIELDS = {
    "tenant_name": "Jane Demo",
    "monthly_rent": "$1,850.00",
    "lease_start": "2024-02-01",
    "lease_end": "2025-01-31",
    "key_clauses": [
        "Late fee of $75 after the 5th",
        "Tenant responsible for repairs under $150",
        "No subletting without consent",
    ],
}


class TestDocumentParserAgent:
    def test_full_extraction(self):
        client = _make_client(FULL_FIELDS)
        agent = DocumentParserAgent(client)
        result = agent.process(SAMPLE_LEASE_TEXT, correlation_id="test-doc-001")
        assert result.tenant_name == "Jane Demo"
        assert result.monthly_rent == "$1,850.00"
        assert result.lease_start == "2024-02-01"
        assert result.lease_end == "2025-01-31"
        assert len(result.key_clauses) == 3
        assert result.parse_warnings == []

    def test_missing_fields_generate_warnings(self):
        partial = {"tenant_name": None, "monthly_rent": None, "lease_start": None, "lease_end": None, "key_clauses": []}
        client = _make_client(partial)
        agent = DocumentParserAgent(client)
        result = agent.process(SAMPLE_DOCUMENT_INVALID, correlation_id="test-doc-002")
        assert "tenant_name missing" in result.parse_warnings
        assert "monthly_rent missing" in result.parse_warnings
        assert "lease_start missing" in result.parse_warnings
        assert "lease_end missing" in result.parse_warnings

    def test_partial_fields_warns_only_missing(self):
        partial = {
            "tenant_name": "John Doe",
            "monthly_rent": "$2,000",
            "lease_start": None,
            "lease_end": None,
            "key_clauses": [],
        }
        client = _make_client(partial)
        agent = DocumentParserAgent(client)
        result = agent.process(SAMPLE_LEASE_TEXT, correlation_id="test-doc-003")
        assert "tenant_name missing" not in result.parse_warnings
        assert "lease_start missing" in result.parse_warnings

    def test_correlation_id_preserved(self):
        client = _make_client(FULL_FIELDS)
        agent = DocumentParserAgent(client)
        result = agent.process(SAMPLE_LEASE_TEXT, correlation_id="corr-doc-abc")
        assert result.correlation_id == "corr-doc-abc"

    def test_api_failure_raises_document_parse_error(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = ConnectionError("Network error")
        agent = DocumentParserAgent(client)
        with pytest.raises(DocumentParseError, match="Failed to parse"):
            agent.process(SAMPLE_LEASE_TEXT, correlation_id="test-doc-err")

    def test_empty_clauses_list_handled(self):
        fields = {**FULL_FIELDS, "key_clauses": None}
        client = _make_client(fields)
        agent = DocumentParserAgent(client)
        result = agent.process(SAMPLE_LEASE_TEXT, correlation_id="test-doc-004")
        assert result.key_clauses == []
