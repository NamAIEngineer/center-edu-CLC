import unittest

from app import generated_route_seed_value


class GeneratedRouteSeedQualityTests(unittest.TestCase):
    def test_confirmed_routes_have_domain_values_for_table_fields(self):
        cases = {
            "/training/announcement": ("thong_bao", "Lịch học tháng 11"),
            "/training/post": ("noi_dung", "Tài liệu ôn tập buổi 3"),
            "/crm/event2/index": ("noi_dung", "Đăng ký lớp tiếng Anh nền tảng"),
            "/crm/discount": ("ten_uu_ai", "Ưu đãi học viên mới"),
            "/crm/packet": ("goi_hoc_phi", "Gói tiếng Anh nền tảng"),
        }
        for route, (key, expected) in cases.items():
            value = generated_route_seed_value(route, key, 1)
            self.assertEqual(value, expected, route)
            self.assertNotRegex(str(value), r"Demo\s*\d+")

    def test_unknown_route_key_remains_unset(self):
        self.assertEqual(generated_route_seed_value("/training/announcement", "unknown", 1), "")


if __name__ == "__main__":
    unittest.main()
