# SENTRY
> **An AI Execution Firewall for Autonomous Agents**

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
- 🧠 **Explainable AI Reasoning**: Dedicated AI reasoning layer (`AIReasoner` interface with IBM Granite-ready implementation) producing human-readable explanations, identified policy violations, suggested fixes, and confidence scores.
- 📜 **Immutable Audit Logging**: Detailed execution metadata tracking (request payload, rule results, reasoning output, risk score, decision, execution latency, and timestamps).
- 📈 **Dashboard-Ready APIs**: High-performance REST endpoints for security operations center (SOC) dashboards and monitoring.
- 🤖 **IBM Granite-Ready Architecture**: Clean, decoupled AI reasoning abstraction structured for seamless integration with IBM Granite / watsonx.ai models.

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
               │ (IBM Granite Ready)   │
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
| **Frontend** | Next.js, React, TypeScript, Tailwind CSS *(Dashboard integration)* |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, AsyncIO |
| **Database** | PostgreSQL 16, Async SQLAlchemy 2.0, Alembic Migrations |
| **AI Reasoning** | IBM Granite (watsonx.ai placeholder architecture), Custom Reasoning Protocol |
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
| `GET` | `/policies` | Lists active security policies ordered by severity. |
| `POST` | `/approve/{id}` | Processes human reviewer approval or rejection for a pending `CONFIRM` request. |
| `GET` | `/health` | Health check endpoint reporting API service and PostgreSQL database connection status. |

*Full interactive OpenAPI documentation is available at `/docs` when running the application.*

---

## Running the Project

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- Python 3.12+ (for local development without Docker)

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/sentry-ai.git
   cd sentry-ai
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```

3. **Start the Service with Docker**:
   ```bash
   docker compose up --build
   ```
   *This starts the FastAPI backend server on `http://localhost:8000` and a healthy PostgreSQL 16 container on port `5432`.*

4. **Verify Backend Health**:
   ```bash
   curl http://localhost:8000/health
   ```

5. **Run Test Suite**:
   ```bash
   pytest
   ```

6. **Frontend Setup** *(Placeholder for Dashboard UI)*:
   ```bash
   # Navigate to frontend directory once available
   # cd frontend && npm install && npm run dev
   ```

---

## Future Work

- 🤖 **Native IBM Granite Integration**: Connect `GraniteReasoner` directly to watsonx.ai IBM Granite model endpoints for live LLM policy reasoning.
- 🏢 **Enterprise Policy Management**: UI-driven policy editor with customizable rule expressions and role-based permissions.
- 🔗 **Multi-Agent Orchestration**: Multi-tenant policy scoping for agentic workflows across complex enterprise toolchains.
- 🔒 **OAuth2 & Role-Based Access Control**: Authentication layer for human approval workflows and admin dashboards.
- ☁️ **Cloud Infrastructure Deployment**: Helm charts and Terraform manifests for Kubernetes & GCP deployment.

---

## Team

- **Backend & AI Architecture**: Team Member 1
- **Frontend & UI/UX**: Team Member 2
- **Product & DevOps**: Team Member 3

---

## License

This project is licensed under the [MIT License](LICENSE).
