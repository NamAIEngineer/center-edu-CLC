# Independent verification — training report lane

- Run: `run_bf152f4f7779`
- Commit: `01c42abf94308fd1027692c5efcc6201167f4cee`
- Parent: `01c42abf94308fd1027692c5efcc6201167f4cee^`
- Scope checked: `static/modules/report_training.js`, `tests/test_report_table.mjs`, supplied report/artifacts.
- Verdict: `PASS_WITH_CONCERNS` (source/test contract passes; browser parity remains UNKNOWN).

## Diff and ownership

Exact commit diff contains five paths: the two requested source/test files and three training-report evidence files under `plans/center-edu-rebuild-20261108-wc-report-training/evidence/visual/training-report-20261108/`. No `static/app.js`, shared CSS, finance module, or other application source changed. Source change exports `TRAINING_AUTO_FILTER_ROUTES` and extends observed update-only behavior to the five listed training report routes; test adds an exact route-list assertion.

## Verification performed

- `node --check static/modules/report_training.js`: PASS.
- `node --test tests/test_report_table.mjs`: PASS, 8/8.
- `node --test tests/report-pagination-contracts.mjs`: PASS, 1/1 (`Report pagination contracts PASS`).
- `git diff --check 01c42abf^ 01c42abf`: CONCERN: fails only on pre-existing evidence line 3 in committed `report.md` (`Run: ...` has trailing spaces). Source/test hunks are clean.
- Inventory `claude-compare-1843/INDEX.md` and assigned comparison images confirm the observed route inventory. Reference metadata contains duplicate labels/options including `Chọn khóa học`, `Tháng 1`, and selector label `10 20 50`; commit preserves them and does not add deduplication.
- No fabricated rows/data observed. Report explicitly leaves persisted row-count differences UNKNOWN; implementation changes controls only.

## Browser and visual boundary

The worker artifact reports `Browsers: Error: The browser access host is unavailable`; no fresh DOM/action or before/after screenshot was captured in this verification. Supplied comparison images are reference inputs only. Authenticated reference/private API behavior, RBAC, production persistence, exact row values, and live DOM parity remain `UNKNOWN`; source and focused tests do not establish those claims.

## Hashes (SHA-256)

- `static/modules/report_training.js`: `f167b11848c375ddea2e6adda31bb38761df54b9222ec32806c83f086bfbff62`
- `tests/test_report_table.mjs`: `4813311c006cd8576ed94feed6babca4143a0758abc5536a84bcc2c9e9f23449`
- worker `report.md`: `32c8f4f9bc52bf8489c46292323a112519e092981323d75515b377be936da52a`
- worker `report.sha256`: `223eceecdd1ceac0510118c8856374044016d265316c8a6dd8bd5ffa7fb1dc03`
- worker `source-test.sha256`: `fa2b127f84fce463bd1b352c967b139819038d9c6625a344891f41fde51cfc3f`
- comparison `INDEX.md`: `ba307bd4af2502c79892fe46b3f2376359d77cc8c7235d3a3124a91b1f68463d`
- assigned image `cmp_report_training_class_v2.png`: `a9d55cc1741266089561e6ab0ead3c95b661ad4bd89664361299c69ce4a0996f`
- assigned image `cmp_report_training_homework_ratio_index.png`: `4006fe8e6f3df48fbbb1807b5762d5cf90665215be9b659fbe94107aaf802e9d`
- assigned image `cmp_report_training_allocation_student_index.png`: `70cadb5a8da42ec2cc55018e8694e07a7170e8f4e0a736569318b9f5fa34d230`
- assigned image `cmp_report_training_due_date_student.png`: `b18b044e804c6aef2ef9026ca4f1708ac96eb456fc8139e8eb92d6db2547a929`

