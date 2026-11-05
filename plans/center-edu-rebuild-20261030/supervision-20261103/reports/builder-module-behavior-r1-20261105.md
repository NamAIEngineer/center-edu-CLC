# CRM module behavior correction — 2026-11-05

## Scope

Owned file only: `products/center-edu-rebuild/static/modules/crm_routes.js`. No edits to `static/app.css`, `static/app.js`, `app.py`, backend private semantics, or shared files.

## Before

- Prior worker receipt identified `static/modules/crm_routes.js` hash `05482f728d65f04c4fd28daba0961bf5c38c2f7dca82bbb12db753b86d8a1168`.
- Delete flow used `.crm-delete-modal` without the shared `.modal-backdrop` / `.modal` classes. It had no Escape handling, backdrop cancel, focus trap, or focus restoration; async failure replaced the confirmation text and could lose focus.
- `/crm/potential/index` legacy projection marked the whole concatenated status summary (`Mới … Đang chăm sóc …`) as `role=tab`, allowing it to be exposed as a tab before the real content tablist. The route document title fell back to generic `Center EDU — Academic Operations` because the route was absent from the shell title map.

## Changes

- Delete confirmation now uses `.modal-backdrop.crm-delete-modal` containing `.modal.crm-delete-dialog`, `role=dialog`, `aria-modal`, and `aria-labelledby`.
- Initial focus remains on Cancel. Escape, backdrop click, and Cancel close the modal; focus returns to the invoking delete button. Tab/Shift+Tab are trapped inside the modal. Confirm disables during DELETE; API errors remain in an `aria-live` error node and focus returns to Confirm.
- Added route-local projection observer: on `/crm/potential/index`, status counters lose erroneous tab roles and receive an accessible summary label, while the existing `.ref-tabs[role=tablist]` content semantics remain untouched. The observer sets route title `Khách hàng tiềm năng` after the legacy renderer runs.

## Verification

- `node --check static/modules/crm_routes.js` — PASS.
- After hash: `91d6053e21d304ece50660bff16dcd72a45d5ba9cd78181396145f1f29b34d8f`.
- Static evidence: only `static/modules/crm_routes.js` changed in this worker scope. Browser/live screenshot verification remains UNKNOWN in this pass; coordinator/verifier may inspect the route with an isolated runtime.

## FACT / UNKNOWN

- FACT: modal behavior and potential-route projection/title corrections are present in the owned module; syntax passes; no shared app/CSS/backend edits made.
- UNKNOWN: live browser acceptance, visual parity, and backend DELETE response semantics were not re-run here.
