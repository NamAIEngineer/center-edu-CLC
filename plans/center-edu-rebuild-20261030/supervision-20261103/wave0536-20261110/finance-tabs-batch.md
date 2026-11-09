# Finance tabs batch — 2026-11-10

Runtime: fresh isolated rich DB at http://127.0.0.1:19363. Viewport 1440×900.

Verified browser behavior: inventory/category/import/export, spend/category,
reserve/refund, ordinary/prepaid/online bill, pricing/course-package,
contract/item-transfer/difference-history. Returning to the base tab restores
exactly one visible table. Independent verifier reported no page errors.

Pricing package scope persists separately from course pricing. Create modal
uses package field and Hủy/Lưu. Item-transfer projection reads only explicit
persisted transfer_kind; no inference from payment method or item names.

Visual review: pairs attached in finance-final/ and commit-finance-after/;
finance-final2/ holds latest spend/bill placement. Filter/search/action rows
moved into a compact route-owned panel. Date placeholders are Vietnamese text.
Page-size controls preserve their real change handler after shell normalization.

Limits: local rich seed differs from demo records. Import/export receipt views
and prepaid/online invoice views show an empty state when no explicit persisted
source discriminator exists. This batch proves tab behavior, not complete
pixel parity or full receipt/invoice subtype CRUD. Remaining UI differences
are tracked in the final acceptance matrix; no 100% acceptance claim.

Checks: node --check on all touched finance JS; isolated pricing/transfer
persistence roundtrip; git diff --check. Python suite: 90 tests, 88 passed;
known failures test_finance_revenue_controls_keep_query_reset_export_contract
and test_health_and_public_shell. Independent screenshots retained.
