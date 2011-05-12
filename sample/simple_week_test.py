import unittest
from sample import simple


class SimpleWeekTest(unittest.TestCase):
    
    def setUp(self):
        self.simple = simple.Simple()
        
    def test_add(self):
        self.assertEqual(self.simple.add(4, 8), 12)
