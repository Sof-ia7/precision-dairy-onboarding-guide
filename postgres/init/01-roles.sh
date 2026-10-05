#!/bin/sh
# Runs once, when the PostgreSQL data volume is first created.
# - creates the schema used by the pipeline (owned by POSTGRES_USER, the writer)
# - creates a read-only role for Grafana that can SELECT every table the pipeline
#   creates now or later (the loader drops and recreates tables on each run).
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE SCHEMA IF NOT EXISTS ${POSTGRES_SCHEMA:-dairy} AUTHORIZATION "$POSTGRES_USER";
CREATE ROLE ${GRAFANA_DB_USER:-grafana_reader} LOGIN PASSWORD '${GRAFANA_DB_PASSWORD}';
GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO ${GRAFANA_DB_USER:-grafana_reader};
GRANT USAGE ON SCHEMA ${POSTGRES_SCHEMA:-dairy} TO ${GRAFANA_DB_USER:-grafana_reader};
GRANT SELECT ON ALL TABLES IN SCHEMA ${POSTGRES_SCHEMA:-dairy} TO ${GRAFANA_DB_USER:-grafana_reader};
ALTER DEFAULT PRIVILEGES FOR ROLE "$POSTGRES_USER" IN SCHEMA ${POSTGRES_SCHEMA:-dairy}
  GRANT SELECT ON TABLES TO ${GRAFANA_DB_USER:-grafana_reader};
SQL
