# Usage & Testing Guide

A complete walkthrough for setting up, running, and testing this project from scratch.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone & Project Structure](#2-clone--project-structure)
3. [Python Setup](#3-python-setup)
4. [TypeScript Webhook Setup](#4-typescript-webhook-setup)
5. [Running Tests](#5-running-tests)
6. [Running the Demo (no API key needed)](#6-running-the-demo-no-api-key-needed)
7. [Running the Demo (live API)](#7-running-the-demo-live-api)
8. [Testing the Webhook Manually](#8-testing-the-webhook-manually)
9. [Understanding the Logs](#9-understanding-the-logs)
10. [What Each File Does](#10-what-each-file-does)
11. [Common Errors & Fixes](#11-common-errors--fixes)

---

## 1. Prerequisites

Make sure you have the following installed:

| Tool | Version | Check |
|---|---|---|
| Python | 3.11 or higher | `python --version` |
| Node.js | 18 or higher | `node --version` |
| npm | 8 or higher | `npm --version` |
| Git | any | `git --version` |

An OpenAI API key is **only needed to run the live demo**. All tests run fully offline without one.

---

## 2. Clone & Project Structure

```bash
git clone https://github.com/YOUR_USERNAME/re-ai-ops.git
cd re-ai-ops
```

```
re-ai-ops/
├── agents/                  ← Python AI agents
│   ├── email_triage_agent.py
│   ├── document_parser_agent.py
│   └── orchestrator.py
├── utils/
│   ├── logging_config.py    ← structured JSON logger
│   └── mock_data.py         ← sanitized fake data for tests/demo
├── tests/
│   ├── unit/                ← isolated agent tests (no API calls)
│   └── integration/         ← end-to-end orchestrator tests
├── scripts/
│   └── run_demo.py          ← CLI runner
├── webhook/                 ← TypeScript Express webhook
│   ├── src/
│   │   ├── server.ts
│   │   ├── validator.ts
│   │   └── logger.ts
│   └── tests/
│       └── webhook.test.ts
├── .env.example
├── requirements.txt
└── README.md
```

---

## 3. Python Setup

**Step 1 — Create a virtual environment**

```bash
python -m venv .venv
```

**Step 2 — Activate it**

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` appear at the start of your terminal prompt.

**Step 3 — Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 4 — Set up environment variables (optional — only for live API runs)**

```bash
cp .env.example .env
```

Open `.env` and add your OpenAI key:

```
OPENAI_API_KEY=sk-your-key-here
```

> If you don't have a key or don't want to use one, skip this step. Tests and the dry-run demo work without it.

---

## 4. TypeScript Webhook Setup

```bash
cd webhook
npm install
cd ..
```

That's it. No environment variables needed for the webhook.

---

## 5. Running Tests

### Python tests

From the root of the project (with venv activated):

```bash
pytest
```

Expected output:

```
collected 23 items

tests/integration/test_orchestrator.py ......... [ 39%]
tests/unit/test_document_parser.py ......        [ 65%]
tests/unit/test_email_triage.py ........         [100%]

23 passed in Xs
```

To see which lines are covered:

```bash
pytest --cov=agents --cov-report=term-missing
```

**Important:** No API key is needed. Every test mocks the OpenAI client — zero real network calls are made.

---

### TypeScript tests

```bash
cd webhook
npm test
```

Expected output:

```
PASS tests/webhook.test.ts
  POST /inbound-event
    valid payloads
      ✓ accepts a valid email event and returns 202
      ✓ accepts a valid document event and returns 202
      ✓ respects x-correlation-id header
    invalid payloads
      ✓ returns 400 for unknown event type
      ✓ returns 400 when email sender is not a valid email
      ✓ returns 400 when required fields are missing
      ✓ returns 400 for empty body

Tests: 7 passed
```

---

## 6. Running the Demo (no API key needed)

Use `--dry-run` to run the full workflow without making any OpenAI API calls. This is safe to run anywhere with no credentials.

**Email triage dry run:**

```bash
python scripts/run_demo.py --type email --dry-run
```

Output:

```
--- Processing email: Leaking faucet in unit 4B ---
  Category:    general
  Draft reply: [DRY RUN] No API call made....

--- Processing email: Question about lease renewal terms ---
  Category:    general
  Draft reply: [DRY RUN] No API call made....
```

**Document parsing dry run:**

```bash
python scripts/run_demo.py --type document --dry-run
```

Output:

```
--- Processing lease document ---
  Tenant:    [DRY RUN]
  Rent:      None
  Lease:     None → None
  Clauses:   0 found
```

---

## 7. Running the Demo (live API)

Make sure your `.env` file has a valid `OPENAI_API_KEY`.

```bash
# Triage sample emails — classifies each and generates a draft reply
python scripts/run_demo.py --type email

# Parse a sample lease document — extracts tenant, rent, dates, clauses
python scripts/run_demo.py --type document
```

Example live output for email triage:

```
--- Processing email: Leaking faucet in unit 4B ---
  Category:    maintenance_request
  Draft reply: Dear Tenant, thank you for reporting the issue with your kitchen
               faucet. We will schedule a maintenance visit within 24-48 hours...

--- Processing email: Question about lease renewal terms ---
  Category:    lease_inquiry
  Draft reply: Hi, thank you for reaching out about your lease renewal...
```

Example live output for document parsing:

```
--- Processing lease document ---
  Tenant:    Jane Demo
  Rent:      $1,850.00
  Lease:     2024-02-01 → 2025-01-31
  Clauses:   5 found
```

---

## 8. Testing the Webhook Manually

**Start the server:**

```bash
cd webhook
npm run dev
```

You should see:

```json
{"level":"info","message":"webhook: listening on port 3000"}
```

**Send a valid email event** (in a new terminal):

```bash
curl -X POST http://localhost:3000/inbound-event \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "payload": {
      "id": "email-001",
      "sender": "tenant@example.com",
      "subject": "Leaking faucet",
      "body": "The kitchen faucet has been dripping for three days."
    }
  }'
```

Expected response:

```json
{
  "ok": true,
  "correlationId": "a3f1bc",
  "type": "email",
  "message": "Event queued for processing."
}
```

**Send a document event:**

```bash
curl -X POST http://localhost:3000/inbound-event \
  -H "Content-Type: application/json" \
  -d '{
    "type": "document",
    "payload": {
      "id": "doc-001",
      "filename": "lease.txt",
      "text": "Tenant: Jane Demo. Rent: $1850. Lease start: 2024-02-01."
    }
  }'
```

**Send an invalid payload (validation test):**

```bash
curl -X POST http://localhost:3000/inbound-event \
  -H "Content-Type: application/json" \
  -d '{"type": "fax", "payload": {}}'
```

Expected response (400):

```json
{
  "ok": false,
  "correlationId": "...",
  "errors": { ... }
}
```

---

## 9. Understanding the Logs

Every action emits a structured JSON log line. Example:

```json
{"level": "INFO", "logger": "agents.orchestrator", "message": "Orchestrator: routing request", "correlation_id": "a3f1bc", "input_type": "email", "dry_run": false}
{"level": "DEBUG", "logger": "agents.email_triage_agent", "message": "EmailTriageAgent: calling classify", "correlation_id": "a3f1bc", "agent": "email_triage"}
{"level": "INFO", "logger": "agents.email_triage_agent", "message": "EmailTriageAgent: complete", "correlation_id": "a3f1bc", "agent": "email_triage", "category": "maintenance_request"}
```

**Key fields:**

| Field | Meaning |
|---|---|
| `level` | DEBUG / INFO / WARN / ERROR |
| `correlation_id` | Unique ID per request — trace a full request across all log lines |
| `agent` | Which agent produced this log line |
| `category` | Email classification result |
| `error` | Error message (only present on failure) |

If something fails, search logs by `correlation_id` to see every step that ran for that request.

---

## 10. What Each File Does

| File | Purpose |
|---|---|
| `agents/email_triage_agent.py` | Classifies emails into 4 categories and generates draft replies |
| `agents/document_parser_agent.py` | Extracts structured fields from lease document text |
| `agents/orchestrator.py` | Single entry point — routes to the right agent, handles `dry_run` |
| `utils/logging_config.py` | JSON log formatter used by all agents |
| `utils/mock_data.py` | Fake sanitized emails and lease text — used by tests and demo |
| `tests/unit/` | Tests for each agent in isolation (mocked OpenAI) |
| `tests/integration/` | End-to-end tests through the orchestrator (mocked OpenAI) |
| `scripts/run_demo.py` | CLI that runs the workflow against mock data |
| `webhook/src/server.ts` | Express HTTP server — `POST /inbound-event` endpoint |
| `webhook/src/validator.ts` | Zod schemas that validate incoming event payloads |
| `webhook/src/logger.ts` | Structured JSON logger for the webhook layer |
| `webhook/tests/webhook.test.ts` | Jest tests covering valid and invalid webhook payloads |

---

## 11. Common Errors & Fixes

**`ModuleNotFoundError: No module named 'agents'`**

Make sure you are running pytest from the project root, not from inside a subdirectory:

```bash
cd re-ai-ops   # project root
pytest
```

---

**`OPENAI_API_KEY not set`**

You tried to run the live demo without a key. Either:
- Add the key to your `.env` file, or
- Add `--dry-run` to skip API calls:

```bash
python scripts/run_demo.py --type email --dry-run
```

---

**`Cannot find module 'zod'` or similar**

Node dependencies are not installed. Run:

```bash
cd webhook
npm install
```

---

**`(.venv)` not appearing after activation (Windows PowerShell)**

Run this once to allow script execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

---

**Tests fail with `ImportError`**

Make sure the venv is activated and dependencies are installed:

```bash
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pytest
```
