# FIN-003 Finance date-filter error UX wave — 2026-11-05

## Scope

Route-owned local verification of the finance contract date-filter error seam after the FIN-002 date-input fix. This report does not promote reference parity, ordinary date-input behavior, or the global 134-route matrix.

## Prior finding

A mobile verifier screenshot exposed the backend validation text `date_from must be before or equal to date_to` directly in the Vietnamese toast. The backend contract remains authoritative: HTTP 400, `code=VALIDATION_ERROR`, and the raw machine-readable message must remain unchanged in the JSON response.

## Source change

`static/app.js` now maps the known date-filter validation messages at the UI seam:

- reversed range → `Ngày bắt đầu không được sau ngày kết thúc.`
- invalid ISO date → `Ngày bắt đầu không hợp lệ. Nhập theo định dạng dd/mm/yyyy.`
- unknown messages remain unchanged.

Current working-tree SHA-256: `84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302`.

## Bounded local smoke evidence

Disposable local runtime: `127.0.0.1:19023`; temporary SQLite database; runtime stopped cleanly. No reference writes or sensitive data.

- Initial state: 10 table rows; summary remained `86` contracts and the existing totals.
- Valid `05/11/2026`: date input stayed `type=text`, displayed `dd/mm/yyyy`; request query used `date_from=2026-11-05`; 2 local rows returned; clear restored 10 rows.
- Impossible `31/02/2026`: UI toast was Vietnamese; network returned HTTP 400 with `code=VALIDATION_ERROR`, raw message `date_from must be YYYY-MM-DD`; existing summary totals remained unchanged.
- Reversed `10/11/2026` → `01/11/2026`: UI toast was Vietnamese; network returned HTTP 400 with `code=VALIDATION_ERROR`, raw message `date_from must be before or equal to date_to`; existing summary totals remained unchanged in this run.
- No confirmed invalid-filter false-zero summary defect. The earlier screenshot observation is retained as unconfirmed pending independent reproduction.
- Mobile viewport `390x844` retained the horizontal table-scroll behavior in the captured run; desktop viewport was `1440x900`.

Structured network/DOM receipt and screenshots are in:

`plans/center-edu-rebuild-20261030/supervision-20261103/evidence/finance-error-ux-wave-20261105/`

Evidence SHA-256:

- `lead-desktop-1440x900.png`: `b7f8f1becc5f51208c8634e2e6c1aa64e3f8c1e7560f8dfe9291d8ea31806f22`
- `lead-mobile-390x844.png`: `7cf2fab4a70a5bcbc14bfe425d432988d95e2ab22d99f391792b0d3855a3239d`
- `network.json`: `980c72c32826c4f635539682caa1016e44e04d399b597459020a2ec9e87275d8`

## Independent verification

Pending `/root/qa_reviewer` verification against this final source edit. FIN-003 remains `IN_PROGRESS` until an independent report verifies the UI, backend response, summary behavior, and evidence hashes.

## Limits

Reference equal-state screenshots/private semantics, browser-host live parity, and the remaining 21 route/action UNKNOWN cells are outside this bounded local wave. Global status remains `PARTIAL / NOT_ACCEPTED`.
