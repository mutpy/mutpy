import unittest
import types
import sys
import ast
from mutpy import controller, operators


class MutationScoreTest(unittest.TestCase):

    def setUp(self):
        self.score = controller.MutationScore()

    def test_count_if_zero_score(self):
        self.assertEqual(self.score.count(), 0)

    def test_count(self):
        self.score.survived_mutants = 5
        self.score.killed_mutants = 5

        self.assertEqual(self.score.count(), 50)

    def test_count_after_inc(self):
        self.score.survived_mutants = 5
        self.score.killed_mutants = 4

        self.score.inc_killed()

        self.assertEqual(self.score.count(), 50)

    def test_count_if_incompetent(self):
        self.score.survived_mutants = 5
        self.score.killed_mutants = 5
        self.score.incompetent_mutants = 1

        self.assertEqual(self.score.count(), 50)

    def test_count_if_timeout(self):
        self.score.survived_mutants = 5
        self.score.killed_mutants = 4
        self.score.timeout_mutants = 1

        self.assertEqual(self.score.count(), 50)


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


class MutationScoreStoreView:

    def end(self, score, *args):
        self.score = score


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
        self.score_view = MutationScoreStoreView()
        mutator = controller.Mutator([operators.ArithmeticOperatorReplacement], percentage=100)
        self.mutation_controller = MockMutationController(target_loader=target_loader,
                                                            test_loader=test_loader,
                                                            views=[self.score_view],
                                                            mutant_generator=mutator)

    def test_run(self):
        self.mutation_controller.run()

        score = self.score_view.score
        self.assertEqual(score.all_mutants, 3)
        self.assertEqual(score.killed_mutants, 2)
        self.assertEqual(score.survived_mutants, 1)

