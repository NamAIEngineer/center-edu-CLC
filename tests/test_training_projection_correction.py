"""Focused deterministic checks for the class list projection correction."""
from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


class TrainingProjectionCorrectionTests(unittest.TestCase):
    def test_timetable_enrichment_and_no_match_predicate(self) -> None:
        source = Path(__file__).parents[1] / "static" / "modules" / "training_routes.js"
        script = textwrap.dedent(f"""
            import {{ enrichClassRows, classSearchMatches, summarizeClassStatuses }} from {json.dumps(source.as_uri())};
            const rows = enrichClassRows([
              {{ code: 'A', name: 'Alpha', schedule: '', teacher: '' }},
              {{ code: 'B', name: 'Beta', schedule: 'existing', teacher: 'Teacher B' }},
            ], [
              {{ class_code: 'A', session_date: '2026-11-04', start_time: '18:30', end_time: '20:00', teacher: 'Teacher A' }},
            ]);
            if (rows[0].schedule !== '2026-11-04 18:30-20:00' || rows[0].teacher !== 'Teacher A') process.exit(1);
            if (rows[1].schedule !== 'existing' || rows[1].teacher !== 'Teacher B') process.exit(2);
            if (classSearchMatches(rows[0], 'NO-SUCH-CLASS')) process.exit(3);
            if (!classSearchMatches(rows[0], 'alpha')) process.exit(4);
            const summary = summarizeClassStatuses([
              {{ code: 'A', status: 'PLANNED' }}, {{ code: 'B', status: 'ENDING_SOON' }},
              {{ code: 'C', status: 'COMPLETED' }}, {{ code: 'D', status: 'CANCELLED' }},
            ], [{{ class_code: 'A' }}, {{ class_code: 'B' }}, {{ class_code: 'C' }}, {{ class_code: 'D' }}]);
            const counts = Object.fromEntries(summary.map((item) => [item.key, item.count]));
            if (counts.planned !== 1 || counts.ending !== 1 || counts.completed !== 1 || counts.cancelled !== 1 || counts.noSchedule !== 0) process.exit(5);
            if (summary.length !== 6 || summary.some((item) => !item.label)) process.exit(6);
        """)
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_class_controls_include_observed_date_ends_and_timetable_actions(self) -> None:
        source = (Path(__file__).parents[1] / "static" / "modules" / "training_routes.js").read_text(encoding="utf-8")
        for marker in (
            "Tất cả khóa học", "Chọn giáo viên",
            "Ngày kết thúc: từ ngày", "Ngày kết thúc: đến ngày",
            "textContent = 'Tìm kiếm'", "textContent = 'Excel'",
            "textContent = 'TKB GV'", "/api/export/timetable",
            "teacherView.disabled = true",
        ):
            self.assertIn(marker, source)

    def test_renderer_keeps_name_secondary_code_and_empty_state_contract(self) -> None:
        source = (Path(__file__).parents[1] / "static" / "modules" / "training_routes.js").read_text(encoding="utf-8")
        for marker in (
            "name.textContent = projection.name",
            "code.textContent = projection.code",
            "Không tìm thấy dữ liệu",
            "rows = rows.filter((row) => classSearchMatches(row, state.filters.q))",
            "export function enrichClassRows",
        ):
            self.assertIn(marker, source)

    def test_class_projection_accepts_legacy_persisted_aliases(self) -> None:
        source = Path(__file__).parents[1] / "static" / "modules" / "training_routes.js"
        script = textwrap.dedent(f"""
            import {{ classListProjection }} from {json.dumps(source.as_uri())};
            const projected = classListProjection({{
              code: 'A-01', name: 'Lớp A', course: 'IELTS',
              enrolled_count: 7, manager: 'CM Mai', teacher_name: 'Cô An',
            }});
            if (projected.courseName !== 'IELTS' || projected.studentCount !== 7
              || projected.manager !== 'CM Mai' || projected.teacher !== 'Cô An') process.exit(1);
        """)
        result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_status_strip_uses_local_denominator_progress_and_accessible_action_affordance(self) -> None:
        source = (Path(__file__).parents[1] / "static" / "modules" / "training_routes.js").read_text(encoding="utf-8")
        for marker in (
            "const total = Array.isArray(rows) ? rows.length : 0",
            "count.textContent = `${item.count === null ? '—' : item.count}/${total}`",
            "track.setAttribute('role', 'progressbar')",
            "button.textContent = '…⌄'",
            "button.setAttribute('aria-label', 'Chi tiết lớp học')",
            "button.textContent = '⌃'",
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
