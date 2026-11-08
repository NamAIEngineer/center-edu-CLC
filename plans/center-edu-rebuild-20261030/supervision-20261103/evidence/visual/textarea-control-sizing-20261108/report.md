# Global textarea/control sizing lane — no-op

Task: `run_bf152f4f7779` · route `/training/absent-v2`, `/training/event` · branch `center-edu-rebuild-verified`

## Finding

The requested global rule already exists in `static/app.css` (the shared visual guardrails block):

```css
textarea {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 96px;
  box-sizing: border-box;
  resize: vertical;
}
```

This satisfies the requested `resize: vertical`, `max-width: 100%`, and `box-sizing: border-box` behavior while preserving the existing `width: 100%` and `min-width: 0` bounds. No CSS edit was made; unrelated shell layout remains untouched.

## Visual inspection

Read `claude-compare-1843/INDEX.md` and inspected `cmp_training_absent_v2.png` and `cmp_training_event.png` at their captured comparison viewport. Both observations are explicitly `textarea kéo giãn được` (`RESIZABLE=7` and `RESIZABLE=2`). The rebuild panels show the corresponding textarea controls; the current source rule provides the requested vertical-only resize and parent-width bound.

The existing same-viewport before/after CSS evidence is retained at:
`plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108/`.
It records the four viewport limits (`1280x900`, `1440x900`, `1920x900`, `390x844`) and 636/636 after checks. A fresh authenticated capture was unavailable in this worker because `LOCAL_PASS` is unset; no screenshots were overwritten or fabricated.

## Checks

- `node --check tests/evidence/test_shared_css_regressions.mjs` — PASS.
- Browser CSS parser check on `static/app.css` — PASS (stylesheet parses; rule declarations present).
- `git diff --check` — PASS.

## Limits

Synthetic CSS evidence only. No reference/live parity or authenticated interaction claim. Scope is limited to the existing global textarea sizing rule and this report; `static/app.js`, `app.py`, and report modules were not touched.
