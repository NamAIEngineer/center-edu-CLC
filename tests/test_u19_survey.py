import csv
import io
import pathlib
import sqlite3
import unittest

from modules import survey


class U19SurveyInteractionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL)')
        self.db.execute("INSERT INTO users VALUES (1, 'Nguyễn Ngọc Mai')")
        survey.ensure_schema(self.db)
        survey.create_survey(self.db, {'name': 'Lớp A', 'due_date': '15/11/2026'}, created_by=1)
        survey.create_survey(self.db, {'name': 'Lớp B', 'status': 'PUBLISHED'}, created_by=1)

    def tearDown(self):
        self.db.close()

    def test_no_match_and_reset_query(self):
        self.assertEqual(survey.list_surveys(self.db, {'q': '__NO_MATCH__'}), [])
        self.assertEqual(len(survey.list_surveys(self.db, {'q': 'Lớp A'})), 1)
        self.assertEqual(len(survey.list_surveys(self.db, {})), 2)

    def test_export_correlates_with_active_filter(self):
        rows = survey.list_surveys(self.db, {'status': 'Đã phát hành'})
        parsed = list(csv.DictReader(io.StringIO(survey.export_csv(rows).lstrip('\ufeff'))))
        self.assertEqual([row['Tên khảo sát'] for row in parsed], ['Lớp B'])

    def test_renderer_contains_semantic_empty_and_reset_hooks(self):
        source = pathlib.Path('static/modules/survey.js').read_text()
        for marker in ('Không có dữ liệu.', 'survey-filter-clear', 'exportSurveyUrl', 'await refresh();'):
            self.assertIn(marker, source)

    def test_controls_are_stable_across_observed_name_normalization(self):
        source = pathlib.Path('static/modules/survey.js').read_text()
        # The shell normalizer can rename q/status/page_size after this renderer
        # returns (for example q -> tim_kiem). Capture the actual nodes before
        # that phase and ensure every interaction path uses those references.
        refs = ("const qControl = screen.querySelector('input[name=\"q\"]');",
                "const statusControl = screen.querySelector('select[name=\"status\"]');",
                "const pageSizeControl = screen.querySelector('select[name=\"page_size\"]');")
        for marker in refs:
            self.assertIn(marker, source)
        self.assertIn("p.set('q', q)", source)
        self.assertIn("p.set('status', status)", source)
        self.assertIn("p.set('page_size', pageSize)", source)
        self.assertIn("if (qControl) qControl.value = ''", source)
        self.assertIn("if (statusControl) statusControl.value = ''", source)
        self.assertNotIn("screen.querySelector('[name=\"q\"]')", source)
        self.assertNotIn("screen.querySelector('[name=\"status\"]')", source)
        self.assertNotIn("screen.querySelector('[name=\"page_size\"]')", source)


if __name__ == '__main__':
    unittest.main()
