import json
import pytest
from unittest.mock import MagicMock, patch

from agents.email_triage_agent import EmailTriageAgent, EmailTriageError, VALID_CATEGORIES
from utils.mock_data import SAMPLE_EMAILS


def _make_client(category: str = "maintenance_request", draft: str = "We will send a technician.") -> MagicMock:
    """Return a mock OpenAI client whose completions return predictable JSON."""
    client = MagicMock()

    def _side_effect(*args, **kwargs):
        messages = kwargs.get("messages", [])
        content = messages[0]["content"] if messages else ""
        if "classify" in content.lower() or "category" in content.lower():
            body = json.dumps({"category": category})
        else:
            body = json.dumps({"draft": draft})
        choice = MagicMock()
        choice.message.content = body
        response = MagicMock()
        response.choices = [choice]
        return response

    client.chat.completions.create.side_effect = _side_effect
    return client


class TestEmailTriageAgent:
    def test_classify_maintenance_request(self):
        client = _make_client(category="maintenance_request")
        agent = EmailTriageAgent(client)
        result = agent.process(SAMPLE_EMAILS[0], correlation_id="test-001")
        assert result.category == "maintenance_request"
        assert result.email_id == "email-001"

    def test_classify_lease_inquiry(self):
        client = _make_client(category="lease_inquiry")
        agent = EmailTriageAgent(client)
        result = agent.process(SAMPLE_EMAILS[1], correlation_id="test-002")
        assert result.category == "lease_inquiry"

    def test_classify_payment_issue(self):
        client = _make_client(category="payment_issue")
        agent = EmailTriageAgent(client)
        result = agent.process(SAMPLE_EMAILS[2], correlation_id="test-003")
        assert result.category == "payment_issue"

    def test_invalid_category_defaults_to_general(self):
        client = _make_client(category="completely_invalid_value")
        agent = EmailTriageAgent(client)
        result = agent.process(SAMPLE_EMAILS[3], correlation_id="test-004")
        assert result.category == "general"

    def test_draft_reply_populated(self):
        expected_draft = "Thank you for reporting this. We will address it shortly."
        client = _make_client(category="maintenance_request", draft=expected_draft)
        agent = EmailTriageAgent(client)
        result = agent.process(SAMPLE_EMAILS[0], correlation_id="test-005")
        assert result.draft_reply == expected_draft

    def test_correlation_id_preserved(self):
        client = _make_client()
        agent = EmailTriageAgent(client)
        result = agent.process(SAMPLE_EMAILS[0], correlation_id="corr-xyz")
        assert result.correlation_id == "corr-xyz"

    def test_api_failure_raises_email_triage_error(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("API timeout")
        agent = EmailTriageAgent(client)
        with pytest.raises(EmailTriageError, match="Failed to triage"):
            agent.process(SAMPLE_EMAILS[0], correlation_id="test-err")

    def test_all_valid_categories_accepted(self):
        for cat in VALID_CATEGORIES:
            client = _make_client(category=cat)
            agent = EmailTriageAgent(client)
            result = agent.process(SAMPLE_EMAILS[0], correlation_id=f"test-{cat}")
            assert result.category == cat
