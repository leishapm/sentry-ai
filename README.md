# SENTRY Backend

SENTRY is an AI Execution Firewall. It will sit between AI agents and external tools, inspect every proposed tool request, and eventually return one of three decisions: `ALLOW`, `BLOCK`, or `CONFIRM`.

This repository currently contains the backend foundation only. Business logic, frontend code, and IBM Granite integration are intentionally not implemented yet.

## What Was Built

### Application Structure

```text
.
├── alembic/                 # Database migration environment.
│   ├── env.py               # Alembic runtime configuration.
│   ├── script.py.mako       # Template for generated migration files.
│   └── versions/            # Generated migration revisions live here.
├── src/                     # Importable application source code.
│   ├── api/                 # API route aggregation and versioning.
│   ├── core/                # Cross-cutting app infrastructure.
│   ├── db/                  # SQLAlchemy engine, sessions, and base classes.
│   ├── health/              # Health-check endpoint module.
│   ├── models/              # SQLAlchemy model registry for Alembic discovery.
│   └── main.py              # FastAPI app factory and ASGI entrypoint.
├── tests/                   # Automated tests.
├── docker-compose.yml       # Local API and PostgreSQL stack.
├── Dockerfile               # Production-style API container image.
├── requirements.txt         # Python dependencies.
├── alembic.ini              # Alembic CLI configuration.
└── .env.example             # Example environment variables.
```

### Why Each Folder Exists

`src/` keeps application code isolated from repo-level tooling, Docker files, and tests. This makes imports predictable and scales cleanly as the backend grows.

`src/api/` owns HTTP routing composition. The `v1` subfolder is ready for versioned endpoints so future API changes can be introduced without breaking old clients.

`src/core/` holds shared infrastructure that many modules will need: configuration, logging, security settings later, feature flags later, and other app-wide utilities.

`src/db/` owns database infrastructure: SQLAlchemy metadata, the async engine, session factory, and dependency used by routes or services that need database access.

`src/health/` is a tiny standalone endpoint module. Keeping it separate prevents operational routes from being mixed with future SENTRY business domains.

`src/models/` is the import registry Alembic uses to discover SQLAlchemy models. It is empty by design until business tables are added.

`alembic/` contains migration code. Database schema changes should go through migrations instead of manual SQL.

`alembic/versions/` stores generated migration files. It contains `.gitkeep` so Git tracks the folder before migrations exist.

`tests/` contains automated tests. The first test locks in the `/health` contract.

### Why Each File Exists

`.env.example` documents the environment variables needed to run the backend locally or in Docker.

`.dockerignore` keeps local caches, virtual environments, and secrets out of Docker build context.

`Dockerfile` builds the FastAPI API image.

`docker-compose.yml` starts the API plus a PostgreSQL database with a health check and persistent volume.

`requirements.txt` lists runtime and test dependencies using pip-compatible packaging.

`alembic.ini` configures Alembic’s script location, migration filename format, and logging.

`alembic/env.py` connects Alembic to the app settings and SQLAlchemy metadata.

`alembic/script.py.mako` defines the template Alembic uses when generating migration files.

`src/main.py` creates the FastAPI app, configures CORS, installs routers, hides docs in production, and logs startup.

`src/core/config.py` loads typed settings from environment variables and `.env`.

`src/core/logging.py` centralizes Python logging configuration.

`src/db/base.py` defines the SQLAlchemy declarative base, naming conventions, and timestamp mixin for future models.

`src/db/session.py` creates the async SQLAlchemy engine and per-request session dependency.

`src/api/router.py` gathers all application routers.

`src/api/v1/router.py` is the future home for versioned API routes.

`src/health/router.py` implements `GET /health`.

`src/health/schemas.py` defines the Pydantic response model for the health endpoint.

`src/models/__init__.py` gives Alembic one stable place to import future SQLAlchemy models.

`tests/test_health.py` verifies the app boots and `/health` returns the expected response.

## Local Development

1. Create an environment file:

```bash
cp .env.example .env
```

2. Start the local stack:

```bash
docker compose up --build
```

3. Open the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "SENTRY API",
  "environment": "local",
  "version": "0.1.0"
}
```

## Database And Migrations

The backend uses PostgreSQL through SQLAlchemy’s async engine:

```text
DATABASE_URL=postgresql+asyncpg://sentry:sentry_password@db:5432/sentry
```

When models are added later, create a migration with:

```bash
alembic revision --autogenerate -m "add firewall tables"
```

Apply migrations with:

```bash
alembic upgrade head
```

No business tables exist yet, so there is no initial schema migration.

## Run Tests

```bash
pytest
```
