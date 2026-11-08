# Wave 0052 training report lane

Reviewed `claude-compare-0052/INDEX.md` and paired images for class/v2, due_date_student, homework_ratio, and allocation_student.

Changes in `static/modules/report_training.js`:

- Added observed pager metadata for `/report/training/class/v2` with page size 10.
- Added observed pager metadata for `/report/training/due_date_student` with page size 15.
- Existing allocation_student page size 20 retained. No rows padded or discarded; shared table controller paginates presentation only.
- No unsupported duplicate label changes applied. Homework-ratio and allocation filters remain source/inventory controlled.

Validation:

- `node --check static/modules/report_training.js` PASS
- `node tests/report-pagination-contracts.mjs` PASS
- `node tests/test_report_table.mjs` PASS, 8/8
- `git diff --check` PASS

Browser attempt: one bounded `shot_failing.js` invocation with configured NODE_PATH and local base. No route-specific fresh capture produced; visual/DOM parity remains UNKNOWN. Existing evidence retained without overwrite.
