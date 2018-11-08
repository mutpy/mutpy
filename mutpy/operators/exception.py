import ast

from mutpy.operators.base import MutationOperator, MutationResign


class BaseExceptionHandlerOperator(MutationOperator):

    @staticmethod
    def _replace_exception_body(exception_node, body):
        return ast.ExceptHandler(type=exception_node.type, name=exception_node.name, lineno=exception_node.lineno,
                                 body=body)


class ExceptionHandlerDeletion(BaseExceptionHandlerOperator):
    def mutate_ExceptHandler(self, node):
        if node.body and isinstance(node.body[0], ast.Raise):
            raise MutationResign()
        return self._replace_exception_body(node, [ast.Raise(lineno=node.body[0].lineno)])


class ExceptionSwallowing(BaseExceptionHandlerOperator):
    def mutate_ExceptHandler(self, node):
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            raise MutationResign()
        return self._replace_exception_body(node, [ast.Pass(lineno=node.body[0].lineno)])

    @classmethod
    def name(cls):
        return 'EXS'
