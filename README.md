# SENTRY

**An AI execution firewall for autonomous agents.**

Built for the **AI Builders Challenge** with the **IBM Bob wildcard challenge**.

SENTRY sits between an AI agent and the tools it wants to call. Before a tool call reaches a database, payment API, email service, shell runner, or MCP tool server, SENTRY evaluates the request against policy rules, calculates a risk score, adds explainable IBM Granite-ready reasoning, records an audit trail, and returns one of three decisions: `ALLOW`, `CONFIRM`, or `BLOCK`.

## Why It Exists

Modern AI agents are moving from chat-only assistants to systems that can take real actions. That creates a new control problem: the dangerous part is often not what the model says, but what the model does.

SENTRY provides a lightweight checkpoint for those actions:

- Prevent agents from using tools outside their allowed scope.
- Detect sensitive parameters such as tokens, passwords, API keys, and secrets.
- Flag high-cost, high-volume, or irreversible actions.
- Route medium-risk actions to human approval instead of executing blindly.
- Store every decision with request payloads, rule results, reasoning, timestamps, and latency.
- Demonstrate how a real MCP tool flow can be protected by an execution firewall.

## Core Features

- **Execution firewall API** - FastAPI service that evaluates proposed agent tool calls in real time.
- **Rule engine** - Scope, parameter safety, rate limit, cost, and irreversible-action checks.
- **Risk engine** - Converts failed rule severities into a 0-100 risk score.
- **Tri-state decisions** - `ALLOW` for low risk, `CONFIRM` for review, `BLOCK` for high-risk violations.
- **Human approval workflow** - Creates approval requests for confirmable actions and supports reviewer decisions.
- **IBM Granite-ready reasoning** - Uses watsonx.ai credentials when configured, with a deterministic fallback for local demos.
- **Audit logging** - Persists execution history, rule output, reasoning, and approval state in PostgreSQL.
- **SOC-style dashboard** - Vite + React frontend for live requests, approvals, policies, audit logs, and analytics.
- **MCP demo** - A real MCP client/server demo where SENTRY gates calls before they reach mock enterprise tools.

## Architecture

```text
AI Agent
   |
   | proposed tool call
   v
SENTRY API
   |
   +--> Rule Engine
   |       - scope boundary
   |       - sensitive parameters
   |       - request volume
   |       - cost threshold
   |       - irreversible action confirmation
   |
   +--> Risk Engine
   |       - severity-weighted score from 0 to 100
   |
   +--> Reasoning Layer
   |       - IBM Granite / watsonx.ai when configured
   |       - local deterministic fallback otherwise
   |
   +--> Decision
   |       - ALLOW: request may execute
   |       - CONFIRM: pause for human approval
   |       - BLOCK: do not execute
   |
   +--> PostgreSQL Audit Log
   |
   v
Dashboard / MCP Agent / External Integrations
```

## Tech Stack

| Area | Stack |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic v2, Async SQLAlchemy |
| Database | PostgreSQL 16, Alembic |
| AI reasoning | IBM watsonx.ai / Granite-ready integration with local fallback |
| Frontend | Vite, React, TypeScript, Tailwind CSS, Radix UI, MUI, Recharts |
| Agent demo | Model Context Protocol (MCP), httpx |
| Testing | Pytest, pytest-asyncio |
| Runtime | Docker, Docker Compose, Uvicorn |

## Repository Layout

```text
.
|-- src/
|   |-- api/                  # API router wiring
|   |-- approval_requests/    # Human approval data model and schemas
|   |-- audit_logs/           # Execution audit model
|   |-- core/                 # Config, enums, logging, exception handlers
|   |-- db/                   # Async SQLAlchemy session and base model
|   |-- execution/            # Rule engine, risk engine, reasoning, services, routes
|   |-- health/               # Health endpoint
|   `-- main.py               # FastAPI app entrypoint
|-- Frontend/                 # Vite React dashboard
|-- mcp_demo/                 # MCP client/server demo protected by SENTRY
|-- alembic/                  # PostgreSQL migrations and seed policies
|-- tests/                    # Backend test suite
|-- docker-compose.yml        # API + PostgreSQL local stack
|-- Dockerfile
`-- requirements.txt
```

## Quick Start

### 1. Start the backend stack

```bash
docker compose up --build
```

In a second terminal, apply the database migration:

```bash
docker compose exec api alembic upgrade head
```

The API runs at:

- `http://localhost:8000`
- `http://localhost:8000/docs` for OpenAPI docs
- `http://localhost:8000/health` for service and database health

### 2. Start the dashboard

```bash
cd Frontend
npm install
npm run dev
```

The frontend uses `VITE_API_URL` when provided and otherwise defaults to `http://localhost:8000`.

Vite normally serves the dashboard at `http://localhost:5173`.

### 3. Run the MCP demo

With the backend running and migrated:

```bash
python -m mcp_demo.scenarios
```

