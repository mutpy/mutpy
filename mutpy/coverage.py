import ast
import copy
from mutpy import utils

COVERAGE_SET_NAME = '__covered_nodes__'

class MarkerNodeTransformer(ast.NodeTransformer):

    def __init__(self):
        super().__init__()
        self.last_marker = 0

    def visit(self, node):
        if not hasattr(node, 'marker') and node.__class__ in CoverageNodeTransformer.coverable_nodes:
            node.marker = self.last_marker
            self.last_marker += 1
        return super().visit(node)


class CoverageNodeTransformer(ast.NodeTransformer):

    inject_inside = [
        ast.ExceptHandler,
        ast.FunctionDef,
        ast.ClassDef
    ]

    inject_before = [
        ast.Assign,
        ast.If,
        ast.While,
        ast.For,
        ast.Expr,
        ast.Return,
        ast.TryExcept,
        ast.TryFinally,
        ast.Delete,
        ast.AugAssign,
        ast.Raise,
        ast.Assert,
        ast.Import,
        ast.ImportFrom,
        ast.Global,
        ast.Nonlocal,
        ast.Break,
        ast.Continue,
        ast.Pass
    ]

    coverable_nodes = inject_before + inject_inside

    def __init__(self):
        super().__init__()
        for node_class in self.coverable_nodes:
            visit_method_name = 'visit_' + node_class.__name__
            if not hasattr(self, visit_method_name):
                if node_class in self.inject_before:
                    setattr(self, visit_method_name, self.inject_before_visit)
                else:
                    setattr(self, visit_method_name, self.inject_inside_visit)

    def inject_before_visit(self, node):
        node = self.generic_visit(node)
        coverage_node = self.generate_coverage_node(node)
        return [coverage_node, node]

    def inject_inside_visit(self, node):
        node = self.generic_visit(node)
        coverage_node = self.generate_coverage_node(node)
        node.body.insert(0, coverage_node)
        return node

    def generate_coverage_node(self, node):
        coverage_node = ast.parse('{}.add({})'.format(COVERAGE_SET_NAME, node.marker)).body[0]
        coverage_node.lineno = node.lineno
        coverage_node.col_offset = node.col_offset
        return coverage_node


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
        if not child_node.__class__ in CoverageNodeTransformer.coverable_nodes:
            return True
        return child_node.marker in self.covered_nodes

    def get_result(self):
        return (len(self.covered_nodes), self.marker_transformer.last_marker)

