import unittest
from simple.simple import Simple


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
