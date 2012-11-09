import unittest
import ast
from mutpy import operators, codegen

EOL = '\n'
INDENT = ' ' * 4
PASS = 'pass'

class MutationOperatorTest(unittest.TestCase):

    class PassIdOperator(operators.MutationOperator):

        def mutate_Pass(self, node):
            return node

    def setUp(self):
        self.operator = self.PassIdOperator()
        self.target_ast = ast.parse(PASS)

    def test_generate_all_mutations_if_always_sampler(self):

        class AlwaysSampler:
            
            def is_mutation_time(self):
                return True

        mutations = list(self.operator.mutate(self.target_ast, sampler=AlwaysSampler()))

        self.assertEqual(len(mutations), 1)


    def test_no_mutations_if_never_sampler(self):
        
        class NeverSampler:
            
            def is_mutation_time(self):
                return False
        
        mutations = list(self.operator.mutate(self.target_ast, sampler=NeverSampler()))

        self.assertEqual(len(mutations), 0)


class OperatorTestCase(unittest.TestCase):

    def assert_mutation(self, original, mutants, lines=None):
        original_ast = ast.parse(original)
        mutants = list(map(codegen.remove_extra_lines, mutants))
        original = codegen.remove_extra_lines(original)
        for mutant, lineno in self.__class__.op.mutate(original_ast, None):
            mutant_code = codegen.remove_extra_lines(codegen.to_source(mutant))
            self.assertIn(mutant_code, mutants)
            mutants.remove(mutant_code)
            self.assert_location(mutant)
            if not lines is None:
                self.assert_mutation_lineo(lineno, lines)

        self.assertListEqual(mutants, [], 'did not generate all mutants')
    
    def assert_location(self, mutant):    
        for node in ast.walk(mutant):
            if 'lineno' in node._attributes and not hasattr(node, 'lineno'):
                self.fail('Missing lineno in ' + str(node))
            if 'col_offset' in node._attributes and not hasattr(node, 'col_offset'):
                self.fail('Missing col_offset in ' + str(node))

    def assert_mutation_lineo(self, lineno, lines):
        mutation_line = lines.pop(0)
        self.assertEqual(mutation_line, lineno, 'Bad mutation lineno!')


class ConstantReplacementTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ConstantReplacement()

    def test_numbers_increment(self):
        self.assert_mutation('2 + 3 - 99', ['3 + 3 - 99', '2 + 4 - 99', '2 + 3 - 100'])

    def test_string_replacement(self):
        self.assert_mutation("x = 'ham' + 'egs'",
                            ["x = '{}' + 'egs'".format(self.op.FIRST_CONST_STRING),
                             "x = 'ham' + '{}'".format(self.op.FIRST_CONST_STRING),
                             "x = '' + 'egs'",
                             "x = 'ham' + ''"])

    def test_resign_if_empty(self):
        self.assert_mutation("'ham' + ''",
                            ["'{}' + ''".format(self.op.FIRST_CONST_STRING),
                             "'' + ''", "'ham' + '{}'".format(self.op.FIRST_CONST_STRING)])

    def test_resign_first(self):
        self.assert_mutation("'' + 'ham'",
                            ["'' + '{}'".format(self.op.FIRST_CONST_STRING),
                             "'' + ''",
                             "'{}' + 'ham'".format(self.op.FIRST_CONST_STRING)])

    def test_not_mutate_function(self):
        self.assert_mutation("@notmutate" + EOL + "def x():" + EOL + INDENT + "'ham'", [])

    def test_not_mutate_class(self):
        self.assert_mutation("@notmutate" + EOL + "class X:" + EOL + INDENT + "'ham'", [])

    def test_replace_first_const_string(self):
        self.assert_mutation("'{}'".format(self.op.FIRST_CONST_STRING),
                            ["'{}'".format(self.op.SEOCND_CONST_STRING), "''"])


class ArithmeticOperatorReplacementTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ArithmeticOperatorReplacement()

    def test_add_to_sub_replacement(self):
        self.assert_mutation('x + y + z', ['x - y + z', 'x + y - z'])

    def test_sub_to_add_replacement(self):
        self.assert_mutation('x - y', ['x + y'])

    def test_mult_to_div_and_pow_replacement(self):
        self.assert_mutation('x * y', ['x / y', 'x // y', 'x ** y'])

    def test_div_replacement(self):
        self.assert_mutation('x / y', ['x * y', 'x // y'])

    def test_floor_div_to_div(self):
        self.assert_mutation('x // y', ['x / y', 'x * y'])

    def test_mod_to_mult(self):
        self.assert_mutation('x % y', ['x * y'])

    def test_pow_to_mult(self):
        self.assert_mutation('x ** y', ['x * y'])

    def test_mutation_lineno(self):
        self.assert_mutation('pass' + EOL + 'x + y' + EOL + 'x - y', 
                            ['pass' + EOL + 'x - y' + EOL + 'x - y', 'pass' + EOL + 'x + y' + EOL + 'x + y'], 
                            [2, 3])
        

