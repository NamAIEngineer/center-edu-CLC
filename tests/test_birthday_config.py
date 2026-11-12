import sqlite3
import tempfile
import unittest
from pathlib import Path
from modules.center_lane import SCHEMA, create_record, update_record, list_records


class BirthdayConfigTests(unittest.TestCase):
    def test_roundtrip_validation_and_role(self):
        route = '/report/center/birth_day/config'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.sqlite3'
            db = sqlite3.connect(path); db.row_factory = sqlite3.Row; db.executescript(SCHEMA)
            data = {'days_before': '2', 'time_sent': '9', 'content': 'QA local birthday config'}
            record = create_record(db, route, data)
            update_record(db, route, record['id'], {'time_sent': '10'})
            for invalid in ({'time_sent': '24'}, {'days_before': '-1'}, {'send_now': True}):
                with self.assertRaises(ValueError): update_record(db, route, record['id'], invalid)
            with self.assertRaises(PermissionError): create_record(db, route, data, role='STUDENT')
            db.close(); db = sqlite3.connect(path); db.row_factory = sqlite3.Row
            rows = list_records(db, route)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['data'], {**data, 'time_sent': '10'})
            db.close()


if __name__ == '__main__': unittest.main()
