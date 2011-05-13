import unittest
import ast

from mutpy import operator, codegen


class OperatorTestCase(unittest.TestCase):
	
	def assert_mutation(self, original, mutants):
		original_ast = ast.parse(original)
		
		for mutant, _ in self.__class__.op.incremental_visit(original_ast, None):
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
		self.assert_mutation("x = 'ham' + 'egs'", ["x = 'mutpy' + 'egs'", "x = 'ham' + 'mutpy'"])
		

class ArithmeticOperatorReplacementTest(OperatorTestCase):
	
	@classmethod
	def setUpClass(cls):
		cls.op = operator.ArithmeticOperatorReplacement()
		
	def test_add_to_sub_replacement(self):
		self.assert_mutation('x + y + z', ['x - y + z', 'x + y - z'])
		

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
	
