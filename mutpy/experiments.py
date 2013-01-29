import ast
from mutpy import operators


class SelfWordDeletion(operators.MutationOperator):

    def mutate_Attribute(self, node):
        try:
            if node.value.id == 'self':
                return ast.Name(id=node.attr, ctx=ast.Load())
            else:
                raise operators.MutationResign()
        except AttributeError:
            raise operators.MutationResign()


class StaticmethodDecoratorDeletion(operators.DecoratorDeletionMutationOperator):

    def get_decorator_name(self):
        return 'staticmethod'


class StaticmethodDecoratorInsertion(operators.DecoratorInsertionMutationOperator):

    def get_decorator_name(self):
        return 'staticmethod'


all_operators = {
    SelfWordDeletion,
    StaticmethodDecoratorDeletion,
    StaticmethodDecoratorInsertion
}