class BitwiseOperatorReplacement(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.BitwiseOperatorReplacement()

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
        cls.op = operators.LogicalOperatorReplacement()

    def test_and_to_or(self):
        self.assert_mutation('(x and y)', ['(x or y)'])

    def test_or_to_and(self):
        self.assert_mutation('(x or y)', ['(x and y)'])


class ConditionalOperatorReplacementTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ConditionalOperatorReplacement()

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
        cls.op = operators.UnaryOperatorReplacement()

    def test_usub(self):
        self.assert_mutation('(-x)', ['(+x)'])

    def test_uadd(self):
        self.assert_mutation('(+x)', ['(-x)'])


class SliceIndexRemoveTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.SliceIndexRemove()

    def test_slice_indexes_remove(self):
        self.assert_mutation('x[1:2:3]', ['x[:2:3]', 'x[1::3]', 'x[1:2]'])

class ConditionalOperatorInsertionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ConditionalOperatorInsertion()

    def test_negate_while_condition(self):
        self.assert_mutation("while x:\n    pass", ["while (not x):\n    pass"])

    def test_negate_if_condition(self):
        self.assert_mutation('if x:\n    pass', ['if (not x):\n    pass'])

    def test_negate_if_and_elif_condition(self):
        self.assert_mutation('if x:' + EOL + INDENT + 'pass' + EOL + 'elif y:' + EOL + INDENT + 'pass',
                            ['if (not x):' + EOL + INDENT + 'pass' + EOL + 'elif y:' + EOL + INDENT + 'pass',
                            'if x:' + EOL + INDENT + 'pass' + EOL + 'elif (not y):' + EOL + INDENT + 'pass'],
                            lines=[1, 3])


class MembershipTestReplacementTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.MembershipTestReplacement()

    def test_in_to_not_in(self):
        self.assert_mutation('x in y', ['x not in y'])

    def test_not_in_to_in(self):
        self.assert_mutation('x not in y', ['x in y'])


class ExceptionHandleDeletionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ExceptionHandleDeletion()

    def test_delete_except(self):
        self.assert_mutation('try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL + INDENT + PASS,
                            ['try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL + INDENT + 'raise',])

    def test_delete_two_except(self):
        self.assert_mutation('try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL
                            + INDENT + PASS + EOL + 'except Y:' + EOL + INDENT + PASS,
                            ['try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL
                            + INDENT + 'raise' + EOL + 'except Y:' + EOL + INDENT + PASS,
                             'try:' + EOL + INDENT + PASS + EOL + 'except Z:' + EOL
                            + INDENT + PASS + EOL + 'except Y:' + EOL + INDENT + 'raise'])


class ZeroIterationLoopTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ZeroIterationLoop()

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
        cls.op = operators.OneIterationLoop()

    def test_for_one_iteration(self):
        self.assert_mutation('for x in y:' + EOL + INDENT + PASS,
                            ['for x in y:' + EOL + INDENT + PASS + EOL + INDENT + 'break'])

    def test_while_one_iteration(self):
        self.assert_mutation('while x:' + EOL + INDENT + PASS,
                            ['while x:' + EOL + INDENT + PASS + EOL + INDENT + 'break'])


class ReverseIterationLoopTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ReverseIterationLoop()

    def test_for_reverse(self):
        self.assert_mutation('for x in y:' + EOL + INDENT + PASS,
                            ['for x in reversed(y):' + EOL + INDENT + PASS])


class StatementDeletionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.StatementDeletion()

    def test_return_deletion(self):
        self.assert_mutation('def f():' + EOL + INDENT + 'return 1', ['def f():' + EOL + INDENT + PASS])

    def test_assign_deletion(self):
        self.assert_mutation('x = 1', [PASS])

    def test_fuction_call_deletion(self):
        self.assert_mutation('f()', ['pass'])

    def test_assign_with_call_deletion(self):
        self.assert_mutation('x = f()', ['pass'])


class ClassmethodDecoratorDeletionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ClassmethodDecoratorDeletion()

    def test_single_classmethod_deletion(self):
        self.assert_mutation('@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' ,
                         ['def f():' + EOL + INDENT + 'pass'])

    def test_classmethod_deletion_with_other(self):
        self.assert_mutation('@staticmethod' + EOL + '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' ,
                         ['@staticmethod' + EOL + 'def f():' + EOL + INDENT + 'pass'])

    def test_classmethod_deletion_with_other_and_arguments(self):
        self.assert_mutation('@wraps(func)' + EOL + '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' ,
                         ['@wraps(func)' + EOL + 'def f():' + EOL + INDENT + 'pass'])

    def test_classmethod_deletion_with_other_from_module(self):
        self.assert_mutation('@itertools.wraps' + EOL + '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' ,
                         ['@itertools.wraps' + EOL + 'def f():' + EOL + INDENT + 'pass'])

    def test_double_classmethod_deletion(self):
        self.assert_mutation('@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' + EOL + 
                                '@classmethod' + EOL + 'def g():' + EOL + INDENT + 'pass', 
                         ['def f():' + EOL + INDENT + 'pass' + EOL + 
                            '@classmethod' + EOL + 'def g():' + EOL + INDENT + 'pass', 
                         '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' + EOL +
                             'def g():' + EOL + INDENT + 'pass'])

class ClassmethodDecoratorInsertionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = operators.ClassmethodDecoratorInsertion()

    def test_add_classmethod_decorator(self):
        self.assert_mutation('def f():' + EOL + INDENT + 'pass',
                             ['@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass'])

    def test_not_add_if_already_has_staticmethod(self):
        self.assert_mutation('@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass', [])

    def test_classmethod_add_with_other_and_arguments(self):
        self.assert_mutation('@wraps(func)' + EOL + 'def f():' + EOL + INDENT + 'pass',
                            ['@wraps(func)' + EOL + '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' ])

    def test_add_classmethod_in_two_function(self):
        self.assert_mutation('def f():' + EOL + INDENT + 'pass' + EOL + 'def g():' + EOL + INDENT + 'pass', 
                             ['@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' + EOL + 
                                'def g():' + EOL + INDENT + 'pass',
                              'def f():' + EOL + INDENT + 'pass' + EOL + '@classmethod' + EOL + 
                                'def g():' + EOL + INDENT + 'pass'])

    def test_classmethod_add_with_other_from_module(self):
        self.assert_mutation('@itertools.wraps' + EOL + 'def f():' + EOL + INDENT + 'pass' ,
                         ['@itertools.wraps' + EOL + '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass'])

