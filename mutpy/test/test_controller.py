import ast
import sys
import types
import unittest

from mutpy import controller, operators, utils, codegen
from mutpy.test.utils import MockModulesLoader
from mutpy.test_runners import UnittestTestRunner


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


class MockMutationController(controller.MutationController):
    def create_target_ast(self, target_module):
        return utils.create_ast(self.target_loader.get_source())


class MutationScoreStoreView:
    def end(self, score, *args):
        self.score = score


class MutationControllerTest(unittest.TestCase):
    TARGET_SRC = 'def mul(x): return x * x'
    TEST_SRC = utils.f("""
    import target
    from unittest import TestCase
    class MulTest(TestCase):
        def test_mul(self):
            self.assertEqual(target.mul(2), 4)
        def test_not_used(self):
            pass
    """)

    def setUp(self):
        target_loader = MockModulesLoader('target', self.TARGET_SRC)
        test_loader = MockModulesLoader('test', self.TEST_SRC)
        self.score_view = MutationScoreStoreView()
        mutator = controller.FirstOrderMutator([operators.ArithmeticOperatorReplacement], percentage=100)
        self.mutation_controller = MockMutationController(
            runner_cls=UnittestTestRunner,
            target_loader=target_loader,
            test_loader=test_loader,
            views=[self.score_view],
            mutant_generator=mutator,
            mutate_covered=True,
        )

    def test_run(self):
        self.mutation_controller.run()

        score = self.score_view.score
        self.assertEqual(score.all_mutants, 3)
        self.assertEqual(score.killed_mutants, 2)
        self.assertEqual(score.survived_mutants, 1)


class BaseHOMStrategyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TWO_AOR_MUTATIONS_ON_SUBTRACTION = [
            cls.aor_mutation_on_subtraction(),
            cls.aor_mutation_on_subtraction(),
        ]
        cls.THREE_AOR_MUTATIONS_ON_SUBTRACTION = cls.TWO_AOR_MUTATIONS_ON_SUBTRACTION + [
            cls.aor_mutation_on_subtraction()
        ]

    @staticmethod
    def aor_mutation(node):
        return operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=node)

    @staticmethod
    def asr_mutation(node):
        return operators.Mutation(operator=operators.AssignmentOperatorReplacement, node=node)

    @staticmethod
    def crp_mutation(node):
        return operators.Mutation(operator=operators.ConstantReplacement, node=node)

    @staticmethod
    def aor_mutation_on_subtraction():
        return operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[]))

    @staticmethod
    def apply_strategy_to_mutations(hom_strategy_cls, mutations, order, hom_kwargs=None):
        if hom_kwargs is None:
            hom_kwargs = {}
        hom_strategy = hom_strategy_cls(order=order, **hom_kwargs)
        return list(hom_strategy.generate(mutations))

    def apply_strategy_to_mutations_with_order_2(self, hom_strategy_cls, mutations, hom_kwargs=None):
        if hom_kwargs is None:
            hom_kwargs = {}
        return self.apply_strategy_to_mutations(hom_strategy_cls, mutations, 2, hom_kwargs=hom_kwargs)

    def assert_num_changesets(self, changes, num_changes):
        self.assertEqual(len(changes), num_changes)

    def assert_num_changeset_entries(self, changes, changeset_index, num_entries):
        self.assertEqual(len(changes[changeset_index]), num_entries)

    def assert_mutation_in_changeset_at_position_equals(self, changes, changeset_index, change_index, mutation):
        self.assertEqual(changes[changeset_index][change_index], mutation)


class FirstToLastHOMStrategyTest(BaseHOMStrategyTest):
    def test_generate(self):
        mutations = self.THREE_AOR_MUTATIONS_ON_SUBTRACTION

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.FirstToLastHOMStrategy, mutations)

        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 2)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[0])
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 1, mutations[2])
        self.assert_num_changeset_entries(changes_to_apply, 1, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[1])

    def test_generate_if_same_node(self):
        node = ast.Sub()
        mutations = [
            self.aor_mutation(node=node),
            self.aor_mutation(node=node),
        ]

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.FirstToLastHOMStrategy, mutations)

        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[0])
        self.assert_num_changeset_entries(changes_to_apply, 1, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[1])

    def test_generate_if_node_child(self):
        node = ast.Sub(children=[])
        mutations = [
            self.aor_mutation(node=ast.UnaryOp(children=[node])),
            self.aor_mutation(node=node),
        ]

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.FirstToLastHOMStrategy, mutations)

        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[0])
        self.assert_num_changeset_entries(changes_to_apply, 1, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[1])


class EachChoiceHOMStrategyTest(BaseHOMStrategyTest):
    def test_generate(self):
        mutations = self.THREE_AOR_MUTATIONS_ON_SUBTRACTION

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.EachChoiceHOMStrategy, mutations)

        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 2)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[0])
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 1, mutations[1])
        self.assert_num_changeset_entries(changes_to_apply, 1, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[2])


