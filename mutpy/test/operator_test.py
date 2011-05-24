import unittest
import ast

from mutpy import operator, codegen

EOL = '\n'
INDENT = ' ' * 4
PASS = 'pass'

class MutationOperatorTest(unittest.TestCase):
	
	def test_getattr_like(self):
		
		class X:
			def mutate_A(self): pass
			def mutate_A_1(self): pass
			def mutate_A_2(self): pass
			def mutate_AB(self): pass
			def mutateA(self): pass
			def mutate_B(self): pass
		
		x = X()
		visits_method = ['mutate_A', 'mutate_A_1', 'mutate_A_2']
		
		for attr in operator.MutationOperator.getattr_like(x, 'mutate_A'):
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
		self.assert_mutation("@notmutate" + EOL + "def x():" + EOL + INDENT + "'ham'", [])
		
	def test_not_mutate_class(self):
		self.assert_mutation("@notmutate" + EOL + "class X:" + EOL + INDENT + "'ham'", [])
		

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
		
	def test_eq(self):
		self.assert_mutation('x == y', ['x != y'])
		
	def test_not_eq(self):
		self.assert_mutation('x != y', ['x == y'])


class UnaryOperatorReplacementTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.UnaryOperatorReplacement()
		
	def test_usub(self):
		self.assert_mutation('(-x)', ['(+x)'])
		
	def test_uadd(self):
		self.assert_mutation('(+x)', ['(-x)'])


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
		
	def test_negate_if_condition(self):
		self.assert_mutation('if x:\n    pass', ['if (not x):\n    pass'])


class MembershipTestReplacementTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.MembershipTestReplacement()
	
	def test_in_to_not_in(self):
		self.assert_mutation('x in y', ['x not in y'])
		
	def test_not_in_to_in(self):
		self.assert_mutation('x not in y', ['x in y'])
		
		
class ExceptionHandleDeletionTest(OperatorTestCase):

	@classmethod
	def setUpClass(cls):
		cls.op = operator.ExceptionHandleDeletion()
		
	def test_delete_except(self):
		self.assert_mutation('try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL + INDENT + PASS,
							['try:' + EOL + INDENT + PASS])
		
	def test_delete_two_except(self):
		self.assert_mutation('try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL 
							+ INDENT + PASS + EOL + 'except Y:' + EOL + INDENT + PASS,
							['try:' + EOL + INDENT + PASS + EOL * 3 + 'except Y:' + EOL + INDENT + PASS,
							 'try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL + INDENT + PASS])
		

class ZeroIterationLoopTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.ZeroIterationLoop()
		
	def test_for_zero_iteration(self):
		self.assert_mutation('for x in y:' + EOL + INDENT + PASS, ['for x in y:' + EOL + INDENT + 'break']) 	

	def test_multiline_for_zero_iteration(self):
		self.assert_mutation('for x in y:' + EOL + INDENT + PASS + EOL + INDENT + PASS,
							['for x in y:' + EOL + INDENT + 'break'])
		
	def test_while_zero_iteration(self):
		self.assert_mutation('while x:' + EOL + INDENT + PASS, ['while x:' + EOL + INDENT + 'break'])
		

class OneIterationLoopTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.OneIterationLoop()
		
	def test_for_one_iteration(self):
		self.assert_mutation('for x in y:' + EOL + INDENT + PASS,
							['for x in y:' + EOL + INDENT + PASS + EOL + INDENT + 'break']) 
		
	def test_while_one_iteration(self):	
		self.assert_mutation('while x:' + EOL + INDENT + PASS,
							['while x:' + EOL + INDENT + PASS + EOL + INDENT + 'break'])
		

class ReverseIterationLoopTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.ReverseIterationLoop()
		
	def test_for_reverse(self):
		self.assert_mutation('for x in y:' + EOL + INDENT + PASS,
							['for x in reversed(y):' + EOL + INDENT + PASS])
		

class StatementDeletionTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.StatementDeletion()
		
	def test_return_deletion(self):
		self.assert_mutation('def f():' + EOL + INDENT + 'return 1', ['def f():' + EOL + INDENT + PASS])
		
	def test_assign_deletion(self):
		self.assert_mutation('x = 1', [PASS])

	def test_fuction_call_deletion(self):
		self.assert_mutation('f()', ['pass'])
	
	def test_assign_with_call_deletion(self):
		self.assert_mutation('x = f()', ['pass'])


class SelfWordDeletionTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.SelfWordDeletion()
		
	def test_self_deletion_with_attribute(self):
		self.assert_mutation('self.x', ['x'])
		
	def test_self_deletion_with_method(self):
		self.assert_mutation('self.f()', ['f()'])
		
	def test_self_deletion_with_multi_attribute(self):
		self.assert_mutation('self.x.y.z', ['x.y.z'])
		
	def test_self_deletion_with_multi_attribute_after_method(self):
		self.assert_mutation('self.f().x.y.z', ['f().x.y.z'])	
