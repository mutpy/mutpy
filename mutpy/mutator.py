import ast
import unittest
import types

class Mutator:
    def __init__(self, target, tests):
        self.target_name = target
        self.tests_name = tests
    def run(self):
        target_module = self.load_target_module()
        target_ast = self.create_target_ast(target_module)
        test_modules = self.load_and_check_tests()
        mutant_ast = self.mutate_ast(target_ast)
        mutant_module = self.create_mutant_module(target_module, mutant_ast)
        self.run_tests_with_mutant(test_modules, mutant_module)

    def load_target_module(self):
        return __import__(self.target_name, globals(), locals())
        
    def create_target_ast(self, target_module):
        target_file = open(target_module.__file__)
        target_ast = ast.parse(target_file.read())
        return target_ast
        
    def load_and_check_tests(self):
        test_modules = []
        for test in self.tests_name:
            test_module = __import__(test, globals(), locals())
            suite = unittest.TestLoader().loadTestsFromModule(test_module)
            result = unittest.TestResult()
            suite.run(result)
            if result.wasSuccessful():
                print('Passed original test!')
                test_modules.append(test_module)
            else:
                print('Failed original test!')
                
        return test_modules
        
    def mutate_ast(self, target_ast):
        return ArithmeticOperatorReplacement().visit(target_ast)
        
    def create_mutant_module(self, target_module, mutant_ast):
        mutant_code = compile(mutant_ast, 'mutant', 'exec')
        mutant_module = types.ModuleType(target_module.__name__)
        exec(mutant_code, mutant_module.__dict__)
        return mutant_module
        
    def run_tests_with_mutant(self, tests_modules, mutant_module):
        for test_module in tests_modules:
            test_module.__dict__[mutant_module.__name__] = mutant_module
            suite = unittest.TestLoader().loadTestsFromModule(test_module)
            result = unittest.TestResult()
            suite.run(result)
            if result.wasSuccessful():
                print('Survived!')
            else:
                print('Killed!')


class ArithmeticOperatorReplacement(ast.NodeTransformer):
    def visit_Add(self, node):
        print('+ -> -')
        return ast.Sub()