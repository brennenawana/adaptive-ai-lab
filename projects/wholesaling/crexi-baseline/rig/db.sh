#!/usr/bin/env bash
# Local Postgres lifecycle for the baseline rig.
#   ./db.sh up       start the pinned container + create the schema (alembic head)
#   ./db.sh down     stop and remove it (data is in a named volume, kept)
#   ./db.sh nuke     remove container AND volume (full reset)
#   ./db.sh snapshot <name>   pg_dump the current state into runs/snapshots/
#   ./db.sh restore  <name>   restore a snapshot (drops and recreates the DB)
#   ./db.sh psql     interactive shell
set -euo pipefail

: "${CREXI_PG_CONTAINER:?source rig/env.sh first}"
: "${CREXI_PG_IMAGE:?source rig/env.sh first}"
: "${CREXI_PG_PORT:?source rig/env.sh first}"
ROOT="${CREXI_BASELINE_ROOT:?source rig/env.sh first}"
VOL="${CREXI_PG_CONTAINER}-data"
SNAPDIR="$ROOT/runs/snapshots"
PGURL_PLAIN="postgresql://wholesaling:wholesaling@localhost:${CREXI_PG_PORT}/wholesaling"
WHOLESALING="${WHOLESALING_REPO:-$HOME/code/wholesaling}"

case "${1:-}" in
up)
  if docker ps -a --format '{{.Names}}' | grep -qx "$CREXI_PG_CONTAINER"; then
    docker start "$CREXI_PG_CONTAINER" >/dev/null
  else
    docker run -d --name "$CREXI_PG_CONTAINER" \
      -e POSTGRES_USER=wholesaling -e POSTGRES_PASSWORD=wholesaling -e POSTGRES_DB=wholesaling \
      -p "${CREXI_PG_PORT}:5432" -v "${VOL}:/var/lib/postgresql/data" \
      "$CREXI_PG_IMAGE" >/dev/null
  fi
  printf 'waiting for postgres'
  for _ in $(seq 1 60); do
    if docker exec "$CREXI_PG_CONTAINER" pg_isready -U wholesaling -q 2>/dev/null; then break; fi
    printf '.'; sleep 1
  done
  echo
  docker exec "$CREXI_PG_CONTAINER" pg_isready -U wholesaling
  echo "-> $PGURL_PLAIN"
  ;;
schema)
  # Alembic is canonical. NOT `supabase db reset` -- supabase/migrations is ~112
  # revisions stale and would omit every crexi table.
  #
  # A fresh Postgres CANNOT run the chain unaided: revision id
  # "0052_source_health_coverage_ratio" is 33 chars and alembic_version.version_num
  # defaults to VARCHAR(32), so the upgrade dies with StringDataRightTruncation the
  # instant it stamps that revision. SQLite ignores VARCHAR length, so CI never sees
  # it. Every live env was widened by hand (issue #960; documented only in the
  # docstring of tests/test_alembic_migrations.py). We do the same, explicitly.
  docker exec -i "$CREXI_PG_CONTAINER" psql -U wholesaling -d wholesaling -q <<'SQL'
CREATE TABLE IF NOT EXISTS alembic_version (
  version_num VARCHAR(128) NOT NULL,
  CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128);
SQL
  echo "alembic_version.version_num widened to VARCHAR(128)"
  cd "$WHOLESALING/backend"
  DATABASE_URL="$DATABASE_URL" .venv/bin/python -m alembic upgrade head
  echo "alembic head applied"
  ;;
down)    docker stop "$CREXI_PG_CONTAINER" >/dev/null && echo "stopped" ;;
nuke)    docker rm -f "$CREXI_PG_CONTAINER" >/dev/null 2>&1 || true
         docker volume rm "$VOL" >/dev/null 2>&1 || true; echo "container + volume removed" ;;
snapshot)
  name="${2:?usage: db.sh snapshot <name>}"; mkdir -p "$SNAPDIR"
  docker exec "$CREXI_PG_CONTAINER" pg_dump -U wholesaling -Fc wholesaling > "$SNAPDIR/$name.dump"
  shasum -a 256 "$SNAPDIR/$name.dump" | tee "$SNAPDIR/$name.sha256"
  echo "snapshot -> $SNAPDIR/$name.dump"
  ;;
restore)
  name="${2:?usage: db.sh restore <name>}"
  docker exec -i "$CREXI_PG_CONTAINER" psql -U wholesaling -d postgres -q \
    -c "DROP DATABASE IF EXISTS wholesaling WITH (FORCE);" -c "CREATE DATABASE wholesaling OWNER wholesaling;"
  docker exec -i "$CREXI_PG_CONTAINER" pg_restore -U wholesaling -d wholesaling --no-owner < "$SNAPDIR/$name.dump"
  echo "restored $name"
  ;;
psql)    docker exec -it "$CREXI_PG_CONTAINER" psql -U wholesaling wholesaling ;;
*) sed -n '2,10p' "$0"; exit 2 ;;
esac
