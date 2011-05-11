import unittest
import ast

from mutpy import operator, codegen


class OperatorTestCase(unittest.TestCase):
	
	def assert_mutation(self, original, mutants):
		original_ast = ast.parse(original)
		op = operator.ConstantReplacement()
		
		for mutant, _ in op.incremental_visit(original_ast):
			mutant_code = codegen.to_source(mutant)
			self.assertIn(mutant_code, mutants)
			mutants.remove(mutant_code)
			
		self.assertListEqual(mutants, [], 'did not generate all mutants')


class ConstantReplacementTest(OperatorTestCase):
	
	def test_numbers_increment(self):
		self.assert_mutation('2 + 3 - 99', ['3 + 3 - 99', '2 + 4 - 99', '2 + 3 - 100'])
		
	def test_string_replecment(self):
		self.assert_mutation("x = 'ham' + 'egs'", ["x = 'mutpy' + 'egs'", "x = 'ham' + 'mutpy'"])
