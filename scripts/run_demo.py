#!/usr/bin/env python3
"""
CLI demo runner.

Usage:
    python scripts/run_demo.py --type email
    python scripts/run_demo.py --type document
    python scripts/run_demo.py --type email --dry-run
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI

from agents.orchestrator import Orchestrator
from utils.mock_data import SAMPLE_EMAILS, SAMPLE_LEASE_TEXT
from utils.logging_config import get_logger

logger = get_logger("demo")


def main() -> None:
    parser = argparse.ArgumentParser(description="Real Estate AI Ops — demo runner")
    parser.add_argument("--type", choices=["email", "document"], default="email", help="Input type to process")
    parser.add_argument("--dry-run", action="store_true", help="Skip OpenAI API calls")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: OPENAI_API_KEY not set. Use --dry-run to test without an API key.")
        sys.exit(1)

    client = OpenAI(api_key=api_key or "dry-run-placeholder")
    orchestrator = Orchestrator(client, dry_run=args.dry_run)

    if args.type == "email":
        for email in SAMPLE_EMAILS[:2]:
            print(f"\n--- Processing email: {email['subject']} ---")
            result = orchestrator.process("email", email)
            print(f"  Category:    {result.category}")
            print(f"  Draft reply: {result.draft_reply[:120]}...")
    else:
        print("\n--- Processing lease document ---")
        result = orchestrator.process("document", SAMPLE_LEASE_TEXT)
        print(f"  Tenant:    {result.tenant_name}")
        print(f"  Rent:      {result.monthly_rent}")
        print(f"  Lease:     {result.lease_start} → {result.lease_end}")
        print(f"  Clauses:   {len(result.key_clauses)} found")
        if result.parse_warnings:
            print(f"  Warnings:  {result.parse_warnings}")


if __name__ == "__main__":
    main()
