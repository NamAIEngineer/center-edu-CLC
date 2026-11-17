import unittest

from modules.center_lane import route_contract, validate_data


class CareDynamicOptionsTests(unittest.TestCase):
    def test_existing_options_and_legacy_values(self):
        contract = route_contract('/cso/customer-care')
        allowed = {'class_name': ('TEST Lớp',), 'staff_name': ('TEST Nhân viên',)}
        result = validate_data(contract, {'student_name': 'TEST', 'class_name': 'TEST Lớp', 'staff_name': 'TEST Nhân viên'}, option_overrides=allowed)
        self.assertEqual(result['class_name'], 'TEST Lớp')
        for field in ('class_name', 'staff_name'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_data(contract, {'student_name': 'TEST', field: 'Không tồn tại'}, option_overrides=allowed)
        legacy = validate_data(contract, {'student_name': 'TEST'}, current={'student_name': 'TEST', 'class_name': 'Lớp cũ'}, option_overrides=allowed)
        self.assertEqual(legacy['class_name'], 'Lớp cũ')

    def test_empty_inventory_does_not_accept_fabricated_names(self):
        with self.assertRaises(ValueError):
            validate_data(route_contract('/cso/customer-care'), {'student_name': 'TEST', 'class_name': 'Không tồn tại'}, option_overrides={'class_name': (), 'staff_name': ()})

    def test_extension_staff_choices_reject_unknown_and_preserve_legacy(self):
        contract = route_contract('/callcenter/extension')
        allowed = {'staff_name': ('TEST Nhân viên',)}
        result = validate_data(contract, {'extension': 'TEST-001', 'staff_name': 'TEST Nhân viên'}, option_overrides=allowed)
        self.assertEqual(result['staff_name'], 'TEST Nhân viên')
        with self.assertRaises(ValueError):
            validate_data(contract, {'extension': 'TEST-001', 'staff_name': 'Không tồn tại'}, option_overrides=allowed)
        result = validate_data(contract, {'extension': 'TEST-002'}, current={'extension': 'TEST-001', 'staff_name': 'Nhân viên cũ'}, option_overrides=allowed)
        self.assertEqual(result['staff_name'], 'Nhân viên cũ')


if __name__ == '__main__':
    unittest.main()
