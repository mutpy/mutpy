import ast
import re
from mutpy import utils


class MutationResign(Exception): pass


class MutationOperator:

    def mutate(self, node, to_mutate):
        self.to_mutate = to_mutate
        for new_node in self.visit(node):
            yield new_node, 1

    def visit(self, node):
        try:
            for decorator in node.decorator_list:
                if decorator.id == utils.notmutate.__name__:
                    return 
        except AttributeError:
            pass

        visitors = self.find_visitors(node) 
        
        if visitors:
            for visitor in visitors: 
                try:
                    new_node = visitor(node)
                    yield new_node
                except MutationResign:
                    for new_node in self.generic_visit(node):
                        yield new_node
        else:
            for new_node in self.generic_visit(node):
                yield new_node

    def generic_visit(self, node):
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                old_values_copy = old_value[:]
                for position, value in enumerate(old_values_copy):
                    if isinstance(value, ast.AST):
                        for new_value in self.visit(value):
                            if not isinstance(new_value, ast.AST):
                                old_value[position:position+1] = new_value
                            elif value is None:
                                del old_value[position]
                            else:
                                old_value[position] = new_value

                            yield node 
                            old_value[:] = old_values_copy

            elif isinstance(old_value, ast.AST):
                for new_node in self.visit(old_value):
                    if new_node is None:
                        delattr(node, field)
                    else:
                        setattr(node, field, new_node)
                    yield node
                    setattr(node, field, old_value)

    def find_visitors(self, node):
        method_prefix = 'mutate_' + node.__class__.__name__
        visitors = self.getattrs_like(method_prefix)
        return visitors

    def getattrs_like(ob, attr_like):
        pattern = re.compile(attr_like + "_\w+")
        return [getattr(ob, attr) for attr in dir(ob) if attr == attr_like or pattern.match(attr)]

    @classmethod
    def name(cls):
        return ''.join([c for c in cls.__name__ if str.isupper(c)])

    @classmethod
    def long_name(cls):
        return cls.__name__


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
            raise MutationResign()

        return ast.Slice(lower=None, upper=node.upper, step=node.step)

    def mutate_Slice_remove_upper(self, node):
        if not node.upper:
            raise MutationResign()

        return ast.Slice(lower=node.lower, upper=None, step=node.step)

    def mutate_Slice_remove_step(self, node):
        if not node.step:
            raise MutationResign()

        return ast.Slice(lower=node.lower, upper=node.upper, step=None)


class MembershipTestReplacement(MutationOperator):

    def mutate_In(self, node):
        return ast.NotIn()

    def mutate_NotIn(self, node):
        return ast.In()


class ExceptionHandleDeletion(MutationOperator):

    def mutate_ExceptHandler(self, node):
        return ast.ExceptHandler(type=node.type, name=node.name, body=[ast.Raise()])


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

