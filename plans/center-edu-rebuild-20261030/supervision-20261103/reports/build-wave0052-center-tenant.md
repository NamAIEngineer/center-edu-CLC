# Wave 0052 center and tenant renderer

Scope: `/center/student/index` and `/tenant/config_excel` only.

Center student: compact multi-select controls now expose exact observed placeholders `Chọn trạng thái` and `Chọn lớp học` through data-placeholder while preserving the native select transport and all seven observed controls. Real API rows/actions unchanged.

Tenant config: existing renderer behavior verified against the observed contract. Missing unique persistence rows default enabled; persisted off values remain off; duplicate titles remain disabled; master row remains visible and guarded. No source change was needed for tenant behavior.

Validation: `node --check static/app.js`, `node --check static/modules/w6_screen_utils.js`, focused student/tenant tests (4/4), `git diff --check` all PASS. Bounded `shot_failing.js` ran against `http://127.0.0.1:18990` using `NODE_PATH=/Users/nam/claude-center-audit/node_modules`; screenshot hashes recorded under evidence/visual/wave0052-center-tenant. Captured runtime was canonical-equivalent; branch-specific DOM replay remains UNKNOWN.
