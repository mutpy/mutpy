import unittest
import os
import shutil
import types
import tempfile
import sys
from mutpy import utils, operators


class ModulesLoaderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='mutpytmp-') + '/'
        os.makedirs(cls.tmp + 'a/b/c')
        open(cls.tmp + 'a/__init__.py', 'w').close()
        open(cls.tmp + 'a/b/__init__.py', 'w').close()
        open(cls.tmp + 'a/b/c/__init__.py', 'w').close()
        with open(cls.tmp + 'a/b/c/sample.py', 'w') as f:
            f.write('class X:\n\tdef f():\n\t\tpass')
        with open(cls.tmp + 'a/b/c/sample_test.py', 'w') as f:
            f.write('from a.b.c import sample')

    def assert_module(self, module_object, module_name, module_path, attrs):
        self.assertIsInstance(module_object, types.ModuleType)
        for attr in attrs:
            self.assertTrue(hasattr(module_object, attr))
        self.assertMultiLineEqual(
            os.path.abspath(module_object.__file__),
            os.path.abspath(ModulesLoaderTest.tmp + module_path),
        )
        self.assertMultiLineEqual(os.path.abspath(module_object.__name__), os.path.abspath(module_name))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def setUp(self):
        self.loader = utils.ModulesLoader(None, ModulesLoaderTest.tmp)

    def test_load_file(self):
        self.assertRaises(NotImplementedError, lambda: self.loader.load_single('sample.py'))

    def test_load_module(self):
        module, to_mutate = self.loader.load_single('a.b.c.sample')[0]

        self.assert_module(module, 'a.b.c.sample', 'a/b/c/sample.py', ['X'])
        self.assertIsNone(to_mutate)

    def test_target_class(self):
        module, to_mutate = self.loader.load_single('a.b.c.sample.X')[0]

        self.assert_module(module, 'a.b.c.sample', 'a/b/c/sample.py', ['X'])
        self.assertMultiLineEqual(to_mutate, 'X')

    def test_target_method(self):
        module, to_mutate = self.loader.load_single('a.b.c.sample.X.f')[0]

        self.assert_module(module, 'a.b.c.sample', 'a/b/c/sample.py', ['X'])
        self.assertMultiLineEqual(to_mutate, 'X.f')

    def test_bad_target_class(self):
        self.assertRaises(utils.ModulesLoaderException, lambda: self.loader.load_single('a.b.c.sample.Y'))

    def test_bad_target_method(self):
        self.assertRaises(utils.ModulesLoaderException, lambda: self.loader.load_single('a.b.c.sample.X.g'))

    def test_bad_module(self):
        self.assertRaises(utils.ModulesLoaderException, lambda: self.loader.load_single('a.b.c.example'))

    def test_load_package(self):
        target, test = self.loader.load_single('a')
        self.assert_module(target[0], 'a.b.c.sample', 'a/b/c/sample.py', [])
        self.assert_module(test[0], 'a.b.c.sample_test', 'a/b/c/sample_test.py', [])


class MockTimer():

    def stop(self):
        return 1


class MockTimeRegister(utils.TimeRegister):
    timer_class = MockTimer


class TimeRegisterTest(unittest.TestCase):

    def setUp(self):
        MockTimeRegister.clean()

    def test_normal_function(self):
        @MockTimeRegister
        def foo():
            pass

        foo()

        self.assertEqual(MockTimeRegister.executions['foo'], 1)

    def test_recursion(self):
        @MockTimeRegister
        def foo(x):
            if x != 0:
                foo(x-1)

        foo(10)

        self.assertEqual(MockTimeRegister.executions['foo'], 1)

    def test_function_with_yield(self):
        @MockTimeRegister
        def foo():
            for i in [1, 2, 3]:
                yield i

        for _ in foo():
            pass

        self.assertEqual(MockTimeRegister.executions['foo'], 1)


class GetByPythonVersionTest(unittest.TestCase):

    class A:
        __python_version__ = (3, 1)

    class B:
        __python_version__ = (3, 2)

    def test_empty_classes(self):
        with self.assertRaises(NotImplementedError):
            utils.get_by_python_version(classes=[])

    def test_no_proper_class(self):
        with self.assertRaises(NotImplementedError):
            utils.get_by_python_version(classes=[self.A, self.B], python_version=(3, 0))

    def test_get_proper_class(self):
        cls = utils.get_by_python_version(classes=[self.A, self.B], python_version=(3, 1))

        self.assertEqual(cls, self.A)

    def test_get_lower_class(self):
        cls = utils.get_by_python_version(classes=[self.A, self.B], python_version=(3, 3))

        self.assertEqual(cls, self.B)


class SortOperatorsTest(unittest.TestCase):

    def test_sort_operators(self):

        class A(operators.MutationOperator):
            pass

        class Z(operators.MutationOperator):
            pass

        sorted_operators = utils.sort_operators([Z, A])

        self.assertEqual(sorted_operators[0], A)
        self.assertEqual(sorted_operators[1], Z)


class TestF(unittest.TestCase):

    def test_f(self):
        self.assertEqual(utils.f("""
        def f():
            pass
        """), 'def f():\n    pass')


class InjectImporterTest(unittest.TestCase):

    def test_inject(self):
        target_module_content = utils.f("""
        def x():
            import source
            return source
        """)
        target_module = types.ModuleType('target')
        source_module_before = types.ModuleType('source')
        source_module_before.__file__ = 'source.py'
        source_module_after = types.ModuleType('source')
        sys.modules['source'] = source_module_before
        importer = utils.InjectImporter(source_module_after)

        eval(compile(target_module_content, 'target.py', 'exec'), target_module.__dict__)
        importer.install()

        source_module = target_module.x()
        self.assertEqual(source_module, source_module_after)
        self.assertEqual(source_module.__loader__, importer)

        del sys.modules['source']
        importer.uninstall()


class ParentNodeTransformerTest(unittest.TestCase):

    def test_set_parent(self):
        node = utils.create_ast('x += y + z')

        utils.ParentNodeTransformer().visit(node)

        self.assertEqual(node.body[0].op.parent, node.body[0])
        self.assertIn(node.body[0].op, node.body[0].children)
        self.assertEqual(node.body[0].value.op.parent, node.body[0].value)
        self.assertIn(node.body[0].value.op, node.body[0].value.children)
