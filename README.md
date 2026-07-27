# SENTRY
> **An AI Execution Firewall for Autonomous Agents**

**AI Builders Challenge with IBM Bob — Wildcard Challenge: Intelligent Systems for the Future of Work**

SENTRY is a lightweight, real-time security firewall that sits between AI agents and external tools. It evaluates agent actions against strict safety rules, computes dynamic risk scores, leverages explainable AI reasoning, records comprehensive audit logs, and enforces human-in-the-loop approval workflows before high-risk actions are executed.

---

## Overview

As AI agents transition from passive chat assistants to autonomous systems capable of calling APIs, executing database queries, and modifying production systems:

- **The Core Problem**: Existing security frameworks focus on response generation safety (e.g. prompt guardrails) rather than governing real-world tool execution.
- **Uncontrolled Action Risk**: Autonomous agents can unintentionally trigger data loss, unauthorized payments, API rate limit breaches, or out-of-scope system calls.
- **The Solution — SENTRY**: SENTRY acts as an Execution Firewall proxy layer. Every tool request is intercepted, evaluated against safety policies, scored for risk, enriched with AI reasoning, and routed to `ALLOW`, `BLOCK`, or `CONFIRM` decisions before execution.

---

## Features

- 🛡️ **AI Execution Firewall**: Real-time evaluation and interception of agent tool call requests.
- 📋 **Rule-Based Policy Enforcement**: Multi-layer security rules enforcing scope boundaries, parameter safety, cost controls, rate limits, and irreversibility checks.
- 📊 **Risk Engine & Scoring**: Dynamic risk scoring algorithm (0–100) mapping severity weights to automated decision outcomes.
- 🚦 **Tri-State Decision Engine**:
  - `ALLOW`: Low-risk requests execute immediately.
  - `CONFIRM`: Medium-risk requests pause and require human reviewer approval.
  - `BLOCK`: High-risk or policy-violating requests are safely halted.
- 👤 **Human Approval Workflow**: Interactive approval queue allowing human operators to approve or reject pending execution requests with reviewer attribution.
- 🧠 **Explainable AI Reasoning**: Dedicated AI reasoning layer (`AIReasoner` interface, implemented by `GraniteReasoner`) producing human-readable explanations, identified policy violations, suggested fixes, and confidence scores.
- 📜 **Immutable Audit Logging**: Detailed execution metadata tracking (request payload, rule results, reasoning output, risk score, decision, execution latency, and timestamps).
- 📈 **Live Dashboard**: React/Vite security operations center UI backed by real REST endpoints - live audit feed, approval queue, policy management, and analytics.
- 🤖 **Real IBM Granite Integration**: `GraniteReasoner` calls watsonx.ai when credentials are configured, and falls back to a deterministic explanation otherwise so the pipeline always runs end to end.

---

## Architecture

```text
               ┌───────────────────────┐
               │       AI Agent        │
               └───────────┬───────────┘
                           │ Tool Request
                           ▼
               ┌───────────────────────┐
               │   SENTRY Middleware   │
               └───────────┬───────────┘
                           │
                           ▼
               ┌───────────────────────┐
               │      Rule Engine      │
               └───────────┬───────────┘
                           │ Evaluated Rules
                           ▼
               ┌───────────────────────┐
               │      Risk Engine      │
               └───────────┬───────────┘
                           │ Risk Score (0-100)
                           ▼
               ┌───────────────────────┐
               │      AI Reasoner      │
               │  (IBM Granite/watsonx │
               │   with mock fallback) │
               └───────────┬───────────┘
                           │ Structured Reasoning & Confidence
                           ▼
               ┌───────────────────────┐
               │    Decision Engine    │
               │ (ALLOW / CONFIRM /    │
               │        BLOCK)         │
               └───────────┬───────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
 ┌───────────────────────┐   ┌───────────────────────┐
 │     Audit Logging     │   │ Human Approval Queue  │
 └───────────┬───────────┘   └───────────┬───────────┘
             │                           │
             ▼                           ▼
 ┌───────────────────────┐   ┌───────────────────────┐
 │  PostgreSQL Database  │   │  Frontend Dashboard   │
 └───────────────────────┘   └───────────────────────┘
```

---

## Tech Stack

| Category | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS v4, shadcn/Radix UI |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, AsyncIO |
| **Database** | PostgreSQL 16, Async SQLAlchemy 2.0, Alembic Migrations |
| **AI Reasoning** | IBM Granite via watsonx.ai (`ibm-watsonx-ai` SDK), with a deterministic mock fallback when no credentials are configured |
| **Agent Protocol** | MCP (Model Context Protocol) demo server + client (`mcp_demo/`) |
| **DevOps & Testing** | Docker, Docker Compose, Pytest, Uvicorn |

