# Center EDU local operations runbook

## Start

```bash
cd products/center-edu-rebuild
set -a; source ops/config.example.env; set +a
python3 app.py --host "$CENTER_EDU_HOST" --port "$CENTER_EDU_PORT"
```

Use a protected environment file for customer deployments. Never use the demo password in production.
Set `CENTER_EDU_COOKIE_SECURE=1` when the reverse proxy enforces HTTPS; leave it `0` only for loopback HTTP development.

## Health and liveness

```bash
curl -fsS "http://${CENTER_EDU_HOST}:${CENTER_EDU_PORT}/api/health"
```

The health response proves process reachability and SQLite selection only. It does not prove TLS, reverse proxy, customer identity, or production authorization.

## Optional macOS startup artifact

`center-edu.launchd.example.plist` is a redacted, install-ready template for a
customer-owned launchd service. It is not installed or loaded by this task. Before
installation, replace `/opt/center-edu-rebuild`, `/var/lib/center-edu` and the log
directory with protected customer paths, create those directories with the required
ownership, put secrets in the protected environment/secret mechanism, then validate
with `plutil -lint`. Loading or unloading the service is a deployment action and
requires the customer release gate.

## Backup

Set `CENTER_EDU_DB` to the live database path, then run:

```bash
CENTER_EDU_DB=/protected/path/center-edu.sqlite3 ./ops/backup.sh /protected/backup/center-edu.sqlite3
```

The script uses SQLite online backup and runs `PRAGMA integrity_check` on the copy. Keep backups outside the product checkout with restrictive permissions.
The script applies `umask 077` and enforces mode `0600` on the resulting backup.

## Restore rehearsal

1. Stop the service using the host process manager.
2. Copy the backup to a new database path; keep the original unchanged.
3. Run `python3 -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute("PRAGMA integrity_check").fetchone()[0])' <new-db>`.
4. Start a canary instance against the restored path on a private loopback port.
5. Check `/api/health`, login, RBAC and a read-only workflow before changing the configured database path.

A restore is a deployment/data operation and requires the customer owner gate.

## Live WAL recovery check (read-only)

When a running service reports a database I/O error, capture a candidate file
set without touching the live process:

```bash
CENTER_EDU_DB=/protected/path/center-edu.sqlite3 ./ops/primary-recovery-check.sh /protected/recovery/center-edu-snapshot
```

The command copies the main, WAL and shared-memory files and checks the copy. It
does not checkpoint, restart, replace, or mutate the source. A successful
snapshot is stored in a `0700` directory with `0600` files; it is preparation evidence; use the restore rehearsal during an
authorized restart window.

## Security checklist

- Store environment values in a protected secret mechanism.
- Keep SQLite and backups outside Git.
- Use TLS and an authenticated reverse proxy before external access.
- Keep `CENTER_EDU_ACCESS_LOG=0` unless logs are reviewed for sensitive fields.
- Rotate demo credentials before any customer use.
