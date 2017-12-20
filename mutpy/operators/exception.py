import ast

from mutpy.operators.base import MutationOperator, MutationResign


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
