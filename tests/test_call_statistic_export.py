import csv
import io
import sqlite3
import unittest
from modules.center_lane import SCHEMA, create_record, export_csv


class CallStatisticExportTests(unittest.TestCase):
    def test_filter_direction_date_and_empty_headers(self):
        db = sqlite3.connect(':memory:'); db.row_factory = sqlite3.Row; db.executescript(SCHEMA)
        route = '/callcenter/get-statistic'
        for direction, day, name in [('inbound','2026-11-10','QA incoming'),('outbound','2026-11-10','QA outgoing'),('outbound','2026-11-09','QA older')]:
            create_record(db, route, {'direction':direction,'from_date':day,'to_date':day,'staff_name':name,'total_calls':2,'answered_calls':1,'missed_calls':1})
        rows = list(csv.reader(io.StringIO(export_csv(db,route,{'direction':'outbound','date_from':'2026-11-10','date_to':'2026-11-10'}).lstrip('\ufeff'))))
        self.assertEqual(len(rows[0]),8)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[1][1],'QA outgoing')
        empty = list(csv.reader(io.StringIO(export_csv(db,route,{'direction':'outbound','date_from':'2027-01-01'}).lstrip('\ufeff'))))
        self.assertEqual(len(empty),1)
        self.assertEqual(empty[0],rows[0])
        db.close()
