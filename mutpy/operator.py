import ast

class ArithmeticOperatorReplacement(ast.NodeTransformer):
    def visit_Add(self, node):
        print('+ -> -')
        return ast.Sub()