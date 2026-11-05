# Finance contract DOM wave — 2026-11-05

Source baseline before edit: `69a43962c04ef3c72e952bbbdc2d40c3c6513df4`
Scope: disposable local synthetic runtime only; no reference writes.

## Reproduction

Runtime: `127.0.0.1:19019`, temporary DB `/tmp/center-edu-finance-dom-20261105.sqlite3`, local `CENTER_EDU_RICH_DEMO=1`, ADMIN login. Browser: system Google Chrome executable driven through app-owned `playwright-core` runtime; isolated context.

At `1440x900` and `390x844`, `/finance/contract` rendered 23 filter labels and 10 table rows. Reference screen spec records 23 observed filters, including paired select/search controls for course, course status, discount, payment, sale, creator. Therefore the paired controls are observed contract evidence, not independently classified as a defect.

Before fix, all four date filter controls were converted by shared `wireDateInputs` to native `type=date`, producing browser-native date UI. Reference spec records these filters as observed `type=text` with Vietnamese placeholders.

Route-owned fix: `static/app.js` adds `data-date-text="1"` to `/finance/contract` date filters; `wireDateInputs` keeps those inputs as text, preserves numeric input mode, formats existing ISO values as `dd/mm/yyyy`, and still parses submitted values through the existing `build` path.

## Post-fix local DOM proof

- Four date controls remained `type=text` at both viewports, with placeholders `Từ ngày tạo`, `Đến ngày tạo`, `Từ ngày hết hạn`, `Đến ngày hết hạn`.
- Initial table rows: `10`.
- Search/filter `HD-005` then `Lọc`: `1` row.
- `Xóa lọc`: `10` rows restored.
- Browser console retained one HTTP 404 for an unrelated optional resource; no source JS exception observed.
- Screenshots:
  - `/tmp/center-finance-fixed-1440.png` SHA-256 `eeef40bb65f87a8721f0effb1d71689854396d0ad5a988c61699401f17f4a5c6`
  - `/tmp/center-finance-fixed-390.png` SHA-256 `7cf2fab4a70a5bcbc14bfe425d432988d95e2ab22d99f391792b0d3855a3239d`

## Checks

- `node --check` across `static/*.js`: PASS.
- `test_generated_screen_projects_legacy_form_keys_to_observed_columns`: PASS.
- `test_health_and_public_shell`: PASS.
- `git diff --check`: PASS.

Reference equal-state screenshots, private API semantics, role parity, and full 134-route interaction coverage remain UNKNOWN. This report proves a local route fix and local behavior only.
