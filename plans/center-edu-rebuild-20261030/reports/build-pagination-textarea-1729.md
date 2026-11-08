# BUILD report — pagination capacities and textarea bounds

Status: PARTIAL / NOT_ACCEPTED

FACT: Updated `TRAINING_REPORT_PAGINATION` for `/report/training/allocation_student/index` and `/report/training/allocation_hours/index` from 10 to the observed capacity 20. Existing seven-route pager remains row-preserving and does not add selectors or rows. No finance module changed.

FACT: Shared `static/app.css` already declares global `textarea { width:100%; max-width:100%; min-width:0; box-sizing:border-box; resize:vertical; }`; no CSS edit was needed.

FACT: Commit `56058e1a659a7abbc399d9467927d59cdffbe7b6`.

FACT: `node --check static/modules/report_training.js`, `node --check static/modules/report_crm_center.js`, `node --test tests/test_report_table.mjs` (7/7), `git diff --check` pass.

UNKNOWN: Latest coordinator counsel says `/report/training/due_date_student` observed selector `[10,20,50]` conflicts with requested 15 and must remain UNKNOWN pending newer route-specific evidence. `/report/finance/class_revenue_tracking/index` and `_new/index` capacity 10 is finance-owned; CRM/report pager defaults lack numeric evidence and remain unchanged. Browser screenshot/DOM, `ui_fine`, and `ui_sweep` were not run because no supported authenticated runtime/credentials were available in this worker.

Hashes: `static/modules/report_training.js` SHA-256 `6e36b7dbe53f69f66b0d3a77f6c81dea8f23b832496cf0d157c0aec452206496`; `tests/test_report_table.mjs` SHA-256 `443e0d80eae8aa2da1dfdb5243afd0c626d98dd280088f83163fd42eac31b`; unchanged `static/app.css` SHA-256 `a2f11f75723bb4ee2de36b89564338ea48472761dbe90520b858e6c4f3993bcf`.
