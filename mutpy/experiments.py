import ast
from mutpy.operators import MutationOperator, MutationResign,\
    DecoratorDeletionMutationOperator, DecoratorInsertionMutationOperator


class SelfWordDeletion(MutationOperator):
    
    def mutate_Attribute(self, node):
        try:
            if node.value.id == 'self':
                return ast.Name(id=node.attr, ctx=ast.Load())
            else:
                raise MutationResign()
        except AttributeError:
            raise MutationResign()


class StaticmethodDecoratorDeletion(DecoratorDeletionMutationOperator):
    
    def get_decorator_name(self):
        return 'staticmethod'


class StaticmethodDecoratorInsertion(DecoratorInsertionMutationOperator):

    def get_decorator_name(self):
        return 'staticmethod'


all_operators = [SelfWordDeletion,
                 StaticmethodDecoratorDeletion,
                 StaticmethodDecoratorInsertion]
    