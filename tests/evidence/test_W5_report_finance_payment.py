import csv
import io
import os
import tempfile
import sqlite3
import unittest
from pathlib import Path

from app import CenterEduService
from modules.finance_report_adapter import FinanceReportProvider
from modules.report_engine import ReportEngine


class W5FinancePaymentReportTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE finance_bills (
              id INTEGER PRIMARY KEY, invoice_code TEXT, contract_code TEXT,
              customer_name TEXT, payment_amount REAL, confirmation_status TEXT,
              payment_method TEXT, invoice_date TEXT, center TEXT, created_at TEXT,
              note TEXT
            );
        ''')
        self.db.executemany(
            '''INSERT INTO finance_bills
               (invoice_code,contract_code,customer_name,payment_amount,confirmation_status,
                payment_method,invoice_date,center,created_at,note)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            [
                ('I-01', 'C-01', 'Nguyễn An', 1000000, 'CONFIRMED', 'Chuyển khoản', '2026-11-01', 'Cơ sở 1', '2026-11-01', ''),
                ('I-02', 'C-02', 'Trần Bình', 250000, 'CONFIRMED', 'cash', '2026-11-02', 'Cơ sở 1', '2026-11-02', ''),
                ('I-03', 'C-03', 'Lê Chi', 500000, 'PENDING', 'Ví CO', '2026-11-03', 'Cơ sở 2', '2026-11-03', ''),
                ('I-04', 'C-04', 'Đỗ Dũng', 900000, 'CONFIRMED', '9PAY', '2026-10-31', 'Cơ sở 2', '2026-10-31', ''),
            ],
        )
        self.db.commit()
        self.provider = FinanceReportProvider(self.db)
        self.engine = ReportEngine(self.provider, spec_path=Path(__file__).parents[2] / 'screen_specs' / 'reference-screen-specs.json')

    def tearDown(self):
        self.db.close()

    def test_payment_aggregate_uses_named_dates_and_vietnamese_methods(self):
        rows = list(self.provider.query_report(entity='report_finance_payment_index', filters={
            'from_date': '2026-11-01', 'to_date': '2026-11-03',
        }))
        self.assertEqual(len(rows), 2)
        by_center = {row['trung_tam']: row for row in rows}
        self.assertEqual(by_center['Cơ sở 1']['chuyen_khoan'], 1000000)
        self.assertEqual(by_center['Cơ sở 1']['tien_mat'], 250000)
        self.assertEqual(by_center['Cơ sở 1']['tong_doanh_thu'], 1250000)
        self.assertEqual(by_center['Cơ sở 2']['vi_co'], 500000)

    def test_report_projection_and_csv_export_keep_reference_columns(self):
        result = self.engine.run('/report/finance/payment/index', filters={'from_date': '2026-11-01', 'to_date': '2026-11-02'})
        self.assertEqual(result['data_status'], 'OBSERVED')
        self.assertEqual([column['key'] for column in result['columns']], [
            'no', 'trung_tam', 'vi_co', 'tien_mat', 'chuyen_khoan', 'quet_the',
            'vimass', 'vnpay', '9pay', 'tra_gop', 'napas', 'tong_doanh_thu',
        ])
        exported = self.engine.export_csv('/report/finance/payment/index', filters={'from_date': '2026-11-01', 'to_date': '2026-11-02'})
        header = next(csv.reader(io.StringIO(exported)))
        self.assertEqual(header, ['No.', 'Trung tâm', 'Ví CO', 'Tiền mặt', 'Chuyển khoản', 'Quẹt thẻ', 'Vimass', 'VNPAY', '9PAY', 'Trả góp', 'NAPAS', 'Tổng doanh thu'])
        self.assertIn('Cơ sở 1', exported)
        self.assertNotIn('Cơ sở 2', exported)

    def test_existing_shell_wire_aliases_map_to_observed_date_filters(self):
        rows = list(self.provider.query_report(entity='report_finance_payment_index', filters={
            'q': '2026-11-01', 'filter_1': '2026-11-02',
        }))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['trung_tam'], 'Cơ sở 1')

    def test_item_export_does_not_project_catalogue_or_bills(self):
        rows = list(self.provider.query_report(entity='report_finance_revenue_item_export', filters={}))
        self.assertEqual(rows, [])

    def test_autoload_registers_owned_adapters_and_preserves_item_export_gap(self):
        old = os.environ.get('CENTER_EDU_RICH_DEMO')
        os.environ['CENTER_EDU_RICH_DEMO'] = '1'
        try:
            with tempfile.TemporaryDirectory() as td:
                service = CenterEduService(Path(td) / 'w5-register.sqlite3')
                try:
                    self.assertEqual(service.module_registry['finance_report_adapter']['status'], 'ADAPTER_READY')
                    self.assertEqual(service.module_registry['report_crm_center']['status'], 'ADAPTER_READY')
                    report = service.report_engine_v2.run('/report/finance/revenue_item/export')
                    self.assertEqual(report['data_status'], 'NO_DATA')
                    self.assertEqual(report['rows'], [])
                finally:
                    service.close()
        finally:
            if old is None:
                os.environ.pop('CENTER_EDU_RICH_DEMO', None)
            else:
                os.environ['CENTER_EDU_RICH_DEMO'] = old


if __name__ == '__main__':
    unittest.main()
