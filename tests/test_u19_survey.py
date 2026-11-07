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


if __name__ == '__main__':
    unittest.main()
