import unittest
from example.simple import Simple


class SimpleGoodTest(unittest.TestCase):

    def setUp(self):
        self.simple = Simple(1337)

    def test_add(self):
        self.assertEqual(self.simple.add(2, 2), 4)

    def test_add_two(self):
        self.assertEqual(self.simple.add_two(2), 4)

    def test_add_etc(self):
        self.assertEqual(self.simple.add_etc('ala, kot, pies'), 'ala, kot, pies etc.')

    def test_add_str(self):
        self.assertEqual(self.simple.add('ala', 'kota'), 'alakota')

    def test_loop(self):
        self.assertEqual(self.simple.loop(), 100)

    def test_last_two(self):
        self.assertSequenceEqual(self.simple.last_two([1, 2, 3, 4]), [3, 4])

    def test_empty_string(self):
        self.assertEqual(self.simple.empty_string(), '')

    def test_get_const(self):
        self.assertEqual(self.simple.get_const(), 1337)

    def test_get_inc_const(self):
        self.assertEqual(self.simple.get_inc_const(), 1338)
        self.assertEqual(Simple.get_inc_const(), 1338)

    def test_get_magic(self):
        self.assertEqual(self.simple.get_magic(), 1337)

    def test_is_odd(self):
        self.assertTrue(self.simple.is_odd(1))

    def test_is_not_odd(self):
        self.assertFalse(self.simple.is_odd(2))

    def test_negate_number(self):
        self.assertEqual(self.simple.negate_number(10), -10)

    def test_negate_bool(self):
        self.assertEqual(self.simple.negate_bool(True), False)

    def test_negate_bitwise(self):
        self.assertEqual(self.simple.negate_bitwise(1), -2)

    def test_bool_conjunction(self):
        self.assertEqual(self.simple.bool_conjunction(True, False), True)

    def test_bitwise_conjunction(self):
        self.assertEqual(self.simple.bitwise_conjunction(1, 0), 1)

    def test_override(self):
        self.assertEqual(self.simple.foo(), 2)

    def test_overridden_call(self):
        self.simple.bar()

        self.assertEqual(self.simple.x, 2)

    def test_handle_exception(self):
        self.assertEqual(self.simple.handle_exception(), 1)

    def test_class_variable(self):
        self.assertEqual(self.simple.X, 2)
