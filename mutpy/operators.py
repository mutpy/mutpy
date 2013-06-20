import ast
import re
import copy
import functools
from mutpy import utils


class MutationResign(Exception): pass


class Mutation:

    def __init__(self, operator, lineno, marker):
        self.operator = operator
        self.lineno = lineno
        self.marker = marker


class MutationOperator:

    def mutate(self, node, to_mutate=None, sampler=None, coverage_injector=None, module=None, only_marked_node=None):
        self.to_mutate = to_mutate
        self.sampler = sampler
        self.lineno = 1
        self.marker = getattr(node, 'marker', None)
        self.only_marked_node = only_marked_node
        self.coverage_injector = coverage_injector
        self.module = module
        for new_node in self.visit(node):
            yield Mutation(operator=self.__class__, lineno=self.lineno, marker=self.marker), new_node

    def visit(self, node):
        if self.has_notmutate(node) or (self.coverage_injector and not self.coverage_injector.is_covered(node)):
            return
        self.set_mutation_lineno(node)
        if self.only_marked_node is not None and self.only_marked_node != getattr(node, 'marker', None):
            for new_node in self.generic_visit(node):
                yield new_node
            return
        visitors = self.find_visitors(node)
        if visitors:
            for visitor in visitors:
                try:
                    if self.sampler and not self.sampler.is_mutation_time():
                        raise MutationResign
                    new_node = visitor(copy.deepcopy(node))
                    ast.fix_missing_locations(new_node)
                    yield new_node
                except MutationResign:
                    pass
                finally:
                    for new_node in self.generic_visit(node):
                        yield new_node
        else:
            for new_node in self.generic_visit(node):
                yield new_node

    def generic_visit(self, node):
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                generator = self.generic_visit_list(old_value)
            elif isinstance(old_value, ast.AST):
                generator = self.generic_visit_real_node(node, field, old_value)
            else:
                generator = []

            for _ in generator:
                yield node

    def generic_visit_list(self, old_value):
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

                    yield
                    old_value[:] = old_values_copy

    def generic_visit_real_node(self, node, field, old_value):
        for new_node in self.visit(old_value):
            if new_node is None:
                delattr(node, field)
            else:
                setattr(node, field, new_node)
            yield
            setattr(node, field, old_value)

    def has_notmutate(self, node):
        try:
            for decorator in node.decorator_list:
                if decorator.id == utils.notmutate.__name__:
                    return True
            return False
        except AttributeError:
            return False

    def set_mutation_lineno(self, node):
        if hasattr(node, 'lineno'):
            self.lineno = node.lineno
        if hasattr(node, 'marker'):
            self.marker = node.marker

    def find_visitors(self, node):
        method_prefix = 'mutate_' + node.__class__.__name__
        return self.getattrs_like(method_prefix)

    def getattrs_like(ob, attr_like):
        pattern = re.compile(attr_like + "($|(_\w+)+$)")
        return [getattr(ob, attr) for attr in dir(ob) if pattern.match(attr)]

    @classmethod
    def name(cls):
        return ''.join([c for c in cls.__name__ if str.isupper(c)])

    @classmethod
    def long_name(cls):
        return cls.__name__


class AbstractArithmeticOperatorReplacement(MutationOperator):

    def mutate_Add(self, node):
        if self.should_mutate(node):
            return ast.Sub()
        raise MutationResign()

    def mutate_Sub(self, node):
        if self.should_mutate(node):
            return ast.Add()
        raise MutationResign()

    def mutate_Mult_to_Div(self, node):
        if self.should_mutate(node):
            return ast.Div()
        raise MutationResign()

    def mutate_Mult_to_FloorDiv(self, node):
        if self.should_mutate(node):
            return ast.FloorDiv()
        raise MutationResign()

    def mutate_Mult_to_Pow(self, node):
        if self.should_mutate(node):
            return ast.Pow()
        raise MutationResign()

    def mutate_Div_to_Mult(self, node):
        if self.should_mutate(node):
            return ast.Mult()
        raise MutationResign()

    def mutate_Div_to_FloorDiv(self, node):
        if self.should_mutate(node):
            return ast.FloorDiv()
        raise MutationResign()

    def mutate_FloorDiv_to_Div(self, node):
        if self.should_mutate(node):
            return ast.Div()
        raise MutationResign()

    def mutate_FloorDiv_to_Mult(self, node):
        if self.should_mutate(node):
            return ast.Mult()
        raise MutationResign()

    def mutate_Mod(self, node):
        if self.should_mutate(node):
            return ast.Mult()
        raise MutationResign()

    def mutate_Pow(self, node):
        if self.should_mutate(node):
            return ast.Mult()
        raise MutationResign()


