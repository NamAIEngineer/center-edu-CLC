"""U14 regression: empty revenue discount type stays optional end to end."""
from pathlib import Path
import re
import sqlite3
import unittest

from modules.finance_revenue import FinanceRevenue


class U14DiscountOptionalTests(unittest.TestCase):
    def test_revenue_select_metadata_is_optional_without_changing_options(self):
        source = (Path(__file__).parents[2] / "static" / "app.js").read_text()
        match = re.search(
            r"\{name:'discount_type',label:'Kiểu giảm',value:x\.discount_type\|\|'',"
            r"(?P<meta>[^}]*)options:\[\{value:'',label:'Không giảm'\},"
            r"\{value:'FIXED',label:'Số tiền'\},\{value:'PERCENT',label:'Phần trăm'\}\]\}",
            source,
        )
        self.assertIsNotNone(match)
        self.assertIn("required:false", match.group("meta"))
        self.assertNotIn("required:true", match.group("meta"))

    def test_api_contract_accepts_empty_discount_type(self):
        db = sqlite3.connect(":memory:")
        try:
            revenue = FinanceRevenue(db)
            row = revenue.create(
                {"code": "U14-OPTIONAL", "name": "Không giảm", "price": 100000, "amount_due": 100000},
                role="ADMIN",
                actor="u14-test",
            )
            self.assertEqual(row["discount_type"], "")
            self.assertIsNone(row["discount_value"])
            fixed = revenue.create(
                {"code": "U14-FIXED", "name": "Giảm tiền", "price": 100000, "discount_type": "FIXED", "discount_value": 5000},
                role="ADMIN",
                actor="u14-test",
            )
            self.assertEqual((fixed["discount_type"], fixed["discount_value"]), ("FIXED", 5000))
            percent = revenue.create(
                {"code": "U14-PERCENT", "name": "Giảm phần trăm", "price": 100000, "discount_type": "PERCENT", "discount_value": 10},
                role="ADMIN",
                actor="u14-test",
            )
            self.assertEqual((percent["discount_type"], percent["discount_value"]), ("PERCENT", 10))
            with self.assertRaises(ValueError):
                revenue.create(
                    {"code": "U14-BAD-PERCENT", "name": "Quá mức", "price": 100000, "discount_type": "PERCENT", "discount_value": 101},
                    role="ADMIN",
                    actor="u14-test",
                )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
