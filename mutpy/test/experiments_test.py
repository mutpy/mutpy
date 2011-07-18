from mutpy.test.operator_test import OperatorTestCase, EOL, INDENT
from mutpy import experiments


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


class ClassmethodDecoratorDeletionTest(OperatorTestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.op = experiments.ClassmethodDecoratorDeletion()
        
    def test_single_classmethod_deletion(self):
        self.assert_mutation('@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' , 
                             ['def f():' + EOL + INDENT + 'pass'])
        
    def test_classmethod_deletion_with_other(self):
        self.assert_mutation('@staticmethod' + EOL + '@classmethod' + EOL + 'def f():' + EOL + INDENT + 'pass' , 
                             ['@staticmethod' + EOL + 'def f():' + EOL + INDENT + 'pass'])        