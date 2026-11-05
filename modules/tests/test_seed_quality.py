from __future__ import annotations

import unittest

from modules.seed_quality import sanitize_payload, sanitize_value


class SeedQualityTests(unittest.TestCase):
    def test_fixture_markers_are_removed_from_presentation_values(self) -> None:
        payload = {
            "student_code": "HV-DEMO-007",
            "student_name": "Demo Learner 007",
            "contract_code": "DEMO-CONTRACT-003",
            "note": "Dữ liệu demo tổng hợp 03",
            "status": "IN_PROGRESS",
        }
        result = sanitize_payload(payload)
        self.assertEqual(result["student_code"], "HV-007")
        self.assertIn(result["student_name"], {"Nguyễn Minh Anh", "Trần Gia Hân", "Lê Hoàng Nam", "Phạm Khánh Linh"})
        self.assertEqual(result["contract_code"], "DL-CONTRACT-003")
        self.assertEqual(result["note"], "")
        self.assertEqual(result["status"], "IN_PROGRESS")

    def test_stable_id_and_unknown_are_unchanged(self) -> None:
        self.assertEqual(sanitize_value("DEMO-CLASS-01", field_name="class_id"), "DEMO-CLASS-01")
        self.assertEqual(sanitize_value("UNKNOWN", field_name="status"), "UNKNOWN")
        self.assertIsNone(sanitize_value(None, field_name="name"))

    def test_normal_values_and_nested_payload_are_unchanged(self) -> None:
        payload = {"name": "Nguyễn An", "items": [{"label": "Lớp IELTS", "status": "ACTIVE"}]}
        self.assertEqual(sanitize_payload(payload), payload)

    def test_teacher_and_vietnamese_demo_names_are_sanitized(self) -> None:
        self.assertNotEqual(sanitize_value("Demo Teacher 4", field_name="teacher_name"), "Demo Teacher 4")
        self.assertNotEqual(sanitize_value("Giáo viên Demo 10", field_name="teacher_name"), "Giáo viên Demo 10")
        self.assertNotEqual(sanitize_value("Học viên Demo 2", field_name="student_name"), "Học viên Demo 2")

    def test_api_payload_sanitizes_nested_rows_without_changing_contract_fields(self) -> None:
        payload = {
            "data": {
                "items": [
                    {
                        "id": "DEMO-CLASS-01",
                        "student_id": "HV-DEMO-007",
                        "identifier": "ID-DEMO-007",
                        "student_code": "HV-DEMO-007",
                        "student_name": "Demo Learner 007",
                        "bill_code": "DEMO-INV-007",
                        "reserve_code": "BL-DEMO-001",
                        "status": "PENDING",
                        "transport": "BANK_TRANSFER",
                        "unknown": "UNKNOWN",
                        "note": "Dữ liệu demo nội bộ",
                        "value": None,
                        "label": "Lớp IELTS",
                    },
                    {
                        "customer_code": "LEAD-DEMO-002",
                        "customer_name": "Demo Customer 002",
                        "teacher_name": "Demo Teacher",
                        "contract_ref": "HD-DEMO-002",
                        "assessment_code": "DG-DEMO-003",
                        "item_code": "IT-DEMO-004",
                        "transfer_code": "CN-DEMO-005",
                    },
                ]
            }
        }

        result = sanitize_payload(payload)
        first, second = result["data"]["items"]

        # IDs and transport contract values are opaque to this presentation layer.
        self.assertEqual(first["id"], "DEMO-CLASS-01")
        self.assertEqual(first["student_id"], "HV-DEMO-007")
        self.assertEqual(first["identifier"], "ID-DEMO-007")
        self.assertEqual(first["status"], "PENDING")
        self.assertEqual(first["transport"], "BANK_TRANSFER")
        self.assertEqual(first["unknown"], "UNKNOWN")
        self.assertIsNone(first["value"])

        # Fixture wording and fixture-only code segments are removed recursively.
        self.assertEqual(first["student_code"], "HV-007")
        self.assertIn(first["student_name"], {"Nguyễn Minh Anh", "Trần Gia Hân", "Lê Hoàng Nam", "Phạm Khánh Linh"})
        self.assertEqual(first["bill_code"], "DL-INV-007")
        self.assertEqual(first["reserve_code"], "BL-001")
        self.assertEqual(first["note"], "")
        self.assertEqual(first["label"], "Lớp IELTS")

        self.assertEqual(second["customer_code"], "KH-002")
        self.assertIn(second["customer_name"], {"Nguyễn Văn Minh", "Trần Thị Lan", "Lê Quốc Bảo", "Phạm Thu Hà"})
        self.assertIn(second["teacher_name"], {"Nguyễn Văn Cường", "Ms Nga", "Trần Minh Quân", "Lê Thu Hà"})
        self.assertEqual(second["contract_ref"], "HD-002")
        self.assertEqual(second["assessment_code"], "DG-003")
        self.assertEqual(second["item_code"], "IT-004")
        self.assertEqual(second["transfer_code"], "CN-005")

    def test_status_transport_suffixes_and_unknown_are_opaque(self) -> None:
        payload = {
            "confirmation_status": "REJECTED",
            "payment_transport": "CASH",
            "unknown_value": "unknown",
            "nested": [{"class_status": "IN_PROGRESS", "source": "Dữ LIỆU DEMO"}],
        }
        self.assertEqual(sanitize_payload(payload), {
            "confirmation_status": "REJECTED",
            "payment_transport": "CASH",
            "unknown_value": "unknown",
            "nested": [{"class_status": "IN_PROGRESS", "source": ""}],
        })

    def test_unobserved_code_prefix_is_not_rewritten(self) -> None:
        self.assertEqual(sanitize_value("ABC-DEMO-001", field_name="reference_code"), "ABC-DEMO-001")
        self.assertEqual(sanitize_value("HV-DEMO-001", field_name="valid"), "HV-001")
        self.assertEqual(sanitize_value("HV-DEMO-001", field_name="validity"), "HV-001")


if __name__ == "__main__":
    unittest.main()
