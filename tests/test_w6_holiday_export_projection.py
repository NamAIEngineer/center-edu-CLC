"""Regression coverage for the W6 holiday export projection."""

from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path

from app import CenterEduService


class W6HolidayExportProjectionTests(unittest.TestCase):
    def test_persisted_holiday_fields_are_readable_and_exported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = CenterEduService(Path(tmp) / "runtime.sqlite3")
            try:
                admin = service.user_by_login("admin")
                self.assertIsNotNone(admin)
                payload = {
                    "name": "W6TEST Holiday, \"quoted\"",
                    "start_date": "2027-01-02",
                    "end_date": "2027-01-03",
                    "description": "W6TEST description, comma",
                    "notice": "W6TEST notice \"quote\"",
                    "status": "Kích hoạt",
                }

                created = service.add_generated_record(admin, "/center/holiday/index", payload)
                readback = service.generated_screen(admin, "/center/holiday/index", "W6TEST")
                exported = service.export_generated_screen(admin, "/center/holiday/index", "W6TEST")

                self.assertEqual(created["data"], payload)
                self.assertEqual(readback["total"], 1)
                self.assertEqual(readback["records"][0]["data"], payload)
                self.assertEqual(
                    exported,
                    [{
                        "No.": 1,
                        "Tên lịch nghỉ": payload["name"],
                        "Từ ngày": payload["start_date"],
                        "Đến hết ngày": payload["end_date"],
                        "Mô tả": payload["description"],
                        "Thông báo": payload["notice"],
                        "Trạng thái": payload["status"],
                        "Hành động": "",
                    }],
                )

                # Exercise the actual CSV projection to preserve comma/quote escaping.
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=list(exported[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(exported)
                rows = list(csv.DictReader(io.StringIO(output.getvalue())))
                self.assertEqual(rows[0]["Tên lịch nghỉ"], payload["name"])
                self.assertEqual(rows[0]["Mô tả"], payload["description"])
                self.assertEqual(rows[0]["Thông báo"], payload["notice"])
            finally:
                service.close()


if __name__ == "__main__":
    unittest.main()
