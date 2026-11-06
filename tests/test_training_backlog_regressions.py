"""Focused source and helper checks for the training backlog regressions."""
from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


class TrainingBacklogRegressionTests(unittest.TestCase):
    source = Path(__file__).parents[1] / "static/modules/training_routes.js"

    def test_u08_null_safe_confirmation_projection(self):
        script = textwrap.dedent(f"""
            import {{ displayText }} from {json.dumps(self.source.as_uri())};
            if (displayText(null, undefined) !== '') process.exit(1);
            if (displayText(null, '2026-11-03') !== '2026-11-03') process.exit(2);
            if (displayText(undefined, 'Nguyễn Minh Anh') !== 'Nguyễn Minh Anh') process.exit(3);
        """)
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_u01_course_search_wires_input_change_and_enter_to_api_query(self):
        source = self.source.read_text(encoding="utf-8")
        for marker in ("courseQueryFromControl", "addEventListener('input', trigger)", "addEventListener('change', load)", "event.key === 'Enter'", "/api/courses${courseQueryFromControl(searchInput)}"):
            self.assertIn(marker, source)
        script = textwrap.dedent(f"""
            import {{ courseQueryFromControl }} from {json.dumps(self.source.as_uri())};
            if (courseQueryFromControl({{ value: '' }}) !== '') process.exit(1);
            if (courseQueryFromControl({{ value: 'IELTS mục tiêu' }}) !== '?q=IELTS%20m%E1%BB%A5c%20ti%C3%AAu') process.exit(2);
        """)
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_u05_empty_and_error_states_are_explicit(self):
        source = self.source.read_text(encoding="utf-8")
        for marker in ("Đang tải dữ liệu…", "Chưa có dữ liệu", "Không thể tải dữ liệu đánh giá.", "Không thể tải dữ liệu khóa học.", "role', state.error ? 'alert' : 'status'"):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
