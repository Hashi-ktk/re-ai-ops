# real-estate-ai-ops

AI automation workflows for real estate operations: email triage and lease document parsing.

Built as a sanitized trial sample. No production credentials, no real tenant data.

**Full walkthrough:** see [USAGE.md](USAGE.md) for step-by-step setup, test commands, curl examples, log explanations, and troubleshooting.

**Author:** Muhammad Hashir Imran — all code written personally. AI coding tools (Claude Code, Cursor) were used for acceleration; every line was reviewed and understood before commit.

---

## What this does

| Agent | Input | Output |
|---|---|---|
| `EmailTriageAgent` | Email dict (id, sender, subject, body) | Category + draft reply |
| `DocumentParserAgent` | Lease document text | Structured fields (tenant, rent, dates, clauses) |
| `Orchestrator` | Input type + payload | Routes to the right agent, supports `dry_run` |
| Webhook (TypeScript) | `POST /inbound-event` JSON | Validates schema, logs event, returns 202 |

---

## Setup

### Python

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # add your OPENAI_API_KEY
```

### TypeScript webhook

```bash
cd webhook
npm install
```

---

## Running tests

### Python — unit + integration

```
pytest
```

Or with coverage:

```
pytest --cov=agents --cov-report=term-missing
```

**Test path:** `tests/`  
**No API key required** — all tests mock the OpenAI client.

### TypeScript webhook

```bash
cd webhook
npm test
```

---

## Running the demo

```bash
# Email triage (dry run — no API key needed)
python scripts/run_demo.py --type email --dry-run

# Email triage (live — requires OPENAI_API_KEY in .env)
python scripts/run_demo.py --type email

# Document parsing
python scripts/run_demo.py --type document

# Start the webhook server
cd webhook && npm run dev
# POST to http://localhost:3000/inbound-event
```

---

## Architecture

```
Orchestrator
├── EmailTriageAgent    → classify + draft reply (OpenAI)
└── DocumentParserAgent → extract lease fields (OpenAI)

webhook/src/server.ts   → Express HTTP entry point
webhook/src/validator.ts → Zod schema validation
webhook/src/logger.ts   → structured JSON logging
```

The TypeScript webhook represents the HTTP ingress layer — in production it would forward validated events to the Python orchestrator via an internal queue or direct HTTP call. For this trial they are independent and each fully testable on their own.

---

## Logging

All Python agents emit structured JSON logs to stdout:

```json
{"level": "INFO", "logger": "agents.orchestrator", "message": "Orchestrator: routing request", "correlation_id": "a3f1bc", "input_type": "email", "dry_run": false}
```

Each request gets a short `correlation_id` for end-to-end tracing. Errors are logged at ERROR level with the exception message before re-raising.

The TypeScript webhook emits the same JSON format to stdout (info/debug) and stderr (warn/error).

---

## Risks and assumptions

**Assumptions:**
- OpenAI model responses are trusted to return valid JSON when `response_format: json_object` is set. A malformed response will cause a `json.JSONDecodeError` — caught and re-raised as a typed agent error.
- Email classification uses a fixed set of four categories. Emails that don't fit cleanly default to `general`.
- Document parsing is best-effort: missing fields produce warnings, not failures.

**What this does NOT handle (intentional scope limit for trial):**
- Authentication or rate limiting on the webhook endpoint
- Persistent storage or queueing of processed results
- Multi-page or binary (PDF) document input — text only
- Retry logic with backoff on OpenAI API failures
- Production secret management (use environment injection, not `.env` in prod)

**Data handling:**
- All sample data in `utils/mock_data.py` is entirely fictional
- `.env` is git-ignored; no credentials are committed
- The trial was completed using my own OpenAI account — no company credentials used or requested

---

## Tooling used

- Python 3.11+, OpenAI Python SDK v1.x
- pytest, unittest.mock
- TypeScript 5, Express 4, Zod 3, Jest 29
- Claude Code + Cursor (for acceleration — all output reviewed personally)
