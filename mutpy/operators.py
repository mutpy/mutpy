import ast
import copy
import re
from mutpy import utils


class MutationResign(Exception): pass


class MutationOperator(ast.NodeTransformer):

    def mutate(self, node, to_mutate):
        self.initialize_mutation()
        while True:
            self.visited_node_number = 0
            node_copy = self.get_node_copy(node)
            new_node = self.visit(node_copy)

            if not self.mutate_method_number:
                self.muteted_node_number += 1

            if not self.mutation_flag:
                break

            self.mutation_flag = False
            self.repair_node(new_node)
            yield new_node, self.mutate_lineno

    def initialize_mutation(self):
        self.muteted_node_number = 0
        self.mutate_method_number = 0
        self.mutation_flag = False

    @utils.TimeRegister
    def get_node_copy(self, node):
        return copy.deepcopy(node)

    @utils.TimeRegister
    def repair_node(self, node):
        ast.fix_missing_locations(node)

    @utils.TimeRegister
    def visit(self, node):
        if hasattr(node, 'lineno'):
            self.curr_line = node.lineno

        if self.mutation_flag:
            return node

        try:
            for decorator in node.decorator_list:
                if decorator.id == utils.notmutate.__name__:
                    return node
        except AttributeError:
            pass

        visitors = self.find_visitors(node)

        if not visitors:
            new_node = self.generic_visit(node)
        else:
            if self.visited_node_number < self.muteted_node_number:
                self.visited_node_number += 1
                new_node = self.generic_visit(node)
            else:
                new_node = self.mutate_with_visitors(node, visitors)

        return new_node

    def mutate_with_visitors(self, node, visitors):
        while self.mutate_method_number < len(visitors):
            visitor = visitors[self.mutate_method_number]
            try:
                new_node = visitor(node)
                self.mutate_lineno = node.lineno if hasattr(node, 'lineno') else self.curr_line
                self.mutation_flag = True
                if new_node:
                    ast.copy_location(new_node, node)
                if visitor is visitors[-1]:
                    self.mutate_method_number = 0
                    self.visited_node_number += 1
                else:
                    self.mutate_method_number += 1

                break
            except MutationResign:
                self.mutate_method_number += 1
                self.muteted_node_number += 1
        else:
            self.mutate_method_number = 0
            self.visited_node_number += 1
            new_node = self.generic_visit(node)

        return new_node

    @staticmethod
    def getattr_like(ob, attr_like):
        pattern = re.compile(attr_like + "_\w+")
        return [getattr(ob, attr) for attr in dir(ob) if attr == attr_like or pattern.match(attr)]

    @classmethod
    def name(cls):
        return ''.join([c for c in cls.__name__ if str.isupper(c)])

    @classmethod
    def long_name(cls):
        return cls.__name__

    def find_visitors(self, node):
        method_prefix = 'mutate_' + node.__class__.__name__
        visitors = MutationOperator.getattr_like(self, method_prefix)
        return visitors


class ArithmeticOperatorReplacement(MutationOperator):

    def mutate_Add(self, node):
        return ast.Sub()

    def mutate_Sub(self, node):
        return ast.Add()

    def mutate_Mult_to_Div(self, node):
        return ast.Div()

    def mutate_Mult_to_FloorDiv(self, node):
        return ast.FloorDiv()

    def mutate_Mult_to_Pow(self, node):
        return ast.Pow()

    def mutate_Div_to_Mult(self, node):
        return ast.Mult()

    def mutate_Div_to_FloorDiv(self, node):
        return ast.FloorDiv()

    def mutate_FloorDiv_to_Div(self, node):
        return ast.Div()

    def mutate_FloorDiv_to_Mult(self, node):
        return ast.Mult()

    def mutate_Mod(self, node):
        return ast.Mult()

    def mutate_Pow(self, node):
        return ast.Mult()


class BitwiseOperatorReplacement(MutationOperator):

    def mutate_BitAnd(self, node):
        return ast.BitOr()

    def mutate_BitOr(self, node):
        return ast.BitAnd()

    def mutate_BitXor(self, node):
        return ast.BitAnd()

    def mutate_LShift(self, node):
        return ast.RShift()

    def mutate_RShift(self, node):
        return ast.LShift()


class LogicalOperatorReplacement(MutationOperator):

    def mutate_And(self, node):
        return ast.Or()

    def mutate_Or(self, node):
        return ast.And()


class ConditionalOperatorReplacement(MutationOperator):

    def mutate_Lt(self, node):
        return ast.Gt()

    def mutate_Lt_to_LtE(self, node):
        return ast.LtE()

    def mutate_Gt(self, node):
        return ast.Lt()

    def mutate_Gt_to_GtE(self, node):
        return ast.GtE()

    def mutate_LtE(self, node):
        return ast.GtE()

    def mutate_LtE_to_Lt(self, node):
        return ast.Lt()

    def mutate_GtE(self, node):
        return ast.LtE()

    def mutate_GtE_to_Gt(self, node):
        return ast.Gt()

    def mutate_Eq(self, node):
        return ast.NotEq()

    def mutate_NotEq(self, node):
        return ast.Eq()