class ArithmeticOperatorReplacement(AbstractArithmeticOperatorReplacement):

    def should_mutate(self, node):
        return not isinstance(node.parent, ast.AugAssign)

    def mutate_USub(self, node):
        return ast.UAdd()

    def mutate_UAdd(self, node):
        return ast.USub()


class AssignmentOperatorReplacement(AbstractArithmeticOperatorReplacement):

    def should_mutate(self, node):
        return isinstance(node.parent, ast.AugAssign)

    @classmethod
    def name(cls):
        return 'ASR'


class AbstractUnaryOperatorDeletion(MutationOperator):

    def mutate_UnaryOp(self, node):
        if isinstance(node.op, self.get_operator_type()):
            return node.operand
        raise MutationResign()


class ArithmeticOperatorDeletion(AbstractUnaryOperatorDeletion):

    def get_operator_type(self):
        return ast.UAdd, ast.USub


class LogicalOperatorReplacement(MutationOperator):

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


class LogicalOperatorDeletion(AbstractUnaryOperatorDeletion):

    def get_operator_type(self):
        return ast.Invert


class LogicalConnectorReplacement(MutationOperator):

    def mutate_And(self, node):
        return ast.Or()

    def mutate_Or(self, node):
        return ast.And()


class RelationalOperatorReplacement(MutationOperator):

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


class ConstantReplacement(MutationOperator):
    FIRST_CONST_STRING = 'mutpy'
    SEOCND_CONST_STRING = 'python'

    def mutate_Num(self, node):
        return ast.Num(n=node.n + 1)

    def mutate_Str(self, node):
        if utils.is_docstring(node):
            raise MutationResign()

        if node.s != self.FIRST_CONST_STRING:
            return ast.Str(s=self.FIRST_CONST_STRING)
        else:
            return ast.Str(s=self.SEOCND_CONST_STRING)

    def mutate_Str_empty(self, node):
        if not node.s or utils.is_docstring(node):
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
        if utils.is_docstring(node.value):
            raise MutationResign()
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


class ConditionalOperatorDeletion(AbstractUnaryOperatorDeletion):

    def get_operator_type(self):
        return ast.Not


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


class ExceptionHandlerDeletion(MutationOperator):

    def mutate_ExceptHandler(self, node):
        if node.body and isinstance(node.body[0], ast.Raise):
            raise MutationResign()
        return ast.ExceptHandler(type=node.type, name=node.name, body=[ast.Raise()])


class ExceptionSwallowing(MutationOperator):

    def mutate_ExceptHandler(self, node):
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            raise MutationResign()
        return ast.ExceptHandler(type=node.type, name=node.name, body=[ast.Pass()])

    @classmethod
    def name(cls):
        return 'EXS'


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


class MethodDecoratorInsertionMutationOperator(MutationOperator):

    def mutate_FunctionDef(self, node):
        if not isinstance(node.parent, ast.ClassDef):
            raise MutationResign()
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


class ClassmethodDecoratorInsertion(MethodDecoratorInsertionMutationOperator):

    def get_decorator_name(self):
        return 'classmethod'


class AbstractOverriddenElementModification(MutationOperator):

    def is_overridden(self, node, name=None):
        if not isinstance(node.parent, ast.ClassDef):
            raise MutationResign()
        if not name:
            name = node.name
        parent = node.parent
        parent_names = []
        while parent:
            if not isinstance(parent, ast.Module):
                parent_names.append(parent.name)
            if not isinstance(parent, ast.ClassDef) and not isinstance(parent, ast.Module):
                raise MutationResign()
            parent = parent.parent
        getattr_rec = lambda obj, attr: functools.reduce(getattr, attr, obj)
        klass = getattr_rec(self.module, reversed(parent_names))
        for base_klass in klass.mro()[1:-1]:
            if hasattr(base_klass, name):
                return True
        return False


class OverridingMethodDeletion(AbstractOverriddenElementModification):

    def mutate_FunctionDef(self, node):
        if self.is_overridden(node):
            return ast.Pass()
        raise MutationResign()

    @classmethod
    def name(cls):
        return 'IOD'


