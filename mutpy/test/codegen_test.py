import unittest
import ast

from mutpy import codegen


EOL = '\n'
SIMPLE_ASSIGN = 'x = 1'
PASS = 'pass'
INDENT = ' ' * 4
CLASS_DEF = 'class Sample:'
EMPTY_CLASS = CLASS_DEF + EOL + INDENT + PASS
FUNC_DEF = 'def f():'
EMPTY_FUNC = FUNC_DEF + EOL + INDENT + PASS

#print('path in test:', sys.path)
#print('codegen in test:', codegen.__file__)

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
        self.assert_code_equal(CLASS_DEF + EOL + INDENT + EOL + INDENT + PASS)

    def test_empty_func(self):
        self.assert_code_equal(EMPTY_FUNC)

    def test_extra_line_before_empty_func(self):
        self.assert_code_equal(EOL + EMPTY_FUNC)

    def test_simple_class(self):
        self.assert_code_equal(CLASS_DEF + EOL + INDENT + FUNC_DEF + EOL + INDENT + INDENT + SIMPLE_ASSIGN)

    def test_import(self):
        self.assert_code_equal("import x")

    def test_import_package(self):
        self.assert_code_equal("import x.y.z")

    def test_import_from(self):
        self.assert_code_equal("from y import x")

    def test_import_multi_from(self):
        self.assert_code_equal("from y import x, z, q")

    def test_import_from_as(self):
        self.assert_code_equal("from y import x as z")

    def test_import_multi_from_as(self):
        self.assert_code_equal("from y import x as z, a as b")

    def test_delete(self):
        self.assert_code_equal("del x")

    def test_delete_multi(self):
        self.assert_code_equal("del x, y, z")

    def test_while_with_compare(self):
        self.assert_code_equal("while (not i != 1):" + EOL + INDENT + SIMPLE_ASSIGN)

    def test_extra_line_before_while(self):
        self.assert_code_equal(SIMPLE_ASSIGN + EOL + EOL + "while False:" + EOL + INDENT + PASS)

    def test_if_without_else(self):
        self.assert_code_equal("if x:" + EOL + INDENT + PASS)

    def test_if_with_else(self):
        self.assert_code_equal("if x:" + EOL + INDENT + PASS + EOL + "else:" + EOL + INDENT + PASS)

    def test_if_with_one_elif(self):
        self.assert_code_equal("if x:" + EOL + INDENT + PASS + EOL + "elif y:" + EOL + INDENT + PASS)

    def test_if_with_one_elif_and_else(self):
        self.assert_code_equal("if x:" + EOL + INDENT + PASS + EOL + "elif y:" + EOL + INDENT + PASS
                               + EOL + "else:" + EOL + INDENT + PASS)

    def test_if_with_two_elif(self):
        self.assert_code_equal("if x:" + EOL + INDENT + PASS + EOL + "elif y:" + EOL + INDENT + PASS
                               + EOL + "elif z:" + EOL + INDENT + PASS)

    def test_if_with_two_elif_and_else(self):
        self.assert_code_equal("if x:" + EOL + INDENT + PASS + EOL + "elif y:" + EOL + INDENT + PASS
                               + EOL + "elif z:" + EOL + INDENT + PASS + EOL + "else:" + EOL + INDENT + PASS)

    def test_try_with_one_except(self):
        self.assert_code_equal("try:" + EOL + INDENT + PASS + EOL + "except Y:" + EOL + INDENT + PASS)

    def test_try_with_extra_lines(self):
        self.assert_code_equal("try:" + EOL + INDENT + PASS + EOL + EOL + EOL + "except Y:" + EOL + INDENT + PASS)

    def test_for_break(self):
        self.assert_code_equal("for x in y:" + EOL + INDENT + "break")

    def test_remove_extra_lines(self):
        code = EOL + INDENT + EOL + INDENT + 'pass' + EOL + INDENT + EOL + INDENT + 'pass' + EOL + EOL
        reduced = codegen.remove_extra_lines(code)
        self.assertEqual(reduced, INDENT + 'pass' + EOL + INDENT + 'pass')

    def test_empty_return(self):
        self.assert_code_equal("def f():" + EOL + INDENT + 'return')
