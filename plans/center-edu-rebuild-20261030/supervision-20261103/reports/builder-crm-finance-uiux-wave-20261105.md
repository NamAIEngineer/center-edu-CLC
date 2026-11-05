# CRM / Finance / Survey / Setup UI UX wave — 2026-11-05

Scope stayed within owned static modules. No app shell, CSS, backend, credentials, reference data, or external state changed.

## Fixed findings

| ID / repro | Expected | Actual before | Severity | File | After evidence |
|---|---|---|---|---|---|
| UI-FIN-01: open `/dashboard/finance`, activate “Trang chủ tài chính” | Home control has an accessible name and performs a route-safe navigation | Button had no accessible name and no event handler (dead action) | P1 | `static/modules/finance_dashboard.js` | Added `aria-label`, history navigation, `popstate` dispatch. SHA-256 `aa352928368d5261eeb088dedc907870e8353964203e78f9a3f0c6ffe61b44bf` |
| UI-FIN-02: open `/finance/history_move_student`, inspect filters | Status/date/table controls include page size, export, and usable paging | Status label was generic “Tất cả”; no page-size/export/paging controls; query dropped pagination | P1 | `static/modules/finance_history_move.js` | Added explicit status label, page-size selector, export action, prev/next controls, `page`/`page_size` query propagation. SHA-256 `92ef1a0cee8a7e87c2cf76f9f6fb8bbe18cc1b90c21f9d35bf06e724605073e4` |
| UI-SUR-01: open `/survey`, activate header actions | Create/statistics/results buttons have deterministic actions | Three buttons were rendered without IDs or listeners (dead icons/actions) | P1 | `static/modules/survey.js` | Added IDs and route-safe `popstate` navigation to create/statistics/results. SHA-256 `7503c5f1174dcaf04f9517b6db32fddb134a4e848cb5f9fceb003354ae053609` |
| UI-SET-01: inspect setup/address utility copy | Vietnamese labels are correctly spelled and consistent | Setup copy contract did not expose corrected address/export labels; surrounding inventory used “Tool chinh sửa” | P2 | `static/modules/center_setup_next.js` | Added `CENTER_SETUP_COPY` constants for corrected address-tool tabs/title and Excel export title. SHA-256 `98b97f2d5f0f6460e3cc81b8effbe3bd00dbacf9695d1c6622b4f9157d93e9f9` |

## Verification

- `node --check` passed for all four changed modules.
- `node tests/evidence/test_w6_frontend_autoload.mjs` passed (1/1).
- `PYTHONPATH=. python3 -m unittest tests.test_crm_supervision tests.test_finance_contract_supervision` passed (12/12).
- Finance frontend registry test was attempted; it remains blocked by its pre-existing assertion that the literal `UNKNOWN` must not occur in `finance_contract.js` (unrelated to this wave).

Live browser screenshots, reference/private semantics, and production persistence remain UNKNOWN. Finance import/renewal writes stay fail-closed.
