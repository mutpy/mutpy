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

class MutationScore:
    
    def __init__(self, all_mutants=0, killed_mutants=0, timeout_mutants=0, incompetent_mutants=0):
        self.all_mutants = all_mutants
        self.killed_mutants = killed_mutants
        self.timeout_mutants = timeout_mutants
        self.incompetent_mutants = incompetent_mutants
        
    def count(self):
        return (self.killed_mutants/(self.all_mutants-self.incompetent_mutants))*100
    
    def inc_all(self):
        self.all_mutants += 1
        
    def inc_killed(self):
        self.killed_mutants += 1
        
    def inc_timeout(self):
        self.timeout_mutants += 1
        
    def inc_incompetent(self):
        self.incompetent_mutants += 1
    
class MutationController:
    
    def __init__(self, mutation_cfg, view):
        self.target_name = mutation_cfg.target
        self.tests_name = mutation_cfg.test
        self.mutation_cfg = mutation_cfg
        self.view = view
        
    def run(self):
        start_time = time.time()
        self.view.initialize(self.mutation_cfg)
        target_module = self.load_target_module()
        target_ast = self.create_target_ast(target_module)
        
        try:
            test_modules = self.load_and_check_tests()
            self.view.passed(test_modules)
            mutant_generator = self.create_mutator(target_ast)
            score = MutationScore()
            self.view.start()
            
            for op, lineno, mutant_ast in mutant_generator.mutate():
                self.view.mutation(op, lineno, mutant_ast)
                score.inc_all()
                mutant_module = self.create_mutant_module(target_module, mutant_ast)
                self.run_tests_with_mutant(test_modules, mutant_module, score)
                    
            self.view.end(score, time.time() - start_time)
        except TestsFailAtOriginal as error:
            self.view.failed(error.result)        

    def load_target_module(self):
        if self.target_name.endswith('.py'):
            self.target_name = self.target_name[:-3]
        return __import__(self.target_name, globals(), locals())
        
    def create_target_ast(self, target_module):
        target_file = open(target_module.__file__)
        return ast.parse(target_file.read())
        
    def load_and_check_tests(self):
        test_modules = []
        for test in self.tests_name:
            if test.endswith('.py'):
                test = test[:-3]
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
        
    def run_tests_with_mutant(self, tests_modules, mutant_module, score):
        for test_module, duration in tests_modules:
            test_module.__dict__[mutant_module.__name__] = mutant_module
            suite = unittest.TestLoader().loadTestsFromModule(test_module)
            result = unittest.TestResult()
            result.failfast = True
            start = time.time()
            runner_thread = KillableThread(target=lambda: suite.run(result))
            runner_thread.start()
            live_time = self.mutation_cfg.timeout_factor * duration if duration > 1 else 1
            runner_thread.join(live_time)
            mutant_duration = time.time() - start
            
            if runner_thread.is_alive():
                runner_thread.kill()
                self.view.timeout()
                score.inc_timeout()
            elif result.errors:
                self.view.error()
                score.inc_incompetent()
            elif result.wasSuccessful():
                self.view.survived(mutant_duration)
            else:
                self.view.killed(mutant_duration)
                score.inc_killed()
    
class KillableThread(threading.Thread):
    
    def kill(self):
        if self.isAlive():
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), ctypes.py_object(SystemExit))
            if res == 0:
                raise ValueError("Invalid thread id.")
            elif res != 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
                raise SystemError("Thread killing failed.")