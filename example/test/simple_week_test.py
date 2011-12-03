import unittest
from example.simple import Simple


class SimpleWeekTest(unittest.TestCase):

    def setUp(self):
        self.simple = Simple(1337)

    def test_add(self):
        self.assertEqual(self.simple.add(4, 8), 12)

