import unittest
import types
import sys
from mutpy import controller, operators, utils, codegen


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

    def test_update_coverage(self):
        self.score.update_coverage(1, 1)

        self.assertEqual(self.score.covered_nodes, 1)
        self.assertEqual(self.score.all_nodes, 1)


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
        return utils.create_ast(self.target_loader.get_source())


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
        mutator = controller.FirstOrderMutator([operators.ArithmeticOperatorReplacement], percentage=100)
        self.mutation_controller = MockMutationController(target_loader=target_loader,
                                                            test_loader=test_loader,
                                                            views=[self.score_view],
                                                            mutant_generator=mutator,
                                                            mutate_covered=True)

    def test_run(self):
        self.mutation_controller.run()

        score = self.score_view.score
        self.assertEqual(score.all_mutants, 3)
        self.assertEqual(score.killed_mutants, 2)
        self.assertEqual(score.survived_mutants, 1)


class FirstToLastHOMStrategyTest(unittest.TestCase):

    def test_generate(self):
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, lineno=1, marker=1),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, lineno=1, marker=2),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, lineno=1, marker=3),
        ]
        hom_strategy = controller.FirstToLastHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply[0]), 2)
        self.assertEqual(changes_to_apply[0][0].marker, 1)
        self.assertEqual(changes_to_apply[0][1].marker, 3)
        self.assertEqual(len(changes_to_apply[1]), 1)
        self.assertEqual(changes_to_apply[1][0].marker, 2)


class FirstOrderMutatorTest(unittest.TestCase):

    def test_first_order_mutation(self):
        mutator = controller.FirstOrderMutator(
            operators=[operators.ArithmeticOperatorReplacement, operators.AssignmentOperatorReplacement],
        )
        target_ast = utils.create_ast('x += y + z')

        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            if number == 0:
                self.assertEqual('x += y - z', codegen.to_source(mutant))
                self.assertEqual(mutations[0].lineno, 1)
            elif number == 1:
                self.assertEqual('x -= y + z', codegen.to_source(mutant))
                self.assertEqual(mutations[0].lineno, 1)
            else:
                self.fail()

        self.assertEqual(codegen.to_source(target_ast), 'x += y + z')


class HighOrderMutatorTest(unittest.TestCase):

    def test_second_order_mutation(self):
        mutator = controller.HighOrderMutator(
            operators=[operators.ArithmeticOperatorReplacement, operators.AssignmentOperatorReplacement],
        )
        target_ast = utils.create_ast('x += y + z')

        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            if number == 0:
                self.assertEqual('x -= y - z', codegen.to_source(mutant))
                self.assertEqual(mutations[0].lineno, 1)
                self.assertEqual(mutations[1].lineno, 1)
            else:
                self.fail()

        self.assertEqual(codegen.to_source(target_ast), 'x += y + z')

    def test_second_order_mutation_with_first_to_last_strategy(self):
        mutator = controller.HighOrderMutator(
            operators=[operators.ArithmeticOperatorReplacement],
        )
        target_ast = utils.create_ast('a + b + c + d + e')
        number = None
        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            if number == 0:
                self.assertEqual('a - b + c + d - e', codegen.to_source(mutant))
                self.assertEqual(mutations[0].lineno, 1)
                self.assertEqual(mutations[1].lineno, 1)
            elif number == 1:
                self.assertEqual('a + b - c - d + e', codegen.to_source(mutant))
                self.assertEqual(mutations[0].lineno, 1)
                self.assertEqual(mutations[1].lineno, 1)
        if number != 1:
            self.fail('no mutations!')
        self.assertEqual(codegen.to_source(target_ast), 'a + b + c + d + e')
