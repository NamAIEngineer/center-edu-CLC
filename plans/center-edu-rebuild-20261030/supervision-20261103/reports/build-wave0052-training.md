# Wave 0052 training renderer

Scope: `/training/absent-v2`, `/training/event`; renderer only.

Changes: filter-row action placement for event and absent; route-owned green absent `+ Thêm mới` and blue event `Tạo sự kiện đào tạo`; eye marker for event view count; links for absent student/session and event title; existing row metadata remains newline rendered; event status supports scheduled metadata when supplied by route payload; icon actions and footer retained.

Validation: `node --check static/modules/training_routes.js` PASS; `git diff --check` PASS. Bounded `shot_failing.js` ran against `http://127.0.0.1:18990` with `NODE_PATH=/Users/nam/claude-center-audit/node_modules`; artifacts copied to `evidence/visual/wave0052-training/` and hashes recorded. Captured service was canonical-equivalent running instance; fresh branch-specific DOM replay remains UNKNOWN.