class UnaryOperatorReplacement(MutationOperator):

    def mutate_USub(self, node):
        return ast.UAdd()

    def mutate_UAdd(self, node):
        return ast.USub()


class ConstantReplacement(MutationOperator):
    FIRST_CONST_STRING = 'mutpy'
    SEOCND_CONST_STRING = 'python'

    def mutate_Num(self, node):
        return ast.Num(n=node.n + 1)

    def mutate_Str(self, node):
        if node.s != self.FIRST_CONST_STRING:
            return ast.Str(s=self.FIRST_CONST_STRING)
        else:
            return ast.Str(s=self.SEOCND_CONST_STRING)

    def mutate_Str_empty(self, node):
        if not node.s:
            raise MutationResign()

        return ast.Str(s='')

    @classmethod
    def name(cls):
        return 'CRP'


class StatementDeletion(MutationOperator):

    def mutate_Assign(self, node):
        return ast.Pass()

    def mutate_Return(self, node):
        return ast.Pass()

    def mutate_Expr(self, node):
        return ast.Pass()

    @classmethod
    def name(cls):
        return 'SDL'


class ConditionalOperatorInsertion(MutationOperator):

    def negate_test(self, node):
        not_node = ast.UnaryOp(op=ast.Not(), operand=node.test)
        node.test = not_node
        return node

    def mutate_While(self, node):
        return self.negate_test(node)

    def mutate_If(self, node):
        return self.negate_test(node)


class SliceIndexRemove(MutationOperator):

    def mutate_Slice_remove_lower(self, node):
        if not node.lower:
            raise MutationResign

        node.lower = None
        return node

    def mutate_Slice_remove_upper(self, node):
        if not node.upper:
            raise MutationResign

        node.upper = None
        return node

    def mutate_Slice_remove_step(self, node):
        if not node.step:
            raise MutationResign

        node.step = None
        return node


class MembershipTestReplacement(MutationOperator):

    def mutate_In(self, node):
        return ast.NotIn()

    def mutate_NotIn(self, node):
        return ast.In()


class ExceptionHandleDeletion(MutationOperator):

    def mutate_ExceptHandler(self, node):
        node.body = [ast.Raise()]
        return node


class ZeroIterationLoop(MutationOperator):

    def zero_iteration(self, node):
        node.body = [ast.Break()]
        return node

    def mutate_For(self, node):
        return self.zero_iteration(node)

    def mutate_While(self, node):
        return self.zero_iteration(node)


class OneIterationLoop(MutationOperator):

    def one_iteration(self, node):
        node.body.append(ast.Break())
        return node

    def mutate_For(self, node):
        return self.one_iteration(node)

    def mutate_While(self, node):
        return self.one_iteration(node)


class ReverseIterationLoop(MutationOperator):

    def mutate_For(self, node):
        old_iter = node.iter
        node.iter = ast.Call(func=ast.Name(id=reversed.__name__, ctx=ast.Load()),
                             args=[old_iter], keywords=[], starargs=None, kwargs=None)
        return node

class DecoratorDeletionMutationOperator(MutationOperator):

    def mutate_FunctionDef(self, node):
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                decorator_name = decorator.func.id
            elif isinstance(decorator, ast.Attribute):
                decorator_name = decorator.value.id
            else:
                decorator_name = decorator.id
            if decorator_name == self.get_decorator_name():
                node.decorator_list.remove(decorator)
                return node
        else:
            raise MutationResign()

    def get_decorator_name(self):
        raise NotImplementedError()


class ClassmethodDecoratorDeletion(DecoratorDeletionMutationOperator):

    def get_decorator_name(self):
        return 'classmethod'


class DecoratorInsertionMutationOperator(MutationOperator):

    def mutate_FunctionDef(self, node):
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                decorator_name = decorator.func.id
            elif isinstance(decorator, ast.Attribute):
                decorator_name = decorator.value.id
            else:
                decorator_name = decorator.id
            if decorator_name == self.get_decorator_name():
                raise MutationResign()

        decorator = ast.Name(id=self.get_decorator_name(), ctx=ast.Load())
        node.decorator_list.append(decorator)
        return node

    def get_decorator_name(self):
        raise NotImplementedError()


class ClassmethodDecoratorInsertion(DecoratorInsertionMutationOperator):

    def get_decorator_name(self):
        return 'classmethod'


all_operators = [ArithmeticOperatorReplacement,
                 UnaryOperatorReplacement,
                 BitwiseOperatorReplacement,
                 LogicalOperatorReplacement,
                 ConditionalOperatorReplacement,
                 ConditionalOperatorInsertion,
                 ConstantReplacement,
                 StatementDeletion,
                 SliceIndexRemove,
                 ExceptionHandleDeletion,
                 MembershipTestReplacement,
                 OneIterationLoop,
                 ZeroIterationLoop,
                 ReverseIterationLoop,
                 ClassmethodDecoratorDeletion,
                 ClassmethodDecoratorInsertion]

