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

    def test_u08_supported_class_filter_and_local_search_reset_contract(self):
        source = self.source.read_text(encoding="utf-8")
        for marker in (
            "renderConfirmationRoute", "confirmationQueryFromControls", "confirmationSearchRows",
            "classSelect?.addEventListener('change', load)", "search?.addEventListener('keydown'",
            "clear.addEventListener('click'", "/api/enrollment-confirmations${confirmationQueryFromControls(classSelect?.value)}",
        ):
            self.assertIn(marker, source)
        script = textwrap.dedent(f"""
            import {{ confirmationQueryFromControls, confirmationSearchRows }} from {json.dumps(self.source.as_uri())};
            if (confirmationQueryFromControls('TA-NEN-TANG-01') !== '?class=TA-NEN-TANG-01') process.exit(1);
            if (confirmationQueryFromControls('') !== '') process.exit(2);
            const rows = [
              {{ full_name: 'Nguyễn Minh Anh', class_code: 'TA-NEN-TANG-01', contract_code: 'CTR-001', confirmed_at: null, confirmed_by: null }},
              {{ full_name: 'Trần Bình', class_code: 'TA-GIAO-TIEP-02', contract_code: 'CTR-002' }},
            ];
            if (confirmationSearchRows(rows, 'no-such').length !== 0) process.exit(3);
            if (confirmationSearchRows(rows, 'CTR-001').length !== 1) process.exit(4);
            if (confirmationSearchRows(rows, '').length !== 2) process.exit(5);
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

    def test_timetable_dates_are_timezone_and_cross_year_stable(self):
        script = textwrap.dedent(f"""
            import {{ timetableDate, scopeTimetableRows }} from {json.dumps(self.source.as_uri())};
            const sameYear = timetableDate('Tuần 37 ♦ 2026 (07/09 - 13/09)');
            if (sameYear.start !== '2026-09-07' || sameYear.end !== '2026-09-13') process.exit(1);
            const crossYear = timetableDate('Tuần 53 ♦ 2026 (28/12 - 03/01)');
            if (crossYear.start !== '2026-12-28' || crossYear.end !== '2027-01-03') process.exit(2);
            const values = {{ week: 'Tuần 37 ♦ 2026 (07/09 - 13/09)', day: 'Thứ 2', day_date: '', time_from: '', time_to: '', session_number: '' }};
            const controls = {{ querySelector(selector) {{ const name = selector.match(/name="([^"]+)"/)?.[1]; return {{ value: values[name] || '' }}; }} }};
            const rows = [{{ session_date: '2026-09-07', id: 1 }}, {{ session_date: '2026-09-08', id: 2 }}, {{ session_date: '2026-09-13', id: 3 }}, {{ session_date: '2026-09-14', id: 4 }}];
            if (scopeTimetableRows(rows, controls).map(row => row.id).join(',') !== '1') process.exit(3);
            values.day = 'Thứ 4';
            if (scopeTimetableRows(rows, controls).length !== 0) process.exit(4);
            values.day = '';
            if (scopeTimetableRows(rows, controls).map(row => row.id).join(',') !== '1,2,3') process.exit(5);
        """)
        for timezone in ("UTC", "Asia/Ho_Chi_Minh"):
            env = {"TZ": timezone}
            result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, env={**__import__("os").environ, **env})
            self.assertEqual(result.returncode, 0, f"{timezone}: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
