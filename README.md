# AI Sales Assistant

> A security-first AI sales assistant for **lead qualification**, **context
> analysis** and **service automation** in a B2B SaaS scenario. Built to
> demonstrate production-minded AI engineering: RAG, structured outputs,
> evaluation, and defense-in-depth.

🇧🇷 _A versão em português está no final._

---

## What it does

An API where a prospect chats with **Aria**, the assistant for a (fictional) SaaS
analytics product called **FlowMetrics**. Each turn is grounded in a knowledge
base, defended by guardrails, and can drive real actions — capturing the lead,
qualifying it (BANT) and scheduling a demo.

## Highlights

- **RAG grounding** — answers are grounded in a knowledge base using
  PostgreSQL + **pgvector** similarity search.
- **Structured lead qualification** — BANT scoring via OpenAI structured outputs
  (Pydantic), persisted and queryable.
- **Service automation** — capture lead contact and schedule demos.
- **Security guardrails** — prompt-injection detection, PII redaction for logs,
  and output moderation. See [SECURITY.md](SECURITY.md).
- **Evaluation harness** — offline suites with metrics (`python -m evals.run`);
  the deterministic guardrail suites run without an API key.
- **Engineering rigor** — typed (mypy strict), tested (pytest), linted (ruff),
  scanned (bandit / pip-audit / gitleaks), containerized and CI-gated.

## Architecture

A FastAPI service whose core is an agent **orchestrator**. A turn flows through:

```
client ──▶ API (auth + rate limit + validation)
             │
             ▼
        Orchestrator
   ┌─────────┼───────────────────────────────┐
   ▼         ▼              ▼                  ▼
 input     RAG          OpenAI            output
 guardrails retrieval   generation        moderation
 (injection (pgvector)  (Responses API)   (safe fallback)
  + PII)        │
               persist (messages, leads, qualifications, bookings)
```

Modules have single responsibilities and talk through small protocols
(`LLMClient`, `Retriever`, `Embedder`, `ModerationClient`), so the OpenAI SDK,
the vector store and moderation are all swappable and mockable in tests.

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL + **pgvector** ·
Alembic · OpenAI · structlog · slowapi · Docker · GitHub Actions · **uv**

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness (public) |
| POST | `/v1/conversations` | Create a conversation |
| GET | `/v1/conversations/{id}` | Get a conversation + messages |
| POST | `/v1/conversations/{id}/messages` | Send a message → grounded, guarded reply |
| POST | `/v1/conversations/{id}/qualify` | Qualify the lead (BANT) |
| GET | `/v1/conversations/{id}/qualification` | Latest qualification |
| POST | `/v1/conversations/{id}/lead` | Capture / update lead contact |
| POST | `/v1/conversations/{id}/schedule-demo` | Schedule a demo |

All `/v1` endpoints require an `X-API-Key` header. Interactive docs at `/docs`.

## Quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/), Docker, and an OpenAI API key.

```bash
# 1. Configure
cp .env.example .env          # set OPENAI_API_KEY (and review the rest)

# 2. Start the stack (Postgres + pgvector, migrations, API)
docker compose -f docker/docker-compose.yml up --build
#    API docs: http://localhost:8000/docs

# 3. Seed the knowledge base and create an API key (in another shell)
uv run python scripts/seed_knowledge.py
uv run python scripts/create_api_key.py "demo"      # prints the key once

# 4. Run the end-to-end demo conversation
uv run python scripts/demo_conversation.py --api-key <KEY>
```

### Running without an OpenAI key

Live inference uses OpenAI, so the chat/qualification demo needs a funded
`OPENAI_API_KEY` (bring your own). Everything that does **not** depend on live
inference runs for free: the full test suite and the deterministic guardrail eval
suites (they mock the model), plus browsing the API contract at `/docs`. The LLM
provider sits behind small protocols, so an alternative provider could be added
without touching the rest of the app.

## Evaluation

```bash
uv run python -m evals.run
```

Runs offline suites and writes `evals/reports/report.json`. The **guardrails**
suites (prompt-injection detection, PII redaction) are deterministic and run
without a key; the **qualification** and **RAG** suites run when an API key (and,
for RAG, a seeded database) are configured.

## Development

```bash
uv sync
uv run pytest -m "not integration"   # unit + db tests (in-memory SQLite)
uv run ruff check . && uv run ruff format --check .
uv run mypy app
uv run bandit -c pyproject.toml -r app
```

Integration tests (marked `integration`) need PostgreSQL/pgvector and run in CI.

## Project structure

```
app/         core · api · agent · rag · qualification · guardrails · db
migrations/  Alembic migrations
data/        fictional FlowMetrics knowledge base
evals/       metrics, suites, datasets, runner
scripts/     seed / create-key / demo
docker/      Dockerfile, compose, db init
tests/       unit · db (SQLite) · agent · qualification · guardrails · evals · integration
```

## License

MIT.

---

# 🇧🇷 Português

> Assistente de IA com **segurança em primeiro lugar** para **qualificação de
> leads**, **análise de contexto** e **automação de atendimento** num cenário de
> SaaS B2B. Demonstra engenharia de IA com mentalidade de produção: RAG, saídas
> estruturadas, avaliação e defesa em camadas.

## O que faz

Uma API onde um prospect conversa com a **Aria**, assistente de um produto SaaS
de analytics (fictício) chamado **FlowMetrics**. Cada turno é fundamentado numa
base de conhecimento, defendido por guardrails, e pode disparar ações reais —
capturar o lead, qualificá-lo (BANT) e agendar uma demo.

## Destaques

- **RAG** — respostas fundamentadas via PostgreSQL + **pgvector**.
- **Qualificação estruturada (BANT)** — saídas estruturadas da OpenAI (Pydantic),
  persistidas e consultáveis.
- **Automação** — captura de contato do lead e agendamento de demos.
- **Guardrails de segurança** — detecção de prompt-injection, redação de PII nos
  logs e moderação de saída. Ver [SECURITY.md](SECURITY.md).
- **Eval harness** — suites offline com métricas (`python -m evals.run`); as
  suites determinísticas de guardrails rodam sem chave de API.
- **Rigor de engenharia** — tipado (mypy strict), testado (pytest), lint (ruff),
  scans (bandit / pip-audit / gitleaks), containerizado e com CI.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL + **pgvector** ·
Alembic · OpenAI · structlog · slowapi · Docker · GitHub Actions · **uv**

## Como rodar

Pré-requisitos: [uv](https://docs.astral.sh/uv/), Docker e uma chave da OpenAI.

```bash
cp .env.example .env          # defina OPENAI_API_KEY
docker compose -f docker/docker-compose.yml up --build   # sobe Postgres + API
# Docs da API: http://localhost:8000/docs

uv run python scripts/seed_knowledge.py                 # popula o RAG
uv run python scripts/create_api_key.py "demo"          # imprime a chave uma vez
uv run python scripts/demo_conversation.py --api-key <CHAVE>   # demo completa
```

## Testes e avaliação

```bash
uv run pytest -m "not integration"   # testes locais (SQLite em memória)
uv run python -m evals.run           # suites de avaliação + relatório
```

## Licença

MIT.
