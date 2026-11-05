# Center EDU takeover checkpoint

Captured: 2026-11-05 (Asia/Ho_Chi_Minh)

## Roots and ownership

- `REA_ROOT`: `/Users/nam/orca/rea` (`morluto/rea`, `main`, clean at capture).
- `SOURCE_ROOT`: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`.
- `TARGET_ROOT`: same as `SOURCE_ROOT` for local verification; no deployment performed.
- `EVIDENCE_ROOT`: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild/docs/parity` plus timestamped evidence outside Git when needed.
- `SOURCE_ROOT` has no Git metadata. File SHA-256 snapshot: `/tmp/center-edu-source-snapshot-20261105.sha256` (308 files, excludes `data/`).

## Current implementation

Independent Python HTTP service with SQLite persistence, cookie sessions, PBKDF2 password hashing, CSRF, RBAC (`ADMIN`, `STAFF`, `TEACHER`, `STUDENT`), Vietnamese SPA-style frontend, module route stores, exports and audit records. It is an independent implementation; it does not proxy or embed the reference service.

## Baseline

- `python3 -m unittest discover -s . -p 'test_*.py' -q`: 107 tests passed.
- `python3 -m py_compile app.py screen_engine.py modules/*.py tests/*.py test_*.py`: passed.
- `node --check static/app.js && node --check static/nav-config.js`: passed.
- README contains historical claims of 70 tests and prior runtime receipts; those claims are not current-run evidence.

## Reference observation

Authenticated reference session opened at `https://demo.center.edu.vn/` with the user supplied demo credentials. Visible identity and role label were observed but are intentionally redacted from this repository. Observed top-level groups: Trang chủ, Tương tác, Đào tạo, CRM, Sale, Tài chính, Báo cáo, Khảo sát, CSO 4, Callcenter, Tài khoản, Thiết lập. Playwright inspected 18 representative routes across Training, CRM, Sale, Finance, Reports and account/setup; all returned HTTP 200 with authenticated content. Sanitized evidence: `plans/ref-survey-20261105.json`. Reference console issues remain recorded there.

## Safety boundary

Credentials, cookies, tokens and sensitive response bodies are excluded from this document and repository. Reference mutations require an explicit test marker and bounded cleanup; no payment, messaging, password change, bulk deletion, deployment or publication is authorized.
