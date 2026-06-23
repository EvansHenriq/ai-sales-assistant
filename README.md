# AI Sales Assistant

> AI assistant for **lead qualification**, **context analysis** and **service automation**
> in a B2B SaaS scenario. Built to showcase production-minded AI engineering:
> RAG, tool-using agents, structured outputs, evaluation, and security-first design.

🇧🇷 _Documentação bilíngue: a versão em português segue após a versão em inglês._

---

## Status

🚧 **Work in progress.** Built incrementally in phases (see the implementation plan).
Phase 0 (project scaffolding) is in place: configuration, structured logging, security
middleware, a health endpoint, Docker, and CI.

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL + **pgvector** · OpenAI ·
Alembic · structlog · Docker · GitHub Actions · uv

## Architecture (target)

A FastAPI service whose core is an **agent orchestrator**. Each lead message flows through:
input guardrails → RAG retrieval → OpenAI agent (function calling) → tools (knowledge search,
lead qualification, contact capture, demo scheduling) → output moderation → persistence.

Security is treated as a first-class concern across two layers: **application/infrastructure**
(API-key auth, secrets, input validation, rate limiting, least-privilege DB, hardened
container) and **LLM guardrails** (prompt-injection defense, output moderation, PII redaction).

## Local development

Requires [uv](https://docs.astral.sh/uv/) and (for the full stack) Docker.

```bash
# Install dependencies
uv sync

# Run the unit test suite (no database required)
uv run pytest -m "not integration"

# Lint, format check, type-check
uv run ruff check .
uv run ruff format --check .
uv run mypy app

# Run the full stack (app + PostgreSQL/pgvector)
cp .env.example .env   # then edit secrets
docker compose -f docker/docker-compose.yml up --build
# API docs at http://localhost:8000/docs
```

---

# 🇧🇷 Português

> Assistente de IA para **qualificação de leads**, **análise de contexto** e **automação de
> atendimento** em um cenário de SaaS B2B. Construído para demonstrar engenharia de IA com
> mentalidade de produção: RAG, agentes com ferramentas, saídas estruturadas, avaliação e
> design com segurança em primeiro lugar.

## Status

🚧 **Em desenvolvimento.** Construído de forma incremental, em fases. A Fase 0 (scaffolding)
já está pronta: configuração, logging estruturado, middleware de segurança, endpoint de
health, Docker e CI.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL + **pgvector** · OpenAI ·
Alembic · structlog · Docker · GitHub Actions · uv

## Como rodar localmente

Requer [uv](https://docs.astral.sh/uv/) e (para a stack completa) Docker.

```bash
uv sync
uv run pytest -m "not integration"      # testes unitários (sem banco)
docker compose -f docker/docker-compose.yml up --build   # stack completa
# Docs da API em http://localhost:8000/docs
```

## Licença

MIT.
