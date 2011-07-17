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
    