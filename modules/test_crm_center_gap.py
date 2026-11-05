"""Focused source-contract checks for CRM and Center teacher persistence."""

import sqlite3
import unittest
from types import SimpleNamespace

from modules.center_setup_next import TeacherStore
from modules.crm_domain import CRMStore, register


class CrmCenterGapTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def test_teacher_store_crud_filter_export_and_role_boundary(self):
        store = TeacherStore(self.db)
        created = store.create({
            "fullname": "Lê Hoàng Anh", "username": "hoanganh",
            "phone": "0903987654", "nationality": "Việt Nam",
            "role": "Giáo viên chủ nhiệm", "status": "Kích hoạt",
        })
        self.assertEqual(store.list({"q": "hoanganh"}, role="STAFF")[0]["id"], created["id"])
        self.assertIn("Lê Hoàng Anh", store.export({"status": "Kích hoạt"}, role="STAFF"))
        updated = store.update(created["id"], {"status": "Đang khóa"}, role="STAFF")
        self.assertEqual(updated["status"], "Đang khóa")
        with self.assertRaises(PermissionError):
            store.delete(created["id"], role="STAFF")
        store.delete(created["id"], role="ADMIN")
        self.assertEqual(store.list(role="ADMIN"), [])
        with self.assertRaises(PermissionError):
            store.list(role="STUDENT")

    def test_crm_update_rejects_unknown_fields_instead_of_silently_dropping(self):
        store = CRMStore(self.db)
        prospect = store.create_prospect(role="ADMIN", full_name="Nguyễn Minh Anh")
        with self.assertRaises(ValueError):
            store.update_prospect(prospect["id"], role="ADMIN", unsupported="x")
        appointment = store.create_appointment(
            role="ADMIN", prospect_id=prospect["id"], appointment_at="2026-11-15 09:30",
            action_type="Gọi", note="Tư vấn", created_by="Admin",
        )
        with self.assertRaises(ValueError):
            store.update_appointment(appointment["id"], role="ADMIN", unsupported="x")

    def test_crm_register_mounts_idempotent_store_and_metadata(self):
        registry = {}

        def register_module(name, *, metadata):
            registry[name] = {"name": name, "registered": True, **metadata}
            return registry[name]

        service = SimpleNamespace(db=self.db, register_module=register_module)
        first = register(service, service)
        mounted = service.crm_store
        second = register(service, service)

        self.assertIs(mounted, service.crm_store)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PERSISTENT_LOCAL_CONTRACT")
        self.assertEqual(first["routes"], [
            "/crm/potential/index", "/sale/potential/index",
            "/crm/potential/appointment", "/sale/potential/appointment",
        ])
        self.assertEqual(first["schema"], "crm_prospects,crm_care_appointments")
        tables = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"crm_prospects", "crm_care_appointments"}.issubset(tables))


if __name__ == "__main__":
    unittest.main()
