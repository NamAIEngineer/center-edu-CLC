from datetime import date
import unittest
import tempfile
from pathlib import Path
from modules.report_filter_domains import current_year_filters
from modules.report_training import training_report_rows
from app import CenterEduService


class ReportYearDomainTests(unittest.TestCase):
    def test_historical_inventory_rolls_with_calendar(self):
        source = [{'name': 'year', 'options': ['Năm 2000', 'Năm 2024']}, {'name': 'status', 'options': ['2024', '2025']}]
        for year in (2026, 2027):
            filters = current_year_filters(source, today=date(year, 1, 1))
            self.assertEqual(filters[0]['options'][0], 'Năm 2000')
            self.assertEqual(filters[0]['options'][-1], f'Năm {year + 5}')
            self.assertEqual(filters[0]['default'], f'Năm {year}')
            self.assertEqual(filters[1], source[1])
        self.assertEqual(source[0]['options'][-1], 'Năm 2024')

    def test_allocation_year_does_not_mix_same_month_across_years(self):
        with tempfile.TemporaryDirectory() as temp:
            service = CenterEduService(Path(temp) / 'fixture.sqlite3')
            try:
                db = service.db
                enrollment = db.execute('SELECT class_id,student_id FROM enrollments LIMIT 1').fetchone()
                self.assertIsNotNone(enrollment)
                db.execute('DELETE FROM attendance')
                for day in ('2025-05-10', '2026-05-10', '2026-05-11'):
                    db.execute("INSERT INTO attendance(class_id,student_id,session_date,status,marked_by) VALUES(?,?,?,'PRESENT',1)", (*enrollment, day))
                for year, count in (('2025', 1), ('2026', 2)):
                    rows = training_report_rows(db, 'report_training_allocation_student_index', {'year': year})
                    self.assertEqual(rows[0]['thang_5'], count)
                with self.assertRaises(ValueError): training_report_rows(db, 'report_training_allocation_hours_index', {'year':'invalid'})
            finally: service.close()
