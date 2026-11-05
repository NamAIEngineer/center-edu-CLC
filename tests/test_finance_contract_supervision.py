"""Focused W3 checks for the observed Finance Contract child routes.

These tests exercise only the owned SQLite contract.  The HTTP shell remains a
coordinator integration boundary; no reference session or private API is used.
"""
from __future__ import annotations

import csv
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

from modules.finance_contract import (
    EXTENSION_ROUTE,
    UPLOAD_HEADERS,
    UPLOAD_SAVE_BLOCKERS,
    UPLOAD_PROVENANCE,
    UPLOAD_ROUTE,
    FinanceContract,
)


def _csv(rows: list[list[str]], headers: tuple[str, ...] = UPLOAD_HEADERS) -> str:
    stream = io.StringIO(newline="")
    csv.writer(stream).writerows([headers, *rows])
    return "\ufeff" + stream.getvalue()


class FinanceContractSupervisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.store = FinanceContract(self.db)
        self.row = [
            "HD-UP-001", "HV-001", "KH-001", "ENG-FND", "12", "PK-ENG", "ITEM-ENG",
            "3000000", "DISC-COURSE", "200000", "2800000", "DISC-CONTRACT", "100000",
            "02/11/2026", "01/02/2027", "3200000", "50000", "2700000",
            "Ghi chú synthetic", "CLASS-001", "05/11/2026",
        ]

    def tearDown(self) -> None:
        self.db.close()

    def test_template_matches_observed_upload_headings_without_rows(self) -> None:
        template = self.store.upload_template()
        rows = list(csv.reader(io.StringIO(template.lstrip("\ufeff"))))
        self.assertEqual(rows, [list(UPLOAD_HEADERS)])
        self.assertEqual(len(UPLOAD_HEADERS), 21)
        self.assertEqual(
            list(UPLOAD_HEADERS[-6:]),
            [
                "Tổng tiền trước giảm giá", "Giảm giá trực tiếp", "Tổng tiền sau giảm giá",
                "Ghi chú hợp đồng", "Mã lớp học", "Ngày bắt đầu học",
            ],
        )
        self.assertNotIn("Nguyễn", template)

    def test_preview_is_read_only_and_reports_invalid_rows(self) -> None:
        before = self.db.execute("SELECT COUNT(*) FROM finance_contracts").fetchone()[0]
        result = self.store.preview_upload(_csv([self.row]), role="ADMIN")
        self.assertEqual(result["valid_count"], 1)
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["mutation"])
        self.assertFalse(result["can_commit"])
        self.assertEqual(result["save_blockers"], list(UPLOAD_SAVE_BLOCKERS))
        self.assertEqual(result["validation_scope"], "LOCAL_SYNTAX_AND_SAFE_TYPES_ONLY")
        self.assertEqual(result["rows"][0]["gross_total_before_discount"], 3200000)
        self.assertEqual(result["rows"][0]["direct_discount"], 50000)
        self.assertEqual(result["rows"][0]["gross_total_after_discount"], 2700000)
        self.assertEqual(result["rows"][0]["contract_note"], "Ghi chú synthetic")
        self.assertEqual(result["rows"][0]["class_code"], "CLASS-001")
        self.assertEqual(result["rows"][0]["start_date"], "2026-11-05")
        self.assertEqual(result["provenance"], UPLOAD_PROVENANCE)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contracts").fetchone()[0], before)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contract_uploads").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contract_upload_rows").fetchone()[0], 0)

        unreconciled = list(self.row)
        unreconciled[10] = "1"
        unreconciled[15] = "999999"
        unreconciled[16] = "2"
        unreconciled[17] = "999998"
        totals = self.store.preview_upload(_csv([unreconciled]), role="ADMIN")
        self.assertEqual(totals["valid_count"], 1)
        self.assertEqual(totals["errors"], [])
        self.assertFalse(totals["can_commit"])
        self.assertEqual(self.db.total_changes, 0)

        malformed = list(self.row)
        malformed[4] = "mười hai"
        invalid = self.store.preview_upload(_csv([malformed]), role="ADMIN")
        self.assertEqual(invalid["valid_count"], 0)
        self.assertEqual(invalid["errors"][0]["row"], 2)
        self.assertIn("Số buổi đăng ký", invalid["errors"][0]["message"])

    def test_commit_is_blocked_for_unsupported_semantics_and_role_bounded(self) -> None:
        with self.assertRaises(PermissionError):
            self.store.preview_upload(_csv([self.row]), role="STUDENT")
        before = self.db.total_changes
        with self.assertRaisesRegex(ValueError, "Lưu bị khóa") as caught:
            self.store.commit_upload(_csv([self.row]), role="ADMIN", actor="Synthetic Operator")
        for blocker in UPLOAD_SAVE_BLOCKERS:
            self.assertIn(blocker, str(caught.exception))
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contracts").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contract_uploads").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contract_upload_rows").fetchone()[0], 0)

    def test_invalid_preview_and_commit_do_not_leave_batch_or_contract_rows(self) -> None:
        bad = list(self.row)
        bad[16] = "-1"  # invalid direct-discount syntax
        preview = self.store.preview_upload(_csv([bad]), role="ADMIN")
        self.assertEqual(preview["valid_count"], 0)
        self.assertIn("Giảm giá trực tiếp", preview["errors"][0]["message"])
        with self.assertRaisesRegex(ValueError, "Tệp CSV có lỗi"):
            self.store.commit_upload(_csv([bad]), role="ADMIN", actor="Synthetic Operator")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contract_uploads").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contracts").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM finance_contract_upload_rows").fetchone()[0], 0)

    def test_restart_keeps_preview_read_only_and_selector_stays_explicit(self) -> None:
        handle = tempfile.NamedTemporaryFile(prefix="w3-contract-", suffix=".sqlite3", delete=False)
        path = Path(handle.name)
        handle.close()
        try:
            db = sqlite3.connect(path)
            db.row_factory = sqlite3.Row
            first = FinanceContract(db)
            preview = first.preview_upload(_csv([self.row]), role="ADMIN")
            self.assertEqual(preview["valid_count"], 1)
            with self.assertRaisesRegex(ValueError, "Lưu bị khóa"):
                first.commit_upload(_csv([self.row]), role="ADMIN", actor="Synthetic Operator")
            db.close()

            reopened = sqlite3.connect(path)
            reopened.row_factory = sqlite3.Row
            second = FinanceContract(reopened)
            self.assertEqual(second.list()["total"], 0)
            self.assertEqual(reopened.execute("SELECT COUNT(*) FROM finance_contract_uploads").fetchone()[0], 0)
            self.assertEqual(reopened.execute("SELECT COUNT(*) FROM finance_contract_upload_rows").fetchone()[0], 0)
            renewal = second.renewal_candidates(role="ADMIN")
            self.assertEqual(renewal["route"], EXTENSION_ROUTE)
            self.assertEqual(renewal["data_status"], "NO_DATA")
            self.assertEqual(renewal["provenance"], UPLOAD_PROVENANCE)
            reopened.close()
        finally:
            for suffix in ("", "-wal", "-shm"):
                try:
                    Path(str(path) + suffix).unlink()
                except FileNotFoundError:
                    pass

    def test_route_manifest_exposes_upload_and_extension_boundaries(self) -> None:
        # ``route_contract`` is a module-level manifest; inspect it through
        # the public import so this test remains independent of app.py wiring.
        from modules.finance_contract import route_contract

        contract = route_contract()
        self.assertEqual(contract["routes"], ("/finance/contract", UPLOAD_ROUTE, EXTENSION_ROUTE))
        self.assertEqual(contract["upload_headers"], UPLOAD_HEADERS)
        self.assertFalse(contract["upload_can_commit"])
        self.assertEqual(contract["upload_save_blockers"], UPLOAD_SAVE_BLOCKERS)
        self.assertIn("POST /api/finance/contract/upload/preview", contract["api_hooks"])


if __name__ == "__main__":
    unittest.main()
