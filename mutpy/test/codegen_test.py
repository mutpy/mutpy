import unittest
import ast

from mutpy import codegen
from curses.ascii import SI


EOL = '\n'
SIMPLE_ASSIGN = 'x = 1'
PASS = 'pass'
IDENT = ' ' * 4
CLASS_DEF = 'class Sample:'
EMPTY_CLASS = CLASS_DEF + EOL + IDENT + PASS
FUNC_DEF = 'def f():'
EMPTY_FUNC = FUNC_DEF + EOL + IDENT + PASS

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
        self.assert_code_equal(EMPTY_CLASS)
        
    def test_extra_line_befor_empty_class(self):
        self.assert_code_equal(EOL + EMPTY_CLASS)
        
    def test_extra_line_after_empty_class(self):
        self.assert_code_equal(EOL + EMPTY_CLASS)
        
    def test_extra_line_inside_empty_clas(self):
        self.assert_code_equal(CLASS_DEF + EOL + IDENT + EOL + IDENT + PASS)
        
    def test_empty_func(self):
        self.assert_code_equal(EMPTY_FUNC)
    
    def test_extra_line_before_empty_func(self):
        self.assert_code_equal(EOL + EMPTY_FUNC)
        
    def test_simple_class(self):
        self.assert_code_equal(CLASS_DEF + EOL + IDENT + FUNC_DEF + EOL + IDENT + IDENT + SIMPLE_ASSIGN)
