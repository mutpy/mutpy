import unittest
import types
import sys
import ast
from mutpy import controller, operators


class MutationScoreTest(unittest.TestCase):

    def test_score(self):
        score = controller.MutationScore(all_mutants=11, killed_mutants=5, incompetent_mutants=1)
        self.assertEqual(score.count(), 50)
        score.inc_killed()
        self.assertEqual(score.count(), 60)

    def test_zero_score(self):
        score = controller.MutationScore(all_mutants=0)
        self.assertEqual(score.count(), 0)


class MockModulesLoader:

    def __init__(self, name, source):
        self.names = [name]
        self.source = source
        self.module = types.ModuleType(name)
        exec(self.source, self.module.__dict__)
        self.module.__file__ = '<string>'
        sys.modules[name] = self.module

    def load(self):
        return [(self.module, None)]

    def get_source(self):
        return self.source


class MockMutationController(controller.MutationController):

    def create_target_ast(self, target_module):
        return ast.parse(self.target_loader.get_source())


class CountingView:

    def __init__(self):
        self.total_mutation = 0
    
    def mutation(self, number, op, filename, lineno, mutant):
        self.total_mutation += 1


class MutationControllerTest(unittest.TestCase):
    TARGET_SRC = 'def mul(x): return x * x'
    TEST_SRC = """
import target
from unittest import TestCase
class MulTest(TestCase):
    def test_mul(self):
        self.assertEqual(target.mul(2), 4)
"""

    def setUp(self):
        target_loader = MockModulesLoader('target', self.TARGET_SRC)
        test_loader = MockModulesLoader('test', self.TEST_SRC)
        self.counting_view = CountingView()
        mutator = controller.Mutator([operators.ArithmeticOperatorReplacement])
        self.mutation_controller = MockMutationController(target_loader=target_loader,
                                                            test_loader=test_loader,
                                                            views=[self.counting_view],
                                                            mutant_generator=mutator)

    def test_sth(self):
        self.mutation_controller.run()

        self.assertEqual(self.counting_view.total_mutation, 3)

