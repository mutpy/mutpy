import ast
import copy
from mutpy import utils

COVERAGE_SET_NAME = '__covered_nodes__'

class MarkerNodeTransformer(ast.NodeTransformer):

    def __init__(self):
        super().__init__()
        self.last_marker = 0

    def visit(self, node):
        if not hasattr(node, 'marker') and node.__class__ in CoverageNodeTransformer.get_coverable_nodes():
            node.marker = self.last_marker
            self.last_marker += 1
        return super().visit(node)


class AbstractCoverageNodeTransformer(ast.NodeTransformer):

    @classmethod
    def get_coverable_nodes(cls):
        return cls.get_statements_nodes() | cls.get_definitions_nodes()

    @classmethod
    def get_statements_nodes(cls):
        raise NotImplementedError()

    @classmethod
    def get_definitions_nodes(cls):
        raise NotImplementedError()

    def __init__(self):
        super().__init__()
        for node_class in self.get_coverable_nodes():
            visit_method_name = 'visit_' + node_class.__name__
            if not hasattr(self, visit_method_name):
                if node_class in self.get_definitions_nodes():
                    setattr(self, visit_method_name, self.inject_inside_visit)
                else:
                    setattr(self, visit_method_name, self.inject_before_visit)

    def inject_before_visit(self, node):
        node = self.generic_visit(node)
        if self.is_future_statement(node) or (isinstance(node, ast.Expr) and utils.is_docstring(node.value)):
            return node
        coverage_node = self.generate_coverage_node(node)
        return [coverage_node, node]

    def inject_inside_visit(self, node):
        node = self.generic_visit(node)
        coverage_node = self.generate_coverage_node(node)
        node.body.insert(0, coverage_node)
        return node

    def generate_coverage_node(self, node):
        coverage_node = utils.create_ast('{}.add({})'.format(COVERAGE_SET_NAME, node.marker)).body[0]
        coverage_node.lineno = node.lineno
        coverage_node.col_offset = node.col_offset
        return coverage_node

    def is_future_statement(self, node):
        return isinstance(node, ast.ImportFrom) and node.module == '__future__'


class CoverageNodeTransformerPython32(AbstractCoverageNodeTransformer):

    __python_version__ = (3, 2)

    @classmethod
    def get_statements_nodes(cls):
        return {
            ast.Assert,
            ast.Assign,
            ast.AugAssign,
            ast.Break,
            ast.Continue,
            ast.Delete,
            ast.Expr,
            ast.For,
            ast.Global,
            ast.If,
            ast.Import,
            ast.ImportFrom,
            ast.Nonlocal,
            ast.Pass,
            ast.Raise,
            ast.Return,
            ast.TryExcept,
            ast.TryFinally,
            ast.While
        }

    @classmethod
    def get_definitions_nodes(cls):
        return {
            ast.ClassDef,
            ast.ExceptHandler,
            ast.FunctionDef
        }


class CoverageNodeTransformerPython33(AbstractCoverageNodeTransformer):

    __python_version__ = (3, 3)

    @classmethod
    def get_statements_nodes(cls):
        return {
            ast.Assert,
            ast.Assign,
            ast.AugAssign,
            ast.Break,
            ast.Continue,
            ast.Delete,
            ast.Expr,
            ast.For,
            ast.Global,
            ast.If,
            ast.Import,
            ast.ImportFrom,
            ast.Nonlocal,
            ast.Pass,
            ast.Raise,
            ast.Return,
            ast.Try,
            ast.While
        }

    @classmethod
    def get_definitions_nodes(cls):
        return {
            ast.ClassDef,
            ast.ExceptHandler,
            ast.FunctionDef
        }


CoverageNodeTransformer = utils.get_by_python_version([
    CoverageNodeTransformerPython32,
    CoverageNodeTransformerPython33
])


class CoverageInjector:

    def __init__(self):
        self.covered_nodes = set()

    def inject(self, node, module_name='coverage'):
        self.covered_nodes.clear()
        self.marker_transformer = MarkerNodeTransformer()
        marker_node = self.marker_transformer.visit(node)
        coverage_node = CoverageNodeTransformer().visit(copy.deepcopy(marker_node))
        with utils.StdoutManager():
            return utils.create_module(
                ast_node=coverage_node,
                module_name=module_name,
                module_dict={COVERAGE_SET_NAME: self.covered_nodes}
            )

    def is_covered(self, child_node):
        if not child_node.__class__ in CoverageNodeTransformer.get_coverable_nodes():
            return True
        return child_node.marker in self.covered_nodes

    def get_result(self):
        return (len(self.covered_nodes), self.marker_transformer.last_marker)

