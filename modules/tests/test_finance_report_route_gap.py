from __future__ import annotations

import sqlite3
import unittest

from modules.finance_report_adapter import FINANCE_ROUTE_ALIASES, register
from modules.report_engine import load_report_engine


class _Service:
    def __init__(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.report_engine_v2 = load_report_engine(_Provider())


class _Provider:
    def query_report(self, **_kwargs):
        return []


class _FallbackProvider:
    def query_report(self, **_kwargs):
        # Simulate the generic report provider returning a row for a finance
        # entity.  The owned adapter must suppress this cross-domain fallback
        # when its persistent finance source is empty.
        return [{"contract_code": "WRONG_DOMAIN_FALLBACK"}]


class _FallbackService:
    def __init__(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.report_engine_v2 = load_report_engine(_FallbackProvider())


class FinanceReportRouteGapTests(unittest.TestCase):
    def test_register_adds_observed_index_aliases_to_loaded_catalog(self) -> None:
        service = _Service()
        result = register(service=service)
        for alias, canonical in FINANCE_ROUTE_ALIASES.items():
            self.assertIn(alias, service.report_engine_v2.definitions)
            self.assertEqual(service.report_engine_v2.definition(alias).entity,
                             service.report_engine_v2.definition(canonical).entity)
        self.assertEqual(result["route_aliases_installed"], True)

    def test_alias_runs_truthful_no_data(self) -> None:
        service = _Service()
        register(service=service)
        result = service.report_engine_v2.run("/report/finance/student_finance/index")
        self.assertEqual(result["data_status"], "NO_DATA")
        self.assertEqual(result["rows"], [])

    def test_empty_finance_source_suppresses_generic_fallback(self) -> None:
        service = _FallbackService()
        register(service=service)
        result = service.report_engine_v2.run("/report/finance/revenue/index")
        self.assertEqual(result["data_status"], "NO_DATA")
        self.assertEqual(result["rows"], [])


if __name__ == "__main__":
    unittest.main()
