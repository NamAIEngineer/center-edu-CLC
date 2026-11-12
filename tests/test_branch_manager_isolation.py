import os
import sqlite3
import tempfile
import unittest

from modules.branch_manager import Actor, BranchManagerStore, ScopeDenied


class BranchManagerIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(prefix="bm-wave3-", suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.db = sqlite3.connect(self.tmp.name)
        self.store = BranchManagerStore(self.db)
        self.db.executemany("INSERT INTO bm_tenants(id,name) VALUES(?,?)", [(1, "Tenant A"), (2, "Tenant B")])
        self.db.executemany(
            "INSERT INTO bm_branches(id,tenant_id,code,name) VALUES(?,?,?,?)",
            [(11, 1, "A1", "Branch A1"), (21, 2, "B1", "Branch B1")],
        )
        self.db.execute(
            "INSERT INTO bm_manager_assignments(tenant_id,branch_id,user_id,role) VALUES(?,?,?,?)",
            (1, 11, 101, "BRANCH_MANAGER"),
        )
        self.db.commit()
        self.manager_a = Actor(101, 1, "BRANCH_MANAGER")
        self.admin_a = Actor(1, 1, "ADMIN")
        self.manager_b = Actor(201, 2, "BRANCH_MANAGER")

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_create_read_search_update_and_restart_persist(self):
        record_id = self.store.create(self.manager_a, branch_id=11, label="TEST_BM_A1", value="v1")
        self.assertEqual(self.store.list_records(self.manager_a, query="TEST_BM_A1")[0]["id"], record_id)
        self.store.update(self.manager_a, record_id, value="v2")
        self.assertEqual(self.store.read(self.manager_a, record_id)["value"], "v2")
        self.db.close()
        self.db = sqlite3.connect(self.tmp.name)
        self.store = BranchManagerStore(self.db)
        self.assertEqual(self.store.read(self.manager_a, record_id)["value"], "v2")

    def test_cross_branch_and_cross_tenant_fail_closed(self):
        record_id = self.store.create(self.manager_a, branch_id=11, label="TEST_SCOPE", value="a")
        with self.assertRaises(ScopeDenied):
            self.store.read(self.manager_b, record_id)
        with self.assertRaises(ScopeDenied):
            self.store.create(self.manager_a, branch_id=21, label="FORGED_B1")
        self.assertEqual(self.store.list_records(self.manager_b), [])

    def test_admin_same_tenant_and_bulk_rollback(self):
        first = self.store.create(self.admin_a, branch_id=11, label="TEST_A", value="a")
        with self.assertRaises(ScopeDenied):
            self.store.bulk_update(self.admin_a, [first, 999999], value="should-rollback")
        self.assertEqual(self.store.read(self.admin_a, first)["value"], "a")
        csv_text = self.store.export_csv(self.admin_a, branch_id=11)
        self.assertIn("TEST_A", csv_text)

    def test_delete_exact_fixture_only(self):
        record_id = self.store.create(self.manager_a, branch_id=11, label="TEST_DELETE", value="x")
        self.store.delete(self.manager_a, record_id)
        self.assertEqual(self.store.list_records(self.manager_a, query="TEST_DELETE"), [])


if __name__ == "__main__":
    unittest.main()
