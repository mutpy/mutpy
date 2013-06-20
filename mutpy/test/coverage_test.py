import unittest
from mutpy import coverage, utils


class CoverageInjectorTest(unittest.TestCase):

    def setUp(self):
        self.coverage_injector = coverage.CoverageInjector()

    def test_covered_node(self):
        node = utils.create_ast('x = 1\nif False:\n\ty = 2')

        self.coverage_injector.inject(node)

        assign_node = node.body[0]
        self.assertTrue(self.coverage_injector.is_covered(assign_node))

    def test_not_covered_node(self):
        node = utils.create_ast('if False:\n\ty = 2')

        self.coverage_injector.inject(node)

        assign_node = node.body[0].body[0]
        self.assertFalse(self.coverage_injector.is_covered(assign_node))

    def test_result(self):
        node = utils.create_ast('x = 1')

        self.coverage_injector.inject(node)

        self.assertEqual(self.coverage_injector.get_result(), (1, 5))

    def test_future_statement_coverage(self):
        node = utils.create_ast('from __future__ import print_function')

        self.coverage_injector.inject(node)

        import_node = node.body[0]
        self.assertFalse(self.coverage_injector.is_covered(import_node))

    def test_docstring_coverage(self):
        node = utils.create_ast('"""doc"""')

        self.coverage_injector.inject(node)

        docstring_node = node.body[0]
        self.assertFalse(self.coverage_injector.is_covered(docstring_node))

