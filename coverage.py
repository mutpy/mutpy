import ast
import copy
import unittest
from mutpy import utils

COVERAGE_SET_NAME = '__covered_nodes__'


class MarkerNodeTransformer(ast.NodeTransformer):

    def __init__(self):
        super().__init__()
        self.last_marker = 0

    def visit(self, node):
        node.marker = self.last_marker
        self.last_marker += 1
        return super().visit(node)


class AbstractCoverageNodeTransformer(ast.NodeTransformer):

    @classmethod
    def get_coverable_nodes(cls):
        raise NotImplementedError()

    def __init__(self):
        super().__init__()
        for node_class in self.get_coverable_nodes():
            visit_method_name = 'visit_' + node_class.__name__
            if not hasattr(self, visit_method_name):
                if node_class == ast.ExceptHandler:
                    setattr(self, visit_method_name, self.inject_inside_visit)
                else:
                    setattr(self, visit_method_name, self.inject_before_visit)

    def inject_before_visit(self, node):
        node = self.generic_visit(node)
        if self.is_future_statement(node):
            return node
        coverage_node = self.generate_coverage_node(node)
        return [coverage_node, node]

    def inject_inside_visit(self, node):
        node = self.generic_visit(node)
        coverage_node = self.generate_coverage_node(node)
        node.body.insert(0, coverage_node)
        return node

    def generate_coverage_node(self, node):
        if hasattr(node, 'body'):
            markers = self.get_markers_from_body_node(node)
        else:
            markers = self.get_included_markers(node)
        coverage_node = utils.create_ast('{}.update({})'.format(COVERAGE_SET_NAME, repr(markers))).body[0]
        coverage_node.lineno = node.lineno
        coverage_node.col_offset = node.col_offset
        return coverage_node

    def is_future_statement(self, node):
        return isinstance(node, ast.ImportFrom) and node.module == '__future__'

    def get_included_markers(self, node, without=None):
        markers = {n.marker for n in ast.walk(node) if hasattr(n, 'marker')}
        if without:
            for n in without:
                markers.difference_update(self.get_included_markers(n))
        return markers

    def get_markers_from_body_node(self, node):
        if isinstance(node, (ast.If, ast.While)):
            return {node.marker} | self.get_included_markers(node.test)
        elif isinstance(node, ast.For):
            return {node.marker} | self.get_included_markers(node.target) | self.get_included_markers(node.iter)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            return self.get_included_markers(node, without=node.body)
        else:
            return {node.marker}


class CoverageNodeTransformerPython32(AbstractCoverageNodeTransformer):

    __python_version__ = (3, 2)

    @classmethod
    def get_coverable_nodes(cls):
        return {
            ast.Assert,
            ast.Assign,
            ast.AugAssign,
            ast.Break,
            ast.Continue,
            ast.Delete,
            ast.Expr,
            ast.Global,
            ast.Import,
            ast.ImportFrom,
            ast.Nonlocal,
            ast.Pass,
            ast.Raise,
            ast.Return,
            ast.FunctionDef,
            ast.ClassDef,
            ast.TryExcept,
            ast.TryFinally,
            ast.ExceptHandler,
            ast.If,
            ast.For,
            ast.While,
        }


class CoverageNodeTransformerPython33(AbstractCoverageNodeTransformer):

    __python_version__ = (3, 3)

    @classmethod
    def get_coverable_nodes(cls):
        return {
            ast.Assert,
            ast.Assign,
            ast.AugAssign,
            ast.Break,
            ast.Continue,
            ast.Delete,
            ast.Expr,
            ast.Global,
            ast.Import,
            ast.ImportFrom,
            ast.Nonlocal,
            ast.Pass,
            ast.Raise,
            ast.Return,
            ast.ClassDef,
            ast.FunctionDef,
            ast.Try,
            ast.ExceptHandler,
            ast.If,
            ast.For,
            ast.While,
        }


CoverageNodeTransformer = utils.get_by_python_version([
    CoverageNodeTransformerPython32,
    CoverageNodeTransformerPython33,
])


class CoverageInjector:

    def __init__(self):
        self.covered_nodes = set()

    def inject(self, node, module_name='coverage'):
        self.covered_nodes.clear()
        self.marker_transformer = MarkerNodeTransformer()
        marker_node = self.marker_transformer.visit(node)
        coverage_node = CoverageNodeTransformer().visit(copy.deepcopy(marker_node))
        self.covered_nodes.add(coverage_node.marker)
        with utils.StdoutManager():
            return utils.create_module(
                ast_node=coverage_node,
                module_name=module_name,
                module_dict={COVERAGE_SET_NAME: self.covered_nodes},
            )

    def is_covered(self, child_node):
        return child_node.marker in self.covered_nodes

    def get_result(self):
        return len(self.covered_nodes), self.marker_transformer.last_marker


class CoverageTestResult(unittest.TestResult):

    def __init__(self, *args, coverage_injector=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.coverage_injector = coverage_injector
        self.always_covered_nodes = coverage_injector.covered_nodes.copy()
        self.test_covered_nodes = {}

    def startTest(self, test):
        super().startTest(test)
        self.covered_nodes = self.coverage_injector.covered_nodes.copy()
        self.coverage_injector.covered_nodes.clear()

    def stopTest(self, test):
        super().stopTest(test)
        self.test_covered_nodes[repr(test)] = self.coverage_injector.covered_nodes.copy() | self.always_covered_nodes
        self.coverage_injector.covered_nodes.update(self.covered_nodes)
