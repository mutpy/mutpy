import unittest
import ast
from mutpy.coverage import CoverageInjector


class CoverageInjectorTest(unittest.TestCase):

    def setUp(self):
        self.coverage_injector = CoverageInjector()

    def test_covered_node(self):
        node = ast.parse('x = 1\nif False:\n\ty = 2')

        self.coverage_injector.inject(node)

        assign_node = node.body[0]
        self.assertTrue(self.coverage_injector.is_covered(assign_node))

    def test_not_covered_node(self):
        node = ast.parse('if False:\n\ty = 2')

        self.coverage_injector.inject(node)

        assign_node = node.body[0].body[0]
        self.assertFalse(self.coverage_injector.is_covered(assign_node))

    def test_result(self):
        node = ast.parse('x = 1')

        self.coverage_injector.inject(node)

        self.assertEqual(self.coverage_injector.get_result(), (1, 1))

