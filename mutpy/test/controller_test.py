import unittest
import os
import shutil
import types
import tempfile
from mutpy import controller


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
        self.assertMultiLineEqual(module_object.__file__, ModulesLoaderTest.tmp + module_path)
        self.assertMultiLineEqual(module_object.__name__, module_name)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def setUp(self):
        self.loader = controller.ModulesLoader(None, ModulesLoaderTest.tmp)

    def test_load_file(self):
        self.assertRaises(NotImplementedError, lambda : self.loader.load_single('sample.py'))

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
        self.assertRaises(controller.ModulesLoaderException, lambda : self.loader.load_single('a.b.c.sample.Y'))

    def test_bad_target_method(self):
        self.assertRaises(controller.ModulesLoaderException, lambda : self.loader.load_single('a.b.c.sample.X.g'))

    def test_bad_module(self):
        self.assertRaises(controller.ModulesLoaderException, lambda : self.loader.load_single('a.b.c.example'))

    def test_load_package(self):
        target, test = self.loader.load_single('a')
        self.assert_module(target[0], 'a.b.c.sample', 'a/b/c/sample.py', [])
        self.assert_module(test[0], 'a.b.c.sample_test', 'a/b/c/sample_test.py', [])



class MutationScoreTest(unittest.TestCase):

    def test_score(self):
        score = controller.MutationScore(all_mutants=11, killed_mutants=5, incompetent_mutants=1)
        self.assertEqual(score.count(), 50)
        score.inc_killed()
        self.assertEqual(score.count(), 60)

    def test_zero_score(self):
        score = controller.MutationScore(all_mutants=0)
        self.assertEqual(score.count(), 0)

