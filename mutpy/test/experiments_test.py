from mutpy.test.operator_test import OperatorTestCase
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
        