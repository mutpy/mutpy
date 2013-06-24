import ast
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


class FirstToLastHOMStrategyTest(unittest.TestCase):

    def test_generate(self):
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
        ]
        hom_strategy = controller.FirstToLastHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 2)
        self.assertEqual(changes_to_apply[0][0], mutations[0])
        self.assertEqual(changes_to_apply[0][1], mutations[2])
        self.assertEqual(len(changes_to_apply[1]), 1)
        self.assertEqual(changes_to_apply[1][0], mutations[1])

    def test_generate_if_same_node(self):
        node = ast.Sub()
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=node),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=node),
        ]
        hom_strategy = controller.FirstToLastHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 1)
        self.assertEqual(changes_to_apply[0][0], mutations[0])
        self.assertEqual(len(changes_to_apply[1]), 1)
        self.assertEqual(changes_to_apply[1][0], mutations[1])

    def test_generate_if_node_child(self):
        node = ast.Sub(children=[])
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.UnaryOp(children=[node])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=node),
        ]
        hom_strategy = controller.FirstToLastHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 1)
        self.assertEqual(changes_to_apply[0][0], mutations[0])
        self.assertEqual(len(changes_to_apply[1]), 1)
        self.assertEqual(changes_to_apply[1][0], mutations[1])


class EachChoiceHOMStrategyTest(unittest.TestCase):

    def test_generate(self):
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
        ]
        hom_strategy = controller.EachChoiceHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 2)
        self.assertEqual(changes_to_apply[0][0], mutations[0])
        self.assertEqual(changes_to_apply[0][1], mutations[1])
        self.assertEqual(len(changes_to_apply[1]), 1)
        self.assertEqual(changes_to_apply[1][0], mutations[2])


class BetweenOperatorsHOMStrategyTest(unittest.TestCase):

    def test_generate_if_one_operator(self):
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
        ]
        hom_strategy = controller.BetweenOperatorsHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 1)
        self.assertEqual(changes_to_apply[0][0], mutations[0])
        self.assertEqual(len(changes_to_apply[1]), 1)
        self.assertEqual(changes_to_apply[1][0], mutations[1])

    def test_generate_if_two_operators(self):
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.AssignmentOperatorReplacement, node=ast.Sub(children=[])),
        ]
        hom_strategy = controller.BetweenOperatorsHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 2)
        self.assertEqual(changes_to_apply[0][0], mutations[0])
        self.assertEqual(changes_to_apply[0][1], mutations[2])
        self.assertEqual(len(changes_to_apply[1]), 2)
        self.assertEqual(changes_to_apply[1][0], mutations[1])
        self.assertEqual(changes_to_apply[1][1], mutations[2])

    def test_generate_if_three_operators(self):
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.AssignmentOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ConstantReplacement, node=ast.Sub(children=[])),
        ]
        hom_strategy = controller.BetweenOperatorsHOMStrategy(order=2)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 2)
        self.assertEqual(changes_to_apply[0][0], mutations[0])
        self.assertEqual(changes_to_apply[0][1], mutations[2])
        self.assertEqual(len(changes_to_apply[1]), 2)
        self.assertEqual(changes_to_apply[1][0], mutations[1])
        self.assertEqual(changes_to_apply[1][1], mutations[3])


class RandomHOMStrategyTest(unittest.TestCase):

    def test_generate(self):
        mutations = [
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
            operators.Mutation(operator=operators.ArithmeticOperatorReplacement, node=ast.Sub(children=[])),
        ]

        def shuffler(mutations):
            mutations.reverse()

        hom_strategy = controller.RandomHOMStrategy(order=2, shuffler=shuffler)

        changes_to_apply = list(hom_strategy.generate(mutations))

        self.assertEqual(len(changes_to_apply), 2)
        self.assertEqual(len(changes_to_apply[0]), 2)
        self.assertEqual(changes_to_apply[0][0], mutations[2])
        self.assertEqual(changes_to_apply[0][1], mutations[1])
        self.assertEqual(len(changes_to_apply[1]), 1)
        self.assertEqual(changes_to_apply[1][0], mutations[0])


class FirstOrderMutatorTest(unittest.TestCase):

    def test_first_order_mutation(self):
        mutator = controller.FirstOrderMutator(
            operators=[operators.ArithmeticOperatorReplacement, operators.AssignmentOperatorReplacement],
        )
        target_ast = utils.create_ast('x += y + z')

        for number, (mutations, mutant) in enumerate(mutator.mutate(target_ast)):
            if number == 0:
                self.assertEqual('x += y - z', codegen.to_source(mutant))
                self.assertEqual(len(mutations), 1)
            elif number == 1:
                self.assertEqual('x -= y + z', codegen.to_source(mutant))
                self.assertEqual(len(mutations), 1)
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
                self.assertEqual(len(mutations), 2)
            else:
                self.fail()

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
                self.assertEqual('(+a)', codegen.to_source(mutant))
                self.assertEqual(len(mutations), 1)
        self.assertEqual(number, 1)
        self.assertEqual(codegen.to_source(target_ast), '(-a)')

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
