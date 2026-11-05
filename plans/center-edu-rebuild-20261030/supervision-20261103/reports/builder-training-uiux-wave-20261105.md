# Training UI/UX builder wave — 2026-11-05

Status: `DONE_WITH_CONCERNS` (local source gates pass; reference/private visual parity remains `UNKNOWN`).

## Findings fixed

| ID | Repro | Expected | Actual before | Severity | File | After evidence |
|---|---|---|---|---|---|---|
| TRN-UI-001 | Open `/training/class` with a class payload using legacy persisted keys (`course`, `enrolled_count`, `teacher_name`, `manager`) | Class table projects course, active student count, manager, teacher | Projection only read current aliases; valid persisted rows could render blank cells | P1 | `static/modules/training_routes.js` | `classListProjection()` now accepts current and legacy aliases; table explicitly renders `course_name` and `student_count`; focused Node assertion passes |
| TRN-UI-002 | Student filter submits Vietnamese placeholder variants with different case (`Tất Cả`, `Chọn khóa học`, `ALL`) | Placeholder choices stay out of `/api/students` predicates | Exact-case sentinel set leaked placeholder values into API filters | P1 | `static/modules/w6_overrides.js` | `studentFilterValues()` trims and uses Vietnamese case-folding; ignores all observed placeholder variants |

## Before/after evidence

- Before: projection read `row.course_name`, `row.student_count`, `row.teacher`, and only `primary_manager`/`secondary_manager`; alternate persisted keys were not projected.
- After: projection normalizes `course_name|course`, `student_count|enrolled_count|active_student_count`, `teacher|teacher_name`, and `primary_manager|manager`; table cells use normalized projection values.
- Before: student placeholder filtering compared exact strings.
- After: normalized `toLocaleLowerCase('vi')` comparison prevents sentinel leakage while preserving real filter values.
- Focused test count: `30` tests, `OK`.

## Verification

Commands:

```text
node --check static/modules/training_routes.js
node --check static/modules/w6_overrides.js
python3 -m py_compile modules/report_training.py
python3 -m unittest tests.test_training_projection_correction tests.test_training_timetable_lane tests.evidence.test_W4_report_training_teacher tests.test_training_supervision -q
```

Result: syntax checks passed; Python compile passed; `30 tests ... OK`.

Disposable runtime/browser visual acceptance was not run in this worker. Reference/private semantics, authenticated parity, and visual parity remain `UNKNOWN`; no external state or preserved runtime was touched.

## Source hashes

```text
963c2a428faf5dfa4a1cfd5cc05cf601b088fcd20f7ac9e6a738cae6c851e767  static/modules/training_routes.js
2829a75b7580051e0f3b1dba0ca75372d83498cb6cd91d29b7703709591ec591  static/modules/w6_overrides.js
a71a1b25e01b9f195a254649eefa28e2c7d5bbb2e3da941e05ab63697f8570a5  modules/report_training.py
99bb17999211bdd3e577128ff4bfb1dd80476500e7a6d2eda200cfedc3f5637d  tests/test_training_projection_correction.py
```
