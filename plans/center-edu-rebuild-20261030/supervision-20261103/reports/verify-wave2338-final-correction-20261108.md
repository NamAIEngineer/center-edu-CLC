# Independent verifier: wave2338 final correction

Date: 2026-11-08. Reviewer: independent read-only verifier. Run: `run_bf152f4f7779`.

## Pin

- HEAD and remote: `10d2d1dde795bdf7b54bf87eba5d8aef5fad4777` (`center-edu-rebuild-verified`)
- Correction commit: `10d2d1d fix(training): preserve unknown row metadata`
- Changed source scope: `static/modules/training_routes.js` only.
- Current SHA-256: `d05b240de8085472e650bfdeb1ebd8317089895bcd451de351a9f2825c775861`

## Checks

- `node --check static/modules/training_routes.js`: PASS.
- `python3 -m unittest tests/test_training_backlog_regressions.py tests/test_training_projection_correction.py tests/test_training_supervision.py tests/test_training_timetable_lane.py`: **31 tests PASS**.
- `git diff --check`: PASS.
- Source scan confirms prior invented fallback values were removed from absent/event row rendering: no fallback student code, birth date, class, event view count, creator, timestamp, or `0/0` values remain. Existing source-backed schedule formatting remains conditional on observed class/date fields.

## Review

The correction removes fabricated metadata defaults while retaining observed values when present. Missing fields now remain empty/unknown. This satisfies the bounded source ownership requirement for training row metadata. No source files outside `training_routes.js` changed in this correction.

No browser or reference replay was attempted. Visual, mobile, action, reference, RBAC, persistence, and full `134/134` acceptance remain UNKNOWN. Existing wave2338 comparison artifacts retain unresolved historical differences and are not promoted by this source-only correction.

## Verdict

`DONE_WITH_CONCERNS`: correction verified at source and focused-test level. Product remains `PARTIAL / NOT_ACCEPTED`; no 100% or visual parity claim.
