import unittest
import ast

from mutpy import codegen


EOL = '\n'
SIMPLE_ASSIGN = 'x = 1'
PASS = 'pass'
IDENT = ' ' * 4
CLASS_DEF = 'class Sample:'


class CodegenTest(unittest.TestCase):
    def assert_code_equal(self, code):
        node = ast.parse(code)
        generated = codegen.to_source(node)
        self.assertMultiLineEqual(code, generated)
    
    def test_one_line(self):
        self.assert_code_equal(SIMPLE_ASSIGN)
        
    def test_two_line(self):
        self.assert_code_equal(SIMPLE_ASSIGN + EOL + SIMPLE_ASSIGN)
        
    def test_two_line_and_empty_line(self):
        self.assert_code_equal(SIMPLE_ASSIGN + EOL + EOL + SIMPLE_ASSIGN)
    
    def test_start_extra_line(self):
        self.assert_code_equal(EOL + SIMPLE_ASSIGN)
        
    def test_double_start_extra_lin(self):
        self.assert_code_equal(EOL + EOL + SIMPLE_ASSIGN)
    
    def test_empty_class(self):
        self.assert_code_equal(CLASS_DEF + EOL + IDENT + PASS)
