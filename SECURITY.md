# Security

Security is a first-class concern in this project. This document summarizes the
threat model and the controls implemented across two layers: application/
infrastructure and LLM-specific guardrails.

## Threat model (high level)

| Asset | Threats considered |
|---|---|
| Lead PII (email, phone, etc.) | Leakage through logs; unauthorized access |
| The assistant's behavior | Prompt injection / jailbreak; unsafe output |
| The API | Unauthenticated access; abuse / DoS via volume |
| The database | SQL injection; over-privileged access; DDL by the app |
| Secrets (API keys, DB creds) | Accidental commit; exposure in images |

## Application & infrastructure controls

- **Authentication** — every non-health endpoint requires an API key
  (`X-API-Key`). Keys are stored only as SHA-256 hashes and compared in constant
  time ([app/core/security.py](app/core/security.py)). The missing-key path
  returns 401 without touching the database.
- **Input validation** — all request bodies are strict Pydantic models.
- **SQL injection** — data access goes exclusively through the SQLAlchemy ORM
  with parameterized queries; no string-built SQL.
- **Least-privilege database** — the application connects as a non-superuser
  `app` role with CRUD-only grants. Schema migrations (DDL) run separately with
  the superuser via a one-shot `migrate` service
  ([docker/docker-compose.yml](docker/docker-compose.yml),
  [docker/initdb/01-init.sh](docker/initdb/01-init.sh)).
- **Rate limiting** — per-API-key (IP fallback) limits via slowapi; exceeding
  the quota returns 429 (covered by a test).
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, a strict `Content-Security-Policy` and `Cache-Control` on
  every response ([app/core/middleware.py](app/core/middleware.py)).
- **CORS** — restricted to configured origins; credentials disabled.
- **Container hardening** — multi-stage build, runs as a non-root user, drops
  all Linux capabilities, `no-new-privileges`, and a healthcheck
  ([docker/Dockerfile](docker/Dockerfile)).
- **Secrets management** — secrets come only from the environment
  (`pydantic-settings`); `.env` is git-ignored and `.env.example` is the
  template. The OpenAI key is wrapped in `SecretStr` so it cannot leak via repr.

## LLM-specific guardrails

- **Prompt-injection defense** — user content is always passed as data, never as
  instructions (role separation in [app/agent/prompts.py](app/agent/prompts.py)).
  A heuristic detector flags known injection phrasings and appends a defense note
  to the system prompt ([app/guardrails/prompt_injection.py](app/guardrails/prompt_injection.py)).
- **PII redaction** — a masked copy of user messages (emails, phones, credit
  cards, CPF) is stored for logs/analytics; raw contact data lives only in the
  `leads` table ([app/guardrails/pii.py](app/guardrails/pii.py)).
- **Output moderation** — assistant replies are checked with the OpenAI
  moderation endpoint; flagged content is replaced with a safe fallback
  ([app/guardrails/moderation.py](app/guardrails/moderation.py)).

These guardrails are measured by the eval harness (`python -m evals.run`): the
injection and PII suites are deterministic and score on curated datasets.

## CI security scanning

The GitHub Actions pipeline runs on every push/PR:

- **bandit** — static analysis (SAST) of the application code.
- **pip-audit** — dependency vulnerability scanning.
- **gitleaks** — secret scanning across history.

## Known limitations

- PII/injection detectors are pragmatic regex/heuristics, not exhaustive; a
  dedicated model classifier or a library such as Presidio could be layered on.
- Rate limiting uses in-memory storage; production should use a shared store
  (e.g. Redis).
- The bundled knowledge base and credentials are fictional/dev defaults.

## Reporting

This is a portfolio project. For real deployments, report vulnerabilities
privately to the maintainer rather than via public issues.
