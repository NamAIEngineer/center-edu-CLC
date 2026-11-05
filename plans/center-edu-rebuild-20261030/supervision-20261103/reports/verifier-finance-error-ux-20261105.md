# VERIFY-06 Finance error UX — independent verification (2026-11-05)

## Scope
Independent browser verification of the current uncommitted `static/app.js` error-message mapping. No source edits. Disposable local runtime only (`127.0.0.1:19030`, SQLite `/tmp/center-edu-finance-error-verify-20261105.sqlite3`, password supplied through environment and not persisted here).

## Evidence
- Source SHA-256: `84923c34c69c035e96ae425b5bb6c697fe17d9a4d7aef022d596d6466717e302`
- Browser: Playwright 1.63.0, Google Chrome for Testing, viewports `1440x900` and `390x844`.
- Structured receipt: `plans/center-edu-rebuild-20261030/supervision-20261103/evidence/finance-error-ux-wave-20261105/independent-network.json`
- Receipt SHA-256: `fbc83919b131a5a3b990b23be725aabc41f74376d98dcb74949ea43db1d549ee`
- Screenshots: `desktop-1440x900.png`, `mobile-390x844.png` (captured in same evidence directory).

## Results

| Check | Result |
|---|---|
| Login and `/finance/contract` | PASS; seeded local admin session |
| Impossible `31/02/2026` | PASS; request `GET /api/finance/contracts?date_from=2026-02-31` returned HTTP 400 and raw JSON `date_from must be YYYY-MM-DD`; visible toast: `Ngày bắt đầu không hợp lệ. Nhập theo định dạng dd/mm/yyyy.` |
| Reversed `10/11/2026` → `01/11/2026` | PASS for final validation; final request returned HTTP 400 and raw JSON `date_from must be before or equal to date_to`; visible toast: `Ngày bắt đầu không được sau ngày kết thúc.` An intermediate input/change request with only `date_from` returned 200 and temporarily rendered 1 row before the final two-field request; this is existing listener behavior, not a source change in this task. |
| Summary preservation | PASS; summary remained `Số hợp đồng 86`, `Tạm tính 192.950.000 VND`, `Đã thanh toán 100.931.250 VND`, `Còn nợ 92.018.750 VND` after invalid and reversed requests. |
| Clear/reset | PASS; four date inputs cleared and table returned to 10 rows. |
| Date controls | PASS; four finance date controls are `type=text`, `data-date-text="1"`, Vietnamese placeholders. |
| Desktop overflow | PASS; document width matched viewport (`1440/1440`). |
| Mobile overflow | UNKNOWN in this runtime; document width matched viewport (`390/390`), while prior bounded evidence recorded table horizontal overflow. No parity promotion from this cell. |

## Verdict
`PASS_WITH_LIMITATIONS`. Current error UX mapping is independently verified for both known backend validation messages, with backend raw errors preserved and summary totals retained. Mobile table overflow requires separate confirmation because this run observed no document-level overflow.

Runtime processes stopped after capture.
