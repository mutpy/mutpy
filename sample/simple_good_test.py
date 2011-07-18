import unittest
from sample import simple


class SimpleGoodTest(unittest.TestCase):
    
    def setUp(self):
        self.simple = simple.Simple()
        
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
        self.assertSameElements(self.simple.last_two([1, 2, 3, 4]), [3, 4])
        
    def test_empty_string(self):
        self.assertEqual(self.simple.empty_string(), '')
        
    def test_get_const(self):
        self.assertEqual(self.simple.get_const(), 1337)