The demo starts a real MCP tool server and routes proposed tool calls through SENTRY first. Only `ALLOW` decisions reach the MCP tool server.

## Local Backend Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start PostgreSQL with Docker:

```bash
docker compose up db
```

Apply migrations and run the API:

```bash
alembic upgrade head
uvicorn src.main:app --reload
```

Default local database URL:

```text
postgresql+asyncpg://sentry:sentry_password@localhost:5432/sentry
```

When running the frontend against a non-Docker backend, include the Vite origin in CORS:

```bash
CORS_ORIGINS=http://localhost:5173 uvicorn src.main:app --reload
```

## Configuration

Settings are loaded from environment variables or a local `.env` file.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `SENTRY API` | Service name shown in health responses |
| `ENVIRONMENT` | `local` | `local`, `staging`, or `production` |
| `LOG_LEVEL` | `INFO` | Backend logging level |
| `DATABASE_URL` | local Postgres URL | Async SQLAlchemy database connection |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed frontend origins |
| `WATSONX_API_KEY` | empty | Enables live watsonx.ai reasoning when set |
| `WATSONX_PROJECT_ID` | empty | Required with `WATSONX_API_KEY` |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | watsonx.ai endpoint |
| `WATSONX_MODEL_ID` | `ibm/granite-3-8b-instruct` | Granite model used by the reasoner |

If watsonx.ai credentials are not configured, SENTRY still works locally using the deterministic Granite-style fallback reasoner.

## API Overview

The same execution routes are available at the root path and under `/api/v1`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/execute` | Evaluate a proposed tool call and create an audit log |
| `GET` | `/audit` | List audit entries with optional filters |
| `GET` | `/stats` | Return dashboard summary metrics |
| `GET` | `/policies` | List seeded security policies |
| `PATCH` | `/policies/{policy_code}` | Enable or disable a policy |
| `POST` | `/approve/{approval_request_id}` | Approve or reject a pending request |
| `GET` | `/health` | Check API and database health |

### Example: Allowed Request

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "Inventory Agent",
    "tool_name": "read_inventory",
    "action": "Check stock for SKU-1024",
    "requested_scope": "inventory_read",
    "allowed_scopes": ["inventory_read"],
    "parameters": { "sku": "SKU-1024" }
  }'
```

Expected result: `ALLOW` with a low risk score.

### Example: Confirmation Request

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "Sales Assistant",
    "tool_name": "delete_customer",
    "action": "Delete customer record 134",
    "requested_scope": "customer_write",
    "allowed_scopes": ["customer_write"],
    "is_irreversible": true,
    "parameters": { "customer_id": 134 }
  }'
```

Expected result: `CONFIRM`, plus an `approval_request_id` that can be passed to `/approve/{approval_request_id}`.

### Example: Blocked Request

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "Sales Assistant",
    "tool_name": "update_pricing",
    "action": "Set SKU-1024 price to $0.01",
    "requested_scope": "pricing_write",
    "allowed_scopes": ["inventory_read", "customer_read"],
    "is_irreversible": true,
    "parameters": { "sku": "SKU-1024", "new_price": 0.01 }
  }'
```

Expected result: `BLOCK`, because the requested scope is outside the allowed scopes and the action is irreversible without prior confirmation.

## Decision Logic

SENTRY evaluates each request with independent policy checks. Failed checks add risk based on severity:

| Severity | Weight |
| --- | ---: |
| `LOW` | 10 |
| `MEDIUM` | 25 |
| `HIGH` | 45 |
| `CRITICAL` | 70 |

Final decision thresholds:

| Risk score | Decision |
| ---: | --- |
| `0-30` | `ALLOW` |
| `31-70` | `CONFIRM` |
| `71-100` | `BLOCK` |

## Testing

```bash
pytest
```

The tests cover health checks, models, rule/risk behavior, reasoning fallback behavior, and execution routes.

## IBM Bob Wildcard Challenge

SENTRY is positioned for the IBM Bob wildcard challenge as an "intelligent systems for the future of work" project: it gives teams a way to deploy autonomous agents without giving those agents unchecked authority over enterprise tools.

The IBM-aligned parts of the project are:

- IBM Granite-ready reasoning through the watsonx.ai SDK.
- Enterprise governance patterns: policy enforcement, auditability, approvals, and risk scoring.
- MCP-based tool protection, showing how agents can be intercepted before performing real work.
- A dashboard workflow for operators who need to inspect, approve, reject, and tune agent behavior.

## Challenge Summary

For the **AI Builders Challenge** and **IBM Bob wildcard challenge**, SENTRY demonstrates a practical safety layer for agentic systems:

- It does not try to make every agent perfect.
- It assumes agents will attempt risky actions.
- It makes those actions observable, explainable, auditable, and controllable before execution.

That makes SENTRY useful as a foundation for enterprise AI agents that need governance around tools, data, payments, infrastructure, communications, and other high-impact actions.
