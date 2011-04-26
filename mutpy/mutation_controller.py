import ast
import unittest
import types
import time
import threading
import multiprocessing
import sys
import trace
import inspect
import ctypes
from mutpy import mutator
from mutpy import codegen

class TestsFailAtOriginal(Exception):
    
    def __init__(self, result=None):
        self.result = result

class MutationController:
    
    def __init__(self, mutation_cfg, view):
        self.target_name = mutation_cfg.target
        self.tests_name = mutation_cfg.test
        self.mutation_cfg = mutation_cfg
        self.view = view
        
    def run(self):
        self.view.initialize(self.mutation_cfg)
        try:
            target_module = self.load_target_module()
            target_ast = self.create_target_ast(target_module)
            test_modules = self.load_and_check_tests()
            self.view.passed(test_modules)
            mutant_generator = self.create_mutator(target_ast)
            all_mutations = 0
            killed = 0
            self.view.start()
            for op, lineno, mutant_ast in mutant_generator.mutate():
                self.view.mutation(op, lineno, mutant_ast)
                all_mutations += 1
                mutant_module = self.create_mutant_module(target_module, mutant_ast)
                if self.run_tests_with_mutant(test_modules, mutant_module):
                    killed += 1
            self.view.end(100*killed/all_mutations, killed, all_mutations, 0)
        except TestsFailAtOriginal as error:
            self.view.failed(error.result)

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
            start = time.time()
            suite.run(result)
            duration = time.time() - start
            if result.wasSuccessful():
                test_modules.append((test_module, duration))
            else:
                raise TestsFailAtOriginal(result)
            
        return test_modules
        
    def create_mutator(self, target_ast):
        return mutator.Mutator(target_ast, self.mutation_cfg)
        
    def create_mutant_module(self, target_module, mutant_ast):
        mutant_code = compile(mutant_ast, 'mutant', 'exec')
        mutant_module = types.ModuleType(target_module.__name__)
        exec(mutant_code, mutant_module.__dict__)
        return mutant_module
        
    def run_tests_with_mutant(self, tests_modules, mutant_module):
        for test_module, duration in tests_modules:
            test_module.__dict__[mutant_module.__name__] = mutant_module
            suite = unittest.TestLoader().loadTestsFromModule(test_module)
            result = unittest.TestResult()
            result.failfast = True #?
            start = time.time()
            runner = lambda: suite.run(result)
            runner_thread = KillableThread(target=runner)
            runner_thread.start()
            runner_thread.join(5*duration if duration > 1 else 1)
            mutant_duration = time.time() - start
            
            if runner_thread.is_alive():
                runner_thread.kill()
                self.view.timeout()
                return False
                
            if result.errors: # np. TypeError
                self.view.error()
                return True
                
            if result.wasSuccessful():
                self.view.survived(mutant_duration)
                return False
            else:
                self.view.killed(mutant_duration)
                return True
    
class KillableThread(threading.Thread):
    
    def kill(self):
        if self.isAlive():
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), ctypes.py_object(SystemExit))
            if res == 0:
                raise ValueError("Invalid thread id.")
            elif res != 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
                raise SystemError("Thread killing failed.")