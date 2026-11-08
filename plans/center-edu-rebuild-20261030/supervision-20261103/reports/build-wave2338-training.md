# Wave 2338 training absent/event builder report

Scope: `/training/absent-v2`, `/training/event` only.

Changes:
- Progress summaries normalize persisted Vietnamese and enum status values; counts derive from loaded rows and bars use route status colors.
- Absent rows render student name/code/birth date, class/session/date/time, reason and creator/time as source-backed multiline cells.
- Event rows render view counts, content with created-by/time secondary text, Vietnamese sent status, and icon-only edit/copy/delete controls.
- Create actions remain in the observed filter row for both routes.
- Existing comment controls and event footer pager retained.

Validation:
- `node --check static/modules/training_routes.js` PASS.
- `python3 -m py_compile app.py` PASS.
- `git diff --check` PASS.
- Screenshot attempt: not run; bounded environment lacks a running local instance/port for `shot_failing.js`. Visual/reference parity remains UNKNOWN.

Evidence:
- Source hashes: `evidence/visual/wave2338-training/source-sha256.txt`.
- Reference comparison inspected: `claude-compare-2338/cmp_training_absent_v2.png`, `cmp_training_event.png`.

Limitations: no browser replay, DOM hash, or independent visual verification. No final acceptance claim.
