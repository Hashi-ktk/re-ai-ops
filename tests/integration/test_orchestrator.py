import json
import pytest
from unittest.mock import MagicMock

from agents.orchestrator import Orchestrator, OrchestratorError
from agents.email_triage_agent import EmailResult
from agents.document_parser_agent import LeaseFields
from utils.mock_data import SAMPLE_EMAILS, SAMPLE_LEASE_TEXT


def _make_client(email_category: str = "maintenance_request") -> MagicMock:
    client = MagicMock()

    def _side_effect(*args, **kwargs):
        messages = kwargs.get("messages", [])
        content = messages[0]["content"] if messages else ""
        if "classify" in content.lower() or "category" in content.lower():
            body = json.dumps({"category": email_category})
        elif "draft" in content.lower() or "reply" in content.lower():
            body = json.dumps({"draft": "Thank you for contacting us."})
        else:
            body = json.dumps({
                "tenant_name": "Jane Demo",
                "monthly_rent": "$1,850.00",
                "lease_start": "2024-02-01",
                "lease_end": "2025-01-31",
                "key_clauses": ["Late fee applies after 5th"],
            })
        choice = MagicMock()
        choice.message.content = body
        response = MagicMock()
        response.choices = [choice]
        return response

    client.chat.completions.create.side_effect = _side_effect
    return client


class TestOrchestratorEmailFlow:
    def test_routes_email_to_triage_agent(self):
        client = _make_client()
        orch = Orchestrator(client)
        result = orch.process("email", SAMPLE_EMAILS[0])
        assert isinstance(result, EmailResult)
        assert result.category == "maintenance_request"

    def test_email_result_has_draft(self):
        client = _make_client()
        orch = Orchestrator(client)
        result = orch.process("email", SAMPLE_EMAILS[1])
        assert isinstance(result.draft_reply, str)
        assert len(result.draft_reply) > 0


class TestOrchestratorDocumentFlow:
    def test_routes_document_to_parser_agent(self):
        client = _make_client()
        orch = Orchestrator(client)
        result = orch.process("document", SAMPLE_LEASE_TEXT)
        assert isinstance(result, LeaseFields)
        assert result.tenant_name == "Jane Demo"

    def test_document_result_has_clauses(self):
        client = _make_client()
        orch = Orchestrator(client)
        result = orch.process("document", SAMPLE_LEASE_TEXT)
        assert len(result.key_clauses) > 0


class TestOrchestratorDryRun:
    def test_dry_run_skips_api_calls(self):
        client = MagicMock()
        orch = Orchestrator(client, dry_run=True)
        orch.process("email", SAMPLE_EMAILS[0])
        client.chat.completions.create.assert_not_called()

    def test_dry_run_returns_email_result(self):
        client = MagicMock()
        orch = Orchestrator(client, dry_run=True)
        result = orch.process("email", SAMPLE_EMAILS[0])
        assert isinstance(result, EmailResult)
        assert "[DRY RUN]" in result.draft_reply

    def test_dry_run_returns_document_result(self):
        client = MagicMock()
        orch = Orchestrator(client, dry_run=True)
        result = orch.process("document", SAMPLE_LEASE_TEXT)
        assert isinstance(result, LeaseFields)
        assert "[DRY RUN]" in result.tenant_name


class TestOrchestratorErrorHandling:
    def test_unknown_input_type_raises(self):
        client = _make_client()
        orch = Orchestrator(client)
        with pytest.raises(OrchestratorError, match="Unknown input_type"):
            orch.process("fax_machine", {})

    def test_agent_failure_raises_orchestrator_error(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("Upstream failure")
        orch = Orchestrator(client)
        with pytest.raises(OrchestratorError, match="Processing failed"):
            orch.process("email", SAMPLE_EMAILS[0])
