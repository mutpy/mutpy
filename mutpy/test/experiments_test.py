from mutpy import experiments
from mutpy.test.operators_test import OperatorTestCase, EOL, INDENT


class SelfWordDeletionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = experiments.SelfWordDeletion()

    def test_self_deletion_with_attribute(self):
        self.assert_mutation('self.x', ['x'])

    def test_self_deletion_with_method(self):
        self.assert_mutation('self.f()', ['f()'])

    def test_self_deletion_with_multi_attribute(self):
        self.assert_mutation('self.x.y.z', ['x.y.z'])

    def test_self_deletion_with_multi_attribute_after_method(self):
        self.assert_mutation('self.f().x.y.z', ['f().x.y.z'])


class StaticmethodDecoratorDeletionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = experiments.StaticmethodDecoratorDeletion()

    def test_single_staticmethod_deletion(self):
        self.assert_mutation('@staticmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' ,
                             ['def f():' + EOL + INDENT + 'pass'])

    def test_staticmethod_deletion_with_other(self):
        self.assert_mutation('@staticmethod' + EOL + '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' ,
                             ['@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass'])


class StaticmethodDecoratorInsertionTest(OperatorTestCase):

    @classmethod
    def setUpClass(cls):
        cls.op = experiments.StaticmethodDecoratorInsertion()

    def test_add_staticmethod_decorator(self):
        self.assert_mutation('def f():' + EOL + INDENT + 'pass',
                             ['@staticmethod' + EOL + 'def f():' + EOL + INDENT + 'pass'])

    def test_not_add_if_already_has_staticmethod(self):
        self.assert_mutation('@staticmethod' + EOL + 'def f():' + EOL + INDENT + 'pass', [])
