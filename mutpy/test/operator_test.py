import unittest
import ast

from mutpy import operator, codegen


class MutationOperatorTest(unittest.TestCase):
	
	def test_getattr_like(self):
		
		class X:
			def visit_A(self): pass
			def visit_A_1(self): pass
			def visit_A_2(self): pass
			def visit_AB(self): pass
			def visitA(self): pass
			def visit_B(self): pass
		
		x = X()
		visits_method = ['visit_A', 'visit_A_1', 'visit_A_2']
		
		for attr in operator.MutationOperator.getattr_like(x, 'visit_A'):
			self.assertIn(attr.__name__, visits_method)
			visits_method.remove(attr.__name__)

class OperatorTestCase(unittest.TestCase):
	
	def assert_mutation(self, original, mutants):
		original_ast = ast.parse(original)
		
		for mutant, _ in self.__class__.op.mutate(original_ast, None):
			mutant_code = codegen.to_source(mutant)
			self.assertIn(mutant_code, mutants)
			mutants.remove(mutant_code)
			
		self.assertListEqual(mutants, [], 'did not generate all mutants')


class ConstantReplacementTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.ConstantReplacement()
		
	def test_numbers_increment(self):
		self.assert_mutation('2 + 3 - 99', ['3 + 3 - 99', '2 + 4 - 99', '2 + 3 - 100'])
		
	def test_string_replacement(self):
		self.assert_mutation("x = 'ham' + 'egs'",
							["x = 'mutpy' + 'egs'", "x = 'ham' + 'mutpy'", "x = '' + 'egs'", "x = 'ham' + ''"])
		
	def test_resign_if_empty(self):
		self.assert_mutation("'ham' + ''", ["'mutpy' + ''", "'' + ''", "'ham' + 'mutpy'" ])

	def test_resign_first(self):
		self.assert_mutation("'' + 'ham'", ["'' + 'mutpy'", "'' + ''", "'mutpy' + 'ham'" ])
		
	def test_not_mutate_function(self):
		self.assert_mutation("@notmutate\ndef x():\n\t'ham'", [])
		
	def test_not_mutate_class(self):
		self.assert_mutation("@notmutate\nclass X:\n\t'ham'", [])	
		

class ArithmeticOperatorReplacementTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.ArithmeticOperatorReplacement()
		
	def test_add_to_sub_replacement(self):
		self.assert_mutation('x + y + z', ['x - y + z', 'x + y - z'])
		
	def test_sub_to_add_replacement(self):
		self.assert_mutation('x - y', ['x + y'])
		
	def test_mult_to_div_replacement(self):
		self.assert_mutation('x * y', ['x / y', 'x // y'])
		
	def test_div_replacement(self):
		self.assert_mutation('x / y', ['x * y', 'x // y'])
		
	def test_floor_div_to_div(self):
		self.assert_mutation('x // y', ['x / y', 'x * y'])	

	def test_mod_to_mult(self):
		self.assert_mutation('x % y', ['x * y'])
		

class BinaryOperatorReplacement(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.BinaryOperatorReplacement()
		
	def test_bin_and_to_bit_or(self):
		self.assert_mutation('x & y', ['x | y'])
	
	def test_bit_or_to_bit_and(self):
		self.assert_mutation('x | y', ['x & y'])
		
	def test_bit_xor_to_bit_and(self):
		self.assert_mutation('x ^ y', ['x & y'])
		
	def test_lshift_to_rshift(self):
		self.assert_mutation('x << y', ['x >> y'])
		
	def test_rshift_to_lshift(self):
		self.assert_mutation('x >> y', ['x << y'])
		

class LogicaOperatorReplacementTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.LogicaOperatorReplacement()
		
	def test_and_to_or(self):
		self.assert_mutation('(x and y)', ['(x or y)'])
		
	def test_or_to_and(self):
		self.assert_mutation('(x or y)', ['(x and y)'])
		
		
class ConditionalOperatorReplacementTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.ConditionalOperatorReplacement()
		
	def test_lt(self):
		self.assert_mutation('x < y', ['x > y', 'x <= y'])
		
	def test_gt(self):
		self.assert_mutation('x > y', ['x < y', 'x >= y'])
		
	def test_lte(self):
		self.assert_mutation('x <= y', ['x >= y', 'x < y'])
		
	def test_gte(self):
		self.assert_mutation('x >= y', ['x <= y', 'x > y'])

class SliceIndexReplaceTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.SliceIndexReplace()
		
	def test_slice_indexes_rotation(self):
		self.assert_mutation('x[1:2:3] = x[(-4):(-5):(-6)]',
							['x[2:3:1] = x[(-4):(-5):(-6)]', 'x[1:2:3] = x[(-5):(-6):(-4)]'])
		
class ConditionNegationTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.ConditionNegation()
		
	def test_negate_while_condition(self):
		self.assert_mutation("while x:\n    pass", ["while (not x):\n    pass"])
	
