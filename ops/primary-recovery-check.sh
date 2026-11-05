#!/usr/bin/env bash
set -euo pipefail
umask 077

# Read-only forensic snapshot for a live SQLite WAL database. This script never
# opens the source database for writes, checkpoints it, stops its process, or
# replaces any source file.
source_db="${CENTER_EDU_DB:-}"
if [[ -z "$source_db" ]]; then
  echo "CENTER_EDU_DB is required" >&2
  exit 2
fi
if [[ ! -f "$source_db" ]]; then
  echo "database not found: $source_db" >&2
  exit 2
fi

snapshot_dir="${1:-$(mktemp -d "${TMPDIR:-/tmp}/center-edu-recovery.XXXXXX")}"
mkdir -p "$snapshot_dir"
chmod 700 "$snapshot_dir"
snapshot_db="$snapshot_dir/$(basename "$source_db")"
cp -p "$source_db" "$snapshot_db"
chmod 600 "$snapshot_db"
for suffix in -wal -shm; do
  if [[ -f "${source_db}${suffix}" ]]; then
    cp -p "${source_db}${suffix}" "${snapshot_db}${suffix}"
    chmod 600 "${snapshot_db}${suffix}"
  fi
done

python3 - "$snapshot_db" <<'PY'
import json
import sqlite3
import sys
from pathlib import Path

path = Path(sys.argv[1])
result = {"snapshot": str(path), "source_mutated": False}
db = sqlite3.connect(str(path))
try:
    result["integrity_check"] = db.execute("PRAGMA integrity_check").fetchone()[0]
    result["users"] = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    result["tables"] = db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
finally:
    db.close()
print(json.dumps(result, sort_keys=True))
PY