class HidingVariableDeletion(AbstractOverriddenElementModification):

    def mutate_Assign(self, node):
        if len(node.targets) > 1:
            raise MutationResign()
        if isinstance(node.targets[0], ast.Name) and self.is_overridden(node, name=node.targets[0].id):
            return ast.Pass()
        elif isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            return self.mutate_unpack(node)
        else:
            raise MutationResign()

    def mutate_unpack(self, node):
        target = node.targets[0]
        value = node.value
        new_targets = []
        new_values = []
        for target_element, value_element in zip(target.elts, value.elts):
            if not self.is_overridden(node, target_element.id):
                new_targets.append(target_element)
                new_values.append(value_element)
        if len(new_targets) == len(target.elts):
            raise MutationResign()
        if not new_targets:
            return ast.Pass()
        elif len(new_targets) == 1:
            node.targets = new_targets
            node.value = new_values[0]
            return node
        else:
            target.elts = new_targets
            value.elts = new_values
            return node

    @classmethod
    def name(cls):
        return 'IHD'


class AbstractSuperCallingModification(MutationOperator):

    def is_super_call(self, node, stmt):
        return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and \
            isinstance(stmt.value.func, ast.Attribute) and isinstance(stmt.value.func.value, ast.Call) and \
            isinstance(stmt.value.func.value.func, ast.Name) and stmt.value.func.value.func.id == 'super' and \
            stmt.value.func.attr == node.name

    def should_mutate(self, node):
        return isinstance(node.parent, ast.ClassDef)

    def get_super_call(self, node):
        for index, stmt in enumerate(node.body):
            if self.is_super_call(node, stmt):
                break
        else:
            return None, None
        return index, stmt


class OverriddenMethodCallingPositionChange(AbstractSuperCallingModification):

    def should_mutate(self, node):
        return super().should_mutate(node) and len(node.body) > 1

    def mutate_FunctionDef(self, node):
        if not self.should_mutate(node):
            raise MutationResign()
        index, stmt = self.get_super_call(node)
        if index is None:
            raise MutationResign()
        super_call = node.body[index]
        del node.body[index]
        if index == 0:
            node.body.append(super_call)
        else:
            node.body.insert(0, super_call)
        return node

    @classmethod
    def name(cls):
        return 'IOP'


class SuperCallingDeletion(AbstractSuperCallingModification):

    def mutate_FunctionDef(self, node):
        if not self.should_mutate(node):
            raise MutationResign()
        index, _ = self.get_super_call(node)
        if index is None:
            raise MutationResign()
        node.body[index] = ast.Pass()
        return node


class SuperCallingInsert(AbstractSuperCallingModification, AbstractOverriddenElementModification):

    def should_mutate(self, node):
        return super().should_mutate(node) and self.is_overridden(node)

    def mutate_FunctionDef(self, node):
        if not self.should_mutate(node):
            raise MutationResign()
        index, stmt = self.get_super_call(node)
        if index is not None:
            raise MutationResign()
        node.body.insert(0, self.create_super_call(node))
        return node

    def create_super_call(self, node):
        super_call = utils.create_ast('super().{}()'.format(node.name)).body[0]
        for arg in node.args.args[1:-len(node.args.defaults) or None]:
            super_call.value.args.append(ast.Name(id=arg.arg, ctx=ast.Load()))
        for arg, default in zip(node.args.args[-len(node.args.defaults):], node.args.defaults):
            super_call.value.keywords.append(ast.keyword(arg=arg.arg, value=default))
        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            super_call.value.keywords.append(ast.keyword(arg=arg.arg, value=default))
        if node.args.vararg:
            super_call.value.starargs = ast.Name(id=node.args.vararg, ctx=ast.Load())
        if node.args.kwarg:
            super_call.value.kwargs = ast.Name(id=node.args.kwarg, ctx=ast.Load())
        return super_call


all_operators = {
    ArithmeticOperatorDeletion,
    ArithmeticOperatorReplacement,
    AssignmentOperatorReplacement,
    ClassmethodDecoratorDeletion,
    ClassmethodDecoratorInsertion,
    ConditionalOperatorDeletion,
    ConditionalOperatorInsertion,
    ConstantReplacement,
    ExceptionHandlerDeletion,
    ExceptionSwallowing,
    HidingVariableDeletion,
    LogicalConnectorReplacement,
    LogicalOperatorDeletion,
    LogicalOperatorReplacement,
    MembershipTestReplacement,
    OneIterationLoop,
    OverriddenMethodCallingPositionChange,
    OverridingMethodDeletion,
    RelationalOperatorReplacement,
    ReverseIterationLoop,
    SliceIndexRemove,
    StatementDeletion,
    SuperCallingDeletion,
    SuperCallingInsert,
    ZeroIterationLoop,
}

