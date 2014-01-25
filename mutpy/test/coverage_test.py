import unittest
from mutpy import coverage, utils


class MarkerNodeTransformerTest(unittest.TestCase):

    def test_visit(self):
        node = utils.create_ast('x = y\ny = x')
        coverage.MarkerNodeTransformer().visit(node)

        y_load_node = node.body[0].value.ctx
        x_load_node = node.body[1].value.ctx

        self.assertTrue(y_load_node.marker < x_load_node.marker)


class CoverageInjectorTest(unittest.TestCase):

    def setUp(self):
        self.coverage_injector = coverage.CoverageInjector()

    def test_covered_node(self):
        node = utils.create_ast('x = 1\nif False:\n\ty = 2')

        self.coverage_injector.inject(node)

        assign_node = node.body[0]
        constant_node = node.body[0].targets[0]
        self.assertTrue(self.coverage_injector.is_covered(assign_node))
        self.assertTrue(self.coverage_injector.is_covered(constant_node))

    def test_not_covered_node(self):
        node = utils.create_ast('if False:\n\ty = 2')

        self.coverage_injector.inject(node)

        assign_node = node.body[0].body[0]
        constant_node = node.body[0].body[0].targets[0]
        self.assertFalse(self.coverage_injector.is_covered(assign_node))
        self.assertFalse(self.coverage_injector.is_covered(constant_node))

    def test_result(self):
        node = utils.create_ast('x = 1')

        self.coverage_injector.inject(node)

        self.assertEqual(self.coverage_injector.get_result(), (5, 5))

    def test_future_statement_coverage(self):
        node = utils.create_ast('from __future__ import print_function')

        self.coverage_injector.inject(node)

        import_node = node.body[0]
        self.assertFalse(self.coverage_injector.is_covered(import_node))

    def test_docstring_coverage(self):
        node = utils.create_ast('"""doc"""')

        self.coverage_injector.inject(node)

        docstring_node = node.body[0]
        self.assertTrue(self.coverage_injector.is_covered(docstring_node))


class CoverageTestResultTest(unittest.TestCase):

    def test_run(self):

        coverage_injector = coverage.CoverageInjector()

        class A:

            def x(self):
                coverage_injector.covered_nodes.add(1)

        class ATest(unittest.TestCase):

            def test_x(self):
                A().x()

            def test_y(self):
                pass

        result = coverage.CoverageTestResult(coverage_injector=coverage_injector)
        suite = unittest.TestSuite()
        test_x = ATest(methodName='test_x')
        suite.addTest(test_x)
        test_y = ATest(methodName='test_y')
        suite.addTest(test_y)

        suite.run(result)

        self.assertEqual(coverage_injector.covered_nodes, {1})
        self.assertEqual(result.test_covered_nodes[test_x], {1})
        self.assertFalse(result.test_covered_nodes[test_y])
