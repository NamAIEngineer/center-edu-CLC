import tempfile
import unittest
from pathlib import Path
from app import CenterEduService
from modules.report_training import training_report_rows


class HomeworkRatioFilters(unittest.TestCase):
    def test_course_class_and_student_predicates_use_persisted_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            service = CenterEduService(Path(temp) / 'fixture.sqlite3')
            try:
                db = service.db
                enrollment = db.execute('SELECT e.class_id,c.course_id,s.full_name FROM enrollments e JOIN classes c ON c.id=e.class_id JOIN students s ON s.id=e.student_id LIMIT 1').fetchone()
                entity = 'report_training_homework_ratio_index'
                rows = training_report_rows(db, entity, {'filter_2':str(enrollment['course_id']),'filter_3':str(enrollment['class_id']),'nhap_ten_hoc_vien':enrollment['full_name']})
                self.assertEqual(len(rows),1)
                self.assertEqual(rows[0]['ho_va_ten'],enrollment['full_name'])
                self.assertIsNone(rows[0]['ti_le_lam_bai_tap'])
                self.assertEqual(training_report_rows(db,entity,{'filter_3':'999999'}),[])
                self.assertEqual(training_report_rows(db,entity,{'nhap_ten_hoc_vien':'QA no match'}),[])
                with self.assertRaises(ValueError): training_report_rows(db,entity,{'filter_3':'invalid'})
            finally: service.close()
