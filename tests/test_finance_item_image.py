"""Focused finance item image migration and persistence checks."""
import base64
import sqlite3
import unittest

from modules.finance_item import ensure_schema, create_item, update_item, list_items


class FinanceItemImageTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        # Existing installation schema, before image_logo was added.
        self.db.executescript("""
        CREATE TABLE finance_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL UNIQUE,
          category TEXT NOT NULL DEFAULT '', fullname TEXT NOT NULL,
          description TEXT NOT NULL DEFAULT '', unit TEXT NOT NULL DEFAULT 'cái',
          course_ids TEXT NOT NULL DEFAULT '', branch TEXT NOT NULL DEFAULT '',
          quantity INTEGER NOT NULL DEFAULT 0, sale_price INTEGER NOT NULL DEFAULT 0,
          price_adjustment INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'Hoạt động', start_date TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        INSERT INTO finance_items(code,fullname,created_at,updated_at)
          VALUES ('BEFORE','Existing item','now','now');
        """)
        ensure_schema(self.db)

    def tearDown(self):
        self.db.close()

    def test_migrates_existing_rows_and_persists_image_on_create_update(self):
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(finance_items)")}
        self.assertIn("image_logo", columns)
        self.assertEqual(self.db.execute("SELECT image_logo FROM finance_items WHERE code='BEFORE'").fetchone()[0], "")
        image = "data:image/png;base64," + base64.b64encode(b"fixture").decode()
        item_id = create_item(self.db, {"code": "IMAGE-1", "fullname": "QA item", "image_logo": image})
        self.assertEqual(list_items(self.db, {"q": "IMAGE-1"})[0]["image_logo"], image)
        update_item(self.db, item_id, {"code": "IMAGE-1", "fullname": "QA item", "image_logo": image})
        self.assertEqual(self.db.execute("SELECT image_logo FROM finance_items WHERE id=?", (item_id,)).fetchone()[0], image)

    def test_rejects_unsupported_image_type_and_oversize_image(self):
        base = {"code": "BAD", "fullname": "Invalid image"}
        with self.assertRaises(ValueError):
            create_item(self.db, {**base, "image_logo": "data:text/html;base64,abc"})
        with self.assertRaises(ValueError):
            create_item(self.db, {**base, "image_logo": "data:image/png;base64," + "a" * 2_800_001})


if __name__ == "__main__":
    unittest.main()
