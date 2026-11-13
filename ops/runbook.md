# Center EDU local operations runbook

## Start

```bash
cd products/center-edu-rebuild
set -a; source ops/config.example.env; set +a
python3 app.py --host "$CENTER_EDU_HOST" --port "$CENTER_EDU_PORT"
```

Use a protected environment file for customer deployments. Never use the demo password in production.
Set `CENTER_EDU_COOKIE_SECURE=1` when the reverse proxy enforces HTTPS; leave it `0` only for loopback HTTP development.

## Production bootstrap (admin-only)

Use the explicit production switch for a new customer database:

```bash
export CENTER_EDU_PRODUCTION=1
export CENTER_EDU_ADMIN_PASSWORD_FILE=/protected/secrets/center-edu-admin-password
python3 app.py --host "$CENTER_EDU_HOST" --port "$CENTER_EDU_PORT" --db "$CENTER_EDU_DB" --production-bootstrap
```

The password source is `CENTER_EDU_ADMIN_PASSWORD`, then
`CENTER_EDU_ADMIN_PASSWORD_FILE`, then the one-time prompt opened by
`--production-bootstrap` when both are absent. There is no literal or default
production password. An empty database receives one `ADMIN` account only;
teacher, staff, student, branch, course, class, classroom, enrollment, and
generated demo rows are not created. Reopening a database that already has a
user is idempotent and does not overwrite users or customer data. The
`CENTER_EDU_RICH_DEMO=1` opt-in is ignored while production mode is active.
Back up the database before customer startup and keep the secret file outside
the checkout.

The ordinary local/demo startup path remains separate. Use
`CENTER_EDU_RICH_DEMO=1` only with a disposable database whose seed data may be
discarded.

## Production tenant and branch scope

Production bootstrap creates one empty tenant idempotently. It creates no
branch unless `CENTER_EDU_INITIAL_BRANCH_CODE` and
`CENTER_EDU_INITIAL_BRANCH_NAME` are supplied together (or the equivalent
`create_server(..., production_initial_branch_*)` arguments). The admin-only
`/api/branch-manager/branches` API and `/center/manager/index` screen support
create, rename, lock/unlock, list, and guarded delete. Duplicate codes return
`409`; a branch with manager assignments or mapped operational rows cannot be
deleted. Existing users and data are never overwritten during bootstrap.

The header branch selector reads the authenticated scope from
`/api/branch-manager/scope` and remembers the selected branch locally. Admin
and staff writes use the sole active branch by default; once multiple active
branches exist, the client must submit the selected `branch_id`. A production
database with no branch remains an admin setup state: student, class, teacher,
staff, and CRM writes fail closed with `BRANCH_REQUIRED` until an admin creates
or supplies a branch. Branch-manager reads and writes remain limited to mapped
rows in their assigned branches.

The verified student-to-class assignment flows are:

* Class creation: `POST /api/classes/workflow` with `course_id`, `code`,
  `name`, `teacher_id`, `sessions`, and `student_ids`. It creates the class,
  timetable rows, and enrollments atomically.
* Existing class: `GET /api/classes/{id}/students`,
  `POST /api/classes/{id}/enrollments` with `student_id` and optional
  `start_date`, `sessions_count`, `schedule`, and `note`, then
  `POST /api/classes/{id}/enrollments/{student_id}` for an explicit status
  transition. The UI route is `/training/class/student/list/{id}`; the class
  list exposes a `Học viên` action and the destination exposes `Ghi danh`,
  status tabs, `Excel`, and per-row status changes.

`students.class_codes` is display/text data only and does not create an
enrollment. Persisted local statuses are `ENROLLED`, `DROPPED`, and
`COMPLETED`; the observed `Bảo lưu` and `Chuyển lớp` tabs remain read-only
empty states until a separate domain contract is evidenced. Enrollment writes
require ADMIN, STAFF, or BRANCH_MANAGER, and both class and student scope are
checked for branch managers. TEACHER and STUDENT can read their permitted
scope but cannot mutate enrollment.

## r19b people and CRM writes

`/api/parents` and `/api/staff` are dedicated persisted APIs. ADMIN/STAFF may
create parents; ADMIN alone may create or edit staff accounts. Passwords are
provided per request and stored as hashes; no shared password is seeded. A
duplicate username, email, or parent/staff code returns `409`.

Parent, staff, and teacher edit responses expose `version` and `updated_at`.
Full-form edits require one of those tokens and use an atomic compare-and-
update; a stale form returns `409 CONFLICT` with a Vietnamese reload message.
Narrow PATCH-style writes remain merge-safe where the endpoint supports them.

Branch-manager assignments must reference existing branches and are validated
before the account is inserted. Explicit branch writes are scope-checked;
ordinary ADMIN/STAFF writes use the selected/default branch when one exists and
fail closed when a multi-branch or empty production scope is ambiguous.
Parent links are branch-safe: every linked student's persisted branch must
match the parent's selected branch on create and edit; a mismatch returns
`409 BRANCH_MISMATCH` and leaves both records unchanged.

Class reads intentionally remain tenant-wide for ADMIN and STAFF. Assigning a
staff account to branch A controls its branch-scoped writes, but does not hide
branch B classes from the class list. The ADMIN header branch selector also
does not narrow class reads; it supplies the branch for writes and exports.
This is the current observed policy, covered by the r19c branch tests.

## r19c class management

`/training/class/detail/{id}` is the verified class detail/edit route. It reads
the existing class record, sends the existing `version` or `updated_at` token
on full-form saves, and reports a Vietnamese conflict message with reload when
the token is stale. `POST /api/classes/{id}/close` changes the class to
`COMPLETED`; `POST /api/classes/{id}/cancel` changes it to `CANCELLED`. Both
require `apply_from`, an optimistic token, and ADMIN, STAFF, or an in-scope
BRANCH_MANAGER. The effective date persists in `status_apply_from` and each
transition writes an audit event. The transition endpoints return `404` for an
out-of-scope class and `403` for roles without lifecycle-write permission.

The class list exposes `Học viên`, `Lịch học`, and `Thời khóa biểu` paths. The
rebuild has no verified curriculum, skill-set, or assignment persistence
module, so those destinations remain explicitly marked not implemented rather
than rendered as no-op buttons. Parallel same-token updates are covered by
the r19c focused test and must produce one winner with `409 CONFLICT` for the
remaining writers.

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
