#!/usr/bin/env bash
set -euo pipefail
umask 077

source_db="${CENTER_EDU_DB:-}"
if [[ -z "$source_db" ]]; then
  echo "CENTER_EDU_DB is required" >&2
  exit 2
fi
if [[ ! -f "$source_db" ]]; then
  echo "database not found: $source_db" >&2
  exit 2
fi
backup_path="${1:-${source_db}.backup-$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ -e "$backup_path" ]]; then
  echo "backup destination already exists; refusing overwrite: $backup_path" >&2
  exit 3
fi
mkdir -p "$(dirname "$backup_path")"
python3 - "$source_db" "$backup_path" <<'PY'
import sqlite3
import sys
src, dst = sys.argv[1:]
source = sqlite3.connect(src)
target = sqlite3.connect(dst)
try:
    source.backup(target)
    result = target.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise SystemExit(f"backup integrity check failed: {result}")
finally:
    target.close()
    source.close()
print(dst)
PY
chmod 600 "$backup_path"
