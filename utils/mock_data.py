"""Sanitized sample data for tests and local demo runs. No real tenant data."""

SAMPLE_EMAILS = [
    {
        "id": "email-001",
        "sender": "tenant.demo@example.com",
        "subject": "Leaking faucet in unit 4B",
        "body": (
            "Hi, the kitchen faucet in my unit has been dripping constantly for three days. "
            "Water is pooling under the sink. Please send someone to fix it as soon as possible."
        ),
    },
    {
        "id": "email-002",
        "sender": "prospective.demo@example.com",
        "subject": "Question about lease renewal terms",
        "body": (
            "Hello, my lease is up in two months and I want to understand the renewal options. "
            "Will the rent increase? Is there a month-to-month option? Thanks."
        ),
    },
    {
        "id": "email-003",
        "sender": "resident.demo@example.com",
        "subject": "Late payment this month",
        "body": (
            "I wanted to let you know my rent payment will be a few days late this month "
            "due to a banking delay. I can pay by the 7th. Please waive the late fee if possible."
        ),
    },
    {
        "id": "email-004",
        "sender": "neighbor.demo@example.com",
        "subject": "Noise complaint",
        "body": (
            "The tenants in unit 6A play loud music after 11pm on weekdays. "
            "I have mentioned it to them but nothing has changed. Can management address this?"
        ),
    },
]

SAMPLE_LEASE_TEXT = """
RESIDENTIAL LEASE AGREEMENT

Tenant Name: Jane Demo
Property Address: 42 Sanitized Street, Unit 4B, Springfield, ST 00000
Monthly Rent: $1,850.00
Lease Start Date: 2024-02-01
Lease End Date: 2025-01-31

Key Clauses:
- Late fee of $75 applies if rent is not received by the 5th of the month.
- Tenant is responsible for minor repairs under $150.
- No subletting without written landlord consent.
- 60-day notice required before lease termination.
- Pets allowed with a $300 non-refundable deposit.
"""

SAMPLE_DOCUMENT_INVALID = """
This document is incomplete and missing required fields.
Just some random text with no structured lease information.
"""
