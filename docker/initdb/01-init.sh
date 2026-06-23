#!/bin/bash
# Runs once on first database initialization (local/dev via docker-compose).
# Production deployments should provision roles/secrets through their own secret
# management; this script encodes the least-privilege intent for local use.
set -euo pipefail

APP_DB_PASSWORD="${APP_DB_PASSWORD:-change-me-app}"

# Pass values as psql variables: %L-style quoting is handled by :'name' (literal)
# and :"name" (identifier). The init dir only runs on a fresh data volume, so the
# role does not yet exist and an unconditional CREATE ROLE is safe.
psql -v ON_ERROR_STOP=1 \
     -v app_password="${APP_DB_PASSWORD}" \
     -v dbname="${POSTGRES_DB}" \
     --username "${POSTGRES_USER}" \
     --dbname "${POSTGRES_DB}" <<-'EOSQL'
    -- Vector similarity search support for the RAG knowledge base.
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Least-privilege application role: can connect and run CRUD, but is not a
    -- superuser. Migrations (DDL) are run with the superuser separately.
    CREATE ROLE app LOGIN PASSWORD :'app_password';

    GRANT CONNECT ON DATABASE :"dbname" TO app;
    GRANT USAGE ON SCHEMA public TO app;

    -- Tables/sequences created later by migrations get CRUD but no DDL.
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO app;
EOSQL

echo "Database initialized: vector extension + least-privilege 'app' role."