class BetweenOperatorsHOMStrategyTest(BaseHOMStrategyTest):
    def test_generate_if_one_operator(self):
        mutations = self.TWO_AOR_MUTATIONS_ON_SUBTRACTION

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.BetweenOperatorsHOMStrategy,
                                                                         mutations)
        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[0])
        self.assert_num_changeset_entries(changes_to_apply, 1, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[1])

    def test_generate_if_two_operators(self):
        mutations = self.TWO_AOR_MUTATIONS_ON_SUBTRACTION + [self.asr_mutation(node=ast.Sub(children=[]))]

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.BetweenOperatorsHOMStrategy,
                                                                         mutations)
        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 2)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[0])
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 1, mutations[2])
        self.assert_num_changeset_entries(changes_to_apply, 1, 2)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[1])
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 1, mutations[2])

    def test_generate_if_three_operators(self):
        mutations = self.TWO_AOR_MUTATIONS_ON_SUBTRACTION + [
            self.asr_mutation(node=ast.Sub(children=[])),
            self.crp_mutation(node=ast.Sub(children=[])),
        ]

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.BetweenOperatorsHOMStrategy,
                                                                         mutations)
        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 2)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[0])
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 1, mutations[2])
        self.assert_num_changeset_entries(changes_to_apply, 1, 2)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[1])
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 1, mutations[3])


class RandomHOMStrategyTest(BaseHOMStrategyTest):
    def test_generate(self):
        mutations = self.THREE_AOR_MUTATIONS_ON_SUBTRACTION

        def shuffler(mutations):
            mutations.reverse()

        changes_to_apply = self.apply_strategy_to_mutations_with_order_2(controller.RandomHOMStrategy, mutations,
                                                                         hom_kwargs={'shuffler': shuffler})
        self.assert_num_changesets(changes_to_apply, 2)
        self.assert_num_changeset_entries(changes_to_apply, 0, 2)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 0, mutations[2])
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 0, 1, mutations[1])
        self.assert_num_changeset_entries(changes_to_apply, 1, 1)
        self.assert_mutation_in_changeset_at_position_equals(changes_to_apply, 1, 0, mutations[0])


class FirstOrderMutatorTest(unittest.TestCase):
    def test_first_order_mutation(self):
        mutator = controller.FirstOrderMutator(
            operators=[operators.ArithmeticOperatorReplacement, operators.AssignmentOperatorReplacement],
        )
        target_ast = utils.create_ast('x += y + z')

        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            self.assertIn(number, [0, 1])
            self.assertEqual(len(mutations), 1)
            if number == 0:
                self.assertEqual('x += y - z', codegen.to_source(mutant))
            elif number == 1:
                self.assertEqual('x -= y + z', codegen.to_source(mutant))

        self.assertEqual(codegen.to_source(target_ast), 'x += y + z')


class HighOrderMutatorTest(unittest.TestCase):
    def test_second_order_mutation(self):
        mutator = controller.HighOrderMutator(
            operators=[operators.ArithmeticOperatorReplacement, operators.AssignmentOperatorReplacement],
        )
        target_ast = utils.create_ast('x += y + z')

        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            self.assertEqual(number, 0)
            self.assertEqual('x -= y - z', codegen.to_source(mutant))
            self.assertEqual(len(mutations), 2)

        self.assertEqual(codegen.to_source(target_ast), 'x += y + z')

    def test_second_order_mutation_with_same_node_as_target(self):
        mutator = controller.HighOrderMutator(
            operators=[operators.ArithmeticOperatorDeletion, operators.ArithmeticOperatorReplacement],
        )
        target_ast = utils.create_ast('- a')
        number = None
        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            if number == 0:
                self.assertEqual('a', codegen.to_source(mutant))
                self.assertEqual(len(mutations), 1)
            elif number == 1:
                self.assertEqual('+a', codegen.to_source(mutant))
                self.assertEqual(len(mutations), 1)
        self.assertEqual(number, 1)
        self.assertEqual(codegen.to_source(target_ast), '-a')

    def test_second_order_mutation_with_multiple_visitors(self):
        mutator = controller.HighOrderMutator(
            operators=[operators.ConstantReplacement],
        )
        target_ast = utils.create_ast('x = "test"')
        number = None
        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            if number == 0:
                self.assertEqual("x = 'mutpy'", codegen.to_source(mutant))
                self.assertEqual(len(mutations), 1)
            elif number == 1:
                self.assertEqual("x = ''", codegen.to_source(mutant))
                self.assertEqual(len(mutations), 1)
        self.assertEqual(number, 1)
        self.assertEqual(codegen.to_source(target_ast), "x = 'test'")