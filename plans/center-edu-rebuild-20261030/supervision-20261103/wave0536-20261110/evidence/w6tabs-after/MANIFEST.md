# W6 visual acceptance manifest

Viewport: 1440x900. Local server: isolated `19371`, rich demo DB `/tmp/wave0536-verification.sqlite`. Reference images are retained under `/Users/nam/claude-center-audit/ref/screens`.

| Surface | Fresh local evidence | Reference | Result / limit |
|---|---|---|---|
| Callcenter staff | `pairs/callcenter_staff-pair.png`, `callcenter-staff-live.png` | `115_callcenter_staff.png` | Compact controls render in the header row: 12 text inputs and 2 permission checkboxes; local persisted staff row differs from reference empty state. |
| Call statistics | `pairs/callcenter_get_statistic-pair.png`, `callcenter_get_statistic-final2.png` | `116_callcenter_get_statistic.png` | Fresh final capture: tabs first, one inline date row, Excel right. Persisted inbound row is visible while reference capture is empty; row-count difference is data, not fabricated for visual parity. |
| CSO support | `pairs/cso_support-pair.png`, `cso_support-final2.png`, `cso-internal.png` | `112_cso_support.png` | Fresh final capture: source-backed four status summaries, upper-right tabs, inline filters/actions, status chip, footer. Reference has four persisted rows; isolated local fixture has two. |
| Upload address | `pairs/center_upload_address-pair.png`, `center_upload_address.png`, `upload-potential-preview.png` | `131_center_upload_address.png` | CSV preview remains attached to selected potential target. |
| Finance points | `pairs/finance_accumulate_points-pair.png`, `finance_accumulate_points.png`, `finance-points-live.png`, `finance-points-statistics-populated.png`, `finance_accumulate_points_statistics-empty.png` | `047_finance_accumulate_points.png` | Empty and persisted-ledger states exercised. Populated row contains escaped text `Nguyễn Minh <A>`; browser showed one statistics row and no errors. Reference statistics-tab behavior is not documented in the inventory. |
| Birthday report | `pairs/birth_day_student-pair.png`, `birth_day-student.png`, `birth_day-staff.png`, `birth_day-staff-live.png` | `094_report_center_birth_day_index.png` | Student/staff tabs request separate persisted sources. Staff reload returned 10 persisted users; student empty state is truthful. Reference documents student view; staff visual contract is not separately documented. |

All images are local captures. A screenshot pair proves the rendered surface at this viewport only; it does not establish untested hover, modal, RBAC, or production parity.
