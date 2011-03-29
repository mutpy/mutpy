import ast
import unittest
import types
from mutpy import mutator

class TestsFailAtOriginal(Exception):
    pass

class MutationController:
    def __init__(self, target_name, tests_name, mutation_cfg):
        self.target_name = target_name
        self.tests_name = tests_name
        self.mutation_cfg = mutation_cfg
    def run(self):
        try:
            target_module = self.load_target_module()
            target_ast = self.create_target_ast(target_module)
            test_modules = self.load_and_check_tests()
            mutant_generator = self.create_mutator(target_ast)
            for mutant_ast in mutant_generator.mutate():
                mutant_module = self.create_mutant_module(target_module, mutant_ast)
                self.run_tests_with_mutant(test_modules, mutant_module)
        except TestsFailAtOriginal:
            print('Failed original test!')

    def load_target_module(self):
        return __import__(self.target_name, globals(), locals())
        
    def create_target_ast(self, target_module):
        target_file = open(target_module.__file__)
        return ast.parse(target_file.read())
        
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
                raise TestsFailAtOriginal()
            
        return test_modules
        
    def create_mutator(self, target_ast):
        return mutator.Mutator(target_ast, self.mutation_cfg)
        
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
