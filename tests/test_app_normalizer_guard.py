"""Regression checks for route-owned training controls in the shared shell."""

from pathlib import Path
import unittest


class AppNormalizerGuardTests(unittest.TestCase):
    def test_training_api_backed_routes_bypass_observed_control_rewrite(self):
        source = (Path(__file__).parents[1] / "static" / "app.js").read_text(encoding="utf-8")
        class_guard = "if (route === '/training/class' && screen?.dataset.trainingObservedRoute === '/training/class') return;"
        student_guard = "if (route === '/center/student/index') return;"
        guard = "if (route === '/training/timetable' || route === '/training/attendance') return;"
        start = source.index("async function normalizeObservedControls(screen, route) {")
        normalizer = source[start:]
        self.assertIn(class_guard, source)
        self.assertIn(student_guard, source)
        self.assertIn(guard, source)
        self.assertLess(normalizer.index(class_guard), normalizer.index("const spec = await observedSpec(route);"))
        self.assertLess(normalizer.index(student_guard), normalizer.index("const spec = await observedSpec(route);"))
        self.assertLess(normalizer.index(guard), normalizer.index("const spec = await observedSpec(route);"))

    def test_unrelated_route_normalization_remains_available(self):
        source = (Path(__file__).parents[1] / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("const expected = Array.isArray(spec?.filters) ? spec.filters : [];", source)
        self.assertIn("const setObservedShape = (control, filter, index) => {", source)


if __name__ == "__main__":
    unittest.main()
