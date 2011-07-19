import ast
from mutpy.operators import MutationOperator, MutationResign


class SelfWordDeletion(MutationOperator):
    
    def mutate_Attribute(self, node):
        try:
            if node.value.id == 'self':
                return ast.Name(id=node.attr, ctx=ast.Load())
            else:
                raise MutationResign()
        except AttributeError:
            raise MutationResign()


class DecoratorDeletionOperator(MutationOperator):
    
    def mutate_FunctionDef(self, node):
        for decorator in node.decorator_list:
            if decorator.id == self.get_decorator_name():
                node.decorator_list.remove(decorator)
                return node
        else:
            raise MutationResign()
        
    def get_decorator_name(self):
        raise NotImplementedError()


class StaticmethodDecoratorDeletion(DecoratorDeletionOperator):
    
    def get_decorator_name(self):
        return 'staticmethod'

        
class ClassmethodDecoratorDeletion(DecoratorDeletionOperator):
    
    def get_decorator_name(self):
        return 'classmethod'


all_operators = {SelfWordDeletion,
                 StaticmethodDecoratorDeletion,
                 ClassmethodDecoratorDeletion}
    