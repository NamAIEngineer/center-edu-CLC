# CRM potential projection — wave1708

Route: `/crm/potential/index`
Source: `static/modules/crm_routes.js`

Observed repair:

- Removed the duplicated `.potential-status-summary` strip after the route renderer settles; the three reference tabs remain the single summary surface.
- Preserved `Khách hàng thô` and bound tab actions. The raw tab filters rendered persisted NEW prospects. The care-history tab reads `/api/care-appointments` and renders returned persisted rows.
- No `static/app.js`, `static/app.css`, or `static/nav-config.js` changes.

Evidence (1440x900, local disposable SQLite instance):

- `local-default.png` SHA256 `ea3561eaa827d288978b3bccbcd74bfe4a064956c093daeefbaf2c816569a0ff`
- `local-raw-tab.png` SHA256 `f051ea0560fab027c9496f85e4088680ab040d250b97f86135e3eb2ec33c835f`
- `local-care-tab.png` SHA256 `ac6ae76c8bb5fac749e37323b5584918a7b652aba0da0f365466b7e56f81a2f1`
- Reference `reference-default.png` SHA256 `1cfd667e2d1e1f2f4179dd20abd501557b9bc074be3e99bdec17d657208c610b`
- Action receipt: `action-receipt.json`

Validation:

- `node --check static/modules/crm_routes.js`
- `node tests/test_crm_potential_projection.mjs`
- `python3 -m unittest tests.test_crm_supervision -q` (6 passed)
- `git diff --check`

Status: PASS (bounded route-owned projection; reference/live data semantics remain bounded by local persisted records)
