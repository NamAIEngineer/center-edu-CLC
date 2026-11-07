"""Focused U06/U07 renderer contract regressions."""
from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


class TrainingAssessmentRendererTests(unittest.TestCase):
    source = Path(__file__).parents[1] / "static/modules/training_routes.js"

    def test_renderer_owns_persisted_rows_empty_error_filters_and_reset(self):
        source = self.source.read_text(encoding="utf-8")
        for marker in (
            "renderAssessmentRoute", "/api/tests", "/api/homework",
            "assessmentQueryFromControls", "Xóa lọc", "Chưa có dữ liệu",
            "Không thể tải dữ liệu", "select[data-filter-key=\"status\"]",
        ):
            self.assertIn(marker, source)

        script = textwrap.dedent(f"""
            import {{ assessmentQueryFromControls }} from {json.dumps(self.source.as_uri())};
            const values = {{ status: 'OPEN', class: 'TA-01' }};
            const select = (key) => ({{ value: values[key] || '' }});
            const controls = {{
              querySelector(selector) {{
                const key = selector.includes('status') ? 'status' : selector.includes('class') ? 'class' : '';
                return key ? select(key) : null;
              }},
              querySelectorAll(selector) {{
                return selector === 'select' ? [select('status'), select('class')] : [];
              }},
            }};
            if (assessmentQueryFromControls(controls) !== '?status=OPEN&class=TA-01') process.exit(1);
            values.status = ''; values.class = '';
            if (assessmentQueryFromControls(controls) !== '') process.exit(2);
        """)
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
