# Center student visual follow-up — 2026-11-08

## Scope

Route-owned `static/app.js` only. Removed unobserved student controls `Xóa lọc`, table search `Tìm trong danh sách…`, and table count `80 mục`; retained seven reference-backed filters plus Excel/Upload/Thêm mới actions.

## Verification

- Reference inspected: `../claude-compare-1957/cmp_center_student_index.png` (1440x900).
- Prior local capture inspected: `../claude-compare-1957/local_center_student_index.png` (1440x900).
- Before evidence copied as `before.png`; SHA-256 `8bfe9c3f8bd7761b6712274e9614a62cc141800c33c92f65fe3db15dfcd6bf6c`.
- Current `static/app.js` SHA-256 `950ae76bba46f217dc0e1d1978611ef6d9c4fdf5231b0af15df0929469883591`.
- `node --check static/app.js` PASS; `git diff --check` PASS.

## Limitations

Fresh after screenshot was not captured: ORCA HTTP provider blocked the shot command for this worker (`http unavailable for EDIT_FILE`). Visual parity after edit remains UNKNOWN; no parity claim made. Focused pytest unavailable in earlier round (`No module named pytest`). Foreign working-tree changes, including `static/modules/report_crm_center.js`, remain unstaged.