---

## Repository Structure

```text
.
├── src/                         # SENTRY core backend source code
│   ├── api/                     # API routers and versioned endpoints (/api/v1)
│   ├── approval_requests/       # Approval workflow models & schemas
│   ├── audit_logs/              # Audit logging engine & models
│   ├── core/                    # App configuration, structured logging, exception handlers
│   ├── db/                      # Database engine, async session factory, base models
│   ├── execution/               # Rule Engine, Risk Engine, AI Reasoning layer & services
│   ├── health/                  # Service & database health monitoring router
│   ├── models/                  # Centralized SQLAlchemy model registry
│   ├── policies/                # Security policy models & schemas
│   └── main.py                  # FastAPI application entrypoint
├── Frontend/                    # React + Vite security operations center dashboard
│   └── src/app/                 # App.tsx (pages/components) + lib/api.ts (backend client)
├── mcp_demo/                    # Real MCP server + client agent demoing AI Agent → SENTRY → Tool
├── tests/                       # Automated test suite (Pytest)
├── alembic/                     # Database schema migration scripts
├── docker-compose.yml           # Multi-container orchestration (API + PostgreSQL)
├── Dockerfile                   # Production container definition
├── requirements.txt             # Dependency manifest
└── README.md                    # Project documentation
```

---

## API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/execute` | Evaluates tool call request through Rule & Risk engines, returns decision (`ALLOW`/`BLOCK`/`CONFIRM`), risk score, reasoning output, and audit ID. |
| `GET` | `/audit` | Retrieves paginated audit logs with filtering by agent, tool, decision, and risk threshold. |
| `GET` | `/stats` | Returns aggregated metrics for security dashboards (total executions, decision distribution, average risk, average latency). |
| `GET` | `/policies` | Lists all security policies (enabled and disabled) ordered by severity. |
| `PATCH` | `/policies/{policy_code}` | Enables or disables a security policy. |
| `POST` | `/approve/{id}` | Processes human reviewer approval or rejection for a pending `CONFIRM` request. |
| `GET` | `/health` | Health check endpoint reporting API service and PostgreSQL database connection status. |

*Full interactive OpenAPI documentation is available at `/docs` when running the application.*

---

## Running the Project

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- Python 3.12+ (for local development without Docker)
- Node.js 20+ and [pnpm](https://pnpm.io/) (for the dashboard)

### Backend Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/leishapm/sentry-ai.git
   cd sentry-ai
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   To enable real IBM Granite reasoning (instead of the deterministic mock fallback), set `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` in `.env`.

3. **Start the Service with Docker**:
   ```bash
   docker compose up --build
   ```
   *This starts the FastAPI backend server on `http://localhost:8000` and a healthy PostgreSQL 16 container on port `5432`.*

4. **Run Database Migrations** *(first run only)*:
   ```bash
   docker compose exec api alembic upgrade head
   ```

5. **Verify Backend Health**:
   ```bash
   curl http://localhost:8000/health
   ```

6. **Run Test Suite**:
   ```bash
   pytest
   ```

### Frontend Setup

The dashboard lives in `Frontend/` and talks to the API above.

```bash
cd Frontend
cp .env.example .env   # VITE_API_URL, defaults to http://localhost:8000
pnpm install
pnpm dev
```

Open `http://localhost:5173`. The dashboard pulls live audit/stats/policy data
from the backend on load (shown as `CONNECTED` in the header) and falls back
to demo data automatically if the backend isn't reachable (`DEMO DATA` badge).
Click **Run Demo** to fire real `POST /execute` requests through the rule
engine and AI reasoner end to end.

### MCP Demo (optional)

`mcp_demo/` demonstrates the same `AI Agent → SENTRY → Tool` flow over the
real Model Context Protocol, with the live backend as the policy checkpoint:

```bash
python -m mcp_demo.scenarios
```

---

## How IBM Bob Was Used

<!-- TODO (team): replace this with what actually happened. Required by the
     submission rules - be specific per person/component, not generic. -->

- **Backend & middleware** (Leisha): _fill in - which parts of `src/execution/`,
  `src/audit_logs/`, `src/approval_requests/`, the Docker/Alembic setup, etc.
  were built or accelerated with IBM Bob?_
- **Frontend dashboard**: _fill in - was the `Frontend/` UI generated or
  iterated on with IBM Bob?_
- **AI integration** (Rushika): _fill in - watsonx.ai/Granite wiring, the
  rule/reasoning/risk pipeline, MCP demo agent._

---
